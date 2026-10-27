"""Authentication for the ComboCurve API: OAuth 2.0 client credentials (v2) and the legacy service
account (v1). See the "Authentication & OAuth 2.0" page of the ComboCurve API docs. (It is not linked
here: `test_docstring_slugs.py` reads every docs link as a Postman operation, and the collection has
no OAuth operation.)

* OAuth (v2, current): `api-credentials.json` holds a `clientId` and `clientSecret`. A bearer token
  comes from a POST to the token endpoint and lives `expires_in` seconds (3600). Every API request
  also carries `x-backend-version: v2`; without it the request reaches the legacy backend and fails.
* Service account (v1, legacy; ComboCurve no longer issues it): a GCP service-account key signs an
  RS256 JWT locally.

Both send the same `x-api-key`. `APIBase._auth_headers` calls `get_auth_headers()` under a lock, so a
token refresh never runs on two threads at once.
"""

from __future__ import annotations

import datetime
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import jwt
import requests
from typing_extensions import Self

from . import config
from ._deprecation import warn_deprecated

if TYPE_CHECKING:
    from collections.abc import Mapping

OAUTH_CREDENTIALS_TYPE = 'combocurve_oauth2_client'
SERVICE_ACCOUNT_CREDENTIALS_TYPE = 'service_account'

DEFAULT_TOKEN_URI = 'https://api.combocurve.com/v1/oauth/token'
SERVICE_ACCOUNT_AUDIENCE = 'https://api.combocurve.com'
SERVICE_ACCOUNT_TOKEN_SECONDS = 3600

# A token is replaced this many seconds before it expires, or at half its lifetime if that is
# shorter. The half-lifetime cap matters for OAuth: the token endpoint allows 10 requests per client
# per 15 minutes, and a lifetime under the margin would otherwise fetch a token for every request.
_REFRESH_MARGIN_SECONDS = 60.0
_TOKEN_REQUEST_TIMEOUT_SECONDS = (30.0, 60.0)


class ComboCurveAuthError(RuntimeError):
    """The token endpoint refused the credentials, or answered without a usable token.

    Deliberately not a `requests.RequestException`: `_send_request` sends a request again after some
    of those, and a refused token must reach the caller at once.
    """


class APIAuth(Protocol):
    """What `APIBase` needs from an auth object: the headers for one request."""

    def get_auth_headers(self) -> dict[str, str]: ...


def _required_fields(document: Mapping[str, Any], names: tuple[str, ...], source: str) -> list[str]:
    """The values of `names` in `document` as strings; raise `ValueError` naming every missing one."""
    missing = [name for name in names if not document.get(name)]
    if missing:
        raise ValueError(f'{source}: missing {", ".join(missing)}')
    return [str(document[name]) for name in names]


@dataclass(frozen=True)
class OAuthClientCredentials:
    """The contents of an OAuth (v2) `api-credentials.json`."""

    client_id: str
    client_secret: str = field(repr=False)
    token_uri: str = DEFAULT_TOKEN_URI

    @classmethod
    def from_mapping(cls, document: Mapping[str, Any], source: str = 'OAuth credentials') -> Self:
        # The file ComboCurve ships spells these `client_id` / `client_secret` (verified 2026-10-27);
        # the docs page shows `clientId` / `clientSecret`. Read either. The token request body uses
        # the camelCase names, as documented (verified live: HTTP 200).
        normalized = {
            'client_id': document.get('client_id') or document.get('clientId'),
            'client_secret': document.get('client_secret') or document.get('clientSecret'),
        }
        client_id, client_secret = _required_fields(normalized, ('client_id', 'client_secret'), source)
        return cls(client_id, client_secret, str(document.get('token_uri') or DEFAULT_TOKEN_URI))


@dataclass(frozen=True)
class ServiceAccount:
    """The fields of a legacy (v1) GCP service-account key that the JWT needs."""

    client_email: str
    private_key: str = field(repr=False)
    private_key_id: str

    @classmethod
    def from_mapping(cls, document: Mapping[str, Any], source: str = 'service account') -> Self:
        client_email, private_key, private_key_id = _required_fields(
            document, ('client_email', 'private_key', 'private_key_id'), source
        )
        return cls(client_email, private_key, private_key_id)


class _CachedBearerTokenAuth(ABC):
    """Caches a bearer token and replaces it shortly before it expires.

    The expiry is wall-clock time (`time.time()`), not `time.monotonic()`: a pickled client sent to
    another process keeps a valid deadline there, so the copies reuse the token instead of each
    fetching one against the OAuth rate limit.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._token: str | None = None
        self._token_refresh_at = 0.0

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def get_auth_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self._current_token()}',
            'x-api-key': self._api_key,
            **self._backend_headers(),
        }

    def _current_token(self) -> str:
        if self._token is None or time.time() >= self._token_refresh_at:
            token, lifetime_seconds = self._new_token()
            margin_seconds = min(_REFRESH_MARGIN_SECONDS, lifetime_seconds / 2.0)
            self._token = token
            self._token_refresh_at = time.time() + lifetime_seconds - margin_seconds
        return self._token

    def _backend_headers(self) -> dict[str, str]:
        """Headers beyond the token and API key that this credential type requires."""
        return {}

    @abstractmethod
    def _new_token(self) -> tuple[str, float]:
        """A new bearer token and its lifetime in seconds."""


class OAuthClientAuth(_CachedBearerTokenAuth):
    """OAuth 2.0 client-credentials auth (v2 credentials)."""

    def __init__(self, credentials: OAuthClientCredentials, api_key: str) -> None:
        super().__init__(api_key)
        self._credentials = credentials

    def _backend_headers(self) -> dict[str, str]:
        return {'x-backend-version': 'v2'}

    def _new_token(self) -> tuple[str, float]:
        """POST the client credentials to the token endpoint.

        A connection failure propagates as the `requests` exception it is, so `_send_request` treats
        it as it treats the API request it was fetching headers for. A refusal raises
        `ComboCurveAuthError` and is not retried: 429 means the client's 10-per-15-minutes token
        quota is spent, and resending only extends the wait.
        """
        response = requests.post(
            self._credentials.token_uri,
            json={
                'grant_type': 'client_credentials',
                'clientId': self._credentials.client_id,
                'clientSecret': self._credentials.client_secret,
            },
            timeout=_TOKEN_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            raise ComboCurveAuthError(
                f'ComboCurve token request failed with HTTP {response.status_code}: {response.text[:500]}'
            )
        try:
            body = response.json()
            token = str(body['access_token'])
            lifetime_seconds = float(body['expires_in'])
        except (ValueError, KeyError, TypeError) as error:
            raise ComboCurveAuthError(f'ComboCurve token response has no usable token: {error!r}') from error
        return token, lifetime_seconds


class ServiceAccountAuth(_CachedBearerTokenAuth):
    """Legacy service-account auth (v1 credentials): an RS256 JWT signed locally.

    Same claims and header as `combocurve-api-v1`'s `JWTHandler`, which this replaces.
    """

    def __init__(self, service_account: ServiceAccount, api_key: str) -> None:
        super().__init__(api_key)
        self._service_account = service_account

    def _new_token(self) -> tuple[str, float]:
        issued_at = datetime.datetime.now(datetime.timezone.utc)
        token = jwt.encode(
            {
                'iss': self._service_account.client_email,
                'sub': self._service_account.client_email,
                'aud': SERVICE_ACCOUNT_AUDIENCE,
                'iat': issued_at,
                'exp': issued_at + datetime.timedelta(seconds=SERVICE_ACCOUNT_TOKEN_SECONDS),
            },
            self._service_account.private_key,
            algorithm='RS256',
            headers={'kid': self._service_account.private_key_id, 'typ': 'JWT', 'alg': 'RS256'},
        )
        return token, float(SERVICE_ACCOUNT_TOKEN_SECONDS)


def auth_from_credentials_file(credentials_path: str | Path, api_key: str) -> APIAuth:
    """Build the auth for a credential JSON of either type, chosen by its `type` field.

    A file without `type` is read as a service account: `combocurve-api-v1` never read the field, so a
    legacy file may lack it.
    """
    credentials_path = Path(credentials_path)
    document = json.loads(credentials_path.read_text())
    if not isinstance(document, dict):
        raise ValueError(f'{credentials_path}: expected a JSON object')
    credentials_type = document.get('type', SERVICE_ACCOUNT_CREDENTIALS_TYPE)
    if credentials_type == OAUTH_CREDENTIALS_TYPE:
        return OAuthClientAuth(OAuthClientCredentials.from_mapping(document, str(credentials_path)), api_key)
    if credentials_type == SERVICE_ACCOUNT_CREDENTIALS_TYPE:
        return ServiceAccountAuth(ServiceAccount.from_mapping(document, str(credentials_path)), api_key)
    raise ValueError(
        f'{credentials_path}: unknown credentials type {credentials_type!r}; expected '
        f'{OAUTH_CREDENTIALS_TYPE!r} or {SERVICE_ACCOUNT_CREDENTIALS_TYPE!r}'
    )


def auth_from_credentials_directory(directory: str | Path) -> APIAuth:
    """Build the auth from an unzipped ComboCurve credential download.

    `directory` holds `api-key.txt` and one of `api-credentials.json` (OAuth) or
    `api-service-account-key.json` (legacy), at its top or in the ZIP's `combocurve/` folder. When
    both credential files are present the OAuth one is used, with a `DeprecationWarning`: from 3.1.0
    that raises. Each download carries its own `api-key.txt`, and a key works only with its own
    credential (verified 2026-10-27: the service account with the OAuth download's key answers 403), so
    one directory cannot serve both.
    """
    native_directory = config.find_native_credentials_directory(directory)
    if native_directory is None:
        raise FileNotFoundError(
            f'no {config.API_KEY_TXT} in {directory} or in its {config.CREDENTIALS_ZIP_FOLDER}/ folder; '
            'unzip the ComboCurve credential download there'
        )
    oauth_path = native_directory / config.API_CREDENTIALS_JSON
    service_account_path = native_directory / config.SERVICE_ACCOUNT_KEY_JSON
    if oauth_path.is_file():
        if service_account_path.is_file():
            warn_deprecated(
                f'{native_directory} holds both {config.API_CREDENTIALS_JSON} and {config.SERVICE_ACCOUNT_KEY_JSON}; '
                f'using {config.API_CREDENTIALS_JSON}, so {config.API_KEY_TXT} must be the key from the same download. '
                'From 3.1.0 this raises: each download has its own API key, so keep one per directory.'
            )
        credentials_path = oauth_path
    elif service_account_path.is_file():
        credentials_path = service_account_path
    else:
        raise FileNotFoundError(
            f'{native_directory} holds {config.API_KEY_TXT} but neither {config.API_CREDENTIALS_JSON} '
            f'nor {config.SERVICE_ACCOUNT_KEY_JSON}'
        )
    return auth_from_credentials_file(credentials_path, config.read_api_key(native_directory))


def default_auth() -> APIAuth:
    """The auth `ComboCurveAPI()` uses: the native files in `~/.combocurve`, else the older
    `combocurve.json` + `cc-api.config.json` layout with a `DeprecationWarning`."""
    if config.find_native_credentials_directory(config.COMBOCURVE_DIRECTORY) is not None:
        return auth_from_credentials_directory(config.COMBOCURVE_DIRECTORY)
    warn_deprecated(
        f'Reading {config.COMBOCURVE_JSON.name} and {config.CC_API_CONFIG_JSON.name} is deprecated and is '
        f'removed in 3.0.0. Unzip the ComboCurve credential download into {config.COMBOCURVE_DIRECTORY} '
        f'({config.API_KEY_TXT} with {config.API_CREDENTIALS_JSON} or {config.SERVICE_ACCOUNT_KEY_JSON}).'
    )
    return auth_from_credentials_file(config.COMBOCURVE_JSON, config.cfg.apikey)
