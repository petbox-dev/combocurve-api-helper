"""Authentication for the ComboCurve API: OAuth 2.0 client credentials (v2) and the legacy service
account (v1). See the "Authentication & OAuth 2.0" page of the ComboCurve API docs. (It is not linked
here: `test_docstring_slugs.py` reads every docs link as a Postman operation, and the collection has
no OAuth operation.)

* OAuth (v2, current): `api-credentials.json` holds a `clientId` and `clientSecret`. A bearer token
  comes from a POST to the token endpoint and lives `expires_in` seconds (3600). Every API request
  also carries `x-backend-version: v2`; without it the request reaches the legacy backend and fails.
  The token is kept on disk (`~/.combocurve/token-cache`), so a new run reuses it until it is due.
* Service account (v1, legacy; ComboCurve no longer issues it): a GCP service-account key signs an
  RS256 JWT locally.

Both send the same `x-api-key`. `APIBase._auth_headers` calls `get_auth_headers()` under a lock, so a
token refresh never runs on two threads at once.
"""

from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import os
import tempfile
import time
import warnings
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
# The longest refresh time after its write that a token file on disk may carry. ComboCurve tokens
# live 3600 s; a larger gap means the file is damaged or was written under a wrong clock.
_MAX_STORED_TOKEN_SECONDS = 24 * 3600.0
# How far ahead of this machine's clock a file's write time may be: hosts that share a home directory
# disagree by a few seconds, and refusing their files would spend the token quota on every run.
_CLOCK_TOLERANCE_SECONDS = 5.0


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
            stored = self._read_stored_token()
            if stored is not None and time.time() < stored[1]:
                self._token, self._token_refresh_at = stored
            else:
                token, lifetime_seconds = self._new_token()
                margin_seconds = min(_REFRESH_MARGIN_SECONDS, lifetime_seconds / 2.0)
                self._token = token
                self._token_refresh_at = time.time() + lifetime_seconds - margin_seconds
                self._store_token(self._token, self._token_refresh_at)
        return self._token

    def _backend_headers(self) -> dict[str, str]:
        """Headers beyond the token and API key that this credential type requires."""
        return {}

    def _read_stored_token(self) -> tuple[str, float] | None:
        """A token kept outside this object (another run's), with its refresh time; None if there is none."""
        return None

    def _store_token(self, token: str, refresh_at: float) -> None:
        """Keep `token` outside this object for later runs. The default keeps nothing."""
        return

    @abstractmethod
    def _new_token(self) -> tuple[str, float]:
        """A new bearer token and its lifetime in seconds."""


class OAuthClientAuth(_CachedBearerTokenAuth):
    """OAuth 2.0 client-credentials auth (v2 credentials).

    The token is also kept on disk, in `token_cache_directory` (default `~/.combocurve/token-cache`),
    so the next run of a script reuses it until it is due for refresh instead of spending one of the
    10 token requests per client per 15 minutes. One file per credential, named by the first 32 hex
    digits of a SHA-256 of the token URI, client id and client secret (a new secret starts a new
    file). The file holds the bearer token in plain text with its write and refresh times, not the
    secret; on POSIX it is readable by the owner only (mode 0600). A token found on disk is checked
    again before each fetch, so a token another process fetched is used. Two processes that both
    find no valid token fetch one each. A file that cannot be read, or whose times are not
    plausible, is ignored; one that cannot be written gives a `RuntimeWarning`, and the request
    goes on. `cache_token_on_disk=False` keeps the token in memory only. If ComboCurve refuses a
    token that is still on disk (revoked on the server), delete the file, or the directory, to make
    the next run fetch a new one.
    """

    # A `str`, not a `Path`, so a pickled client unpickles on another OS (a `WindowsPath` does not on
    # POSIX). The class-level default also serves a client pickled before 3.2.0, which has no such
    # attribute: unpickled here, it keeps its token in memory only.
    _token_cache_file: str | None = None

    def __init__(
        self,
        credentials: OAuthClientCredentials,
        api_key: str,
        *,
        cache_token_on_disk: bool = True,
        token_cache_directory: str | Path | None = None,
    ) -> None:
        super().__init__(api_key)
        self._credentials = credentials
        if cache_token_on_disk:
            directory = Path(config.TOKEN_CACHE_DIRECTORY if token_cache_directory is None else token_cache_directory)
            identity = '\n'.join((credentials.token_uri, credentials.client_id, credentials.client_secret))
            self._token_cache_file = str(directory / f'{hashlib.sha256(identity.encode()).hexdigest()[:32]}.json')

    def _backend_headers(self) -> dict[str, str]:
        return {'x-backend-version': 'v2'}

    def _read_stored_token(self) -> tuple[str, float] | None:
        """The token on disk, or None when there is none or it is not trustworthy.

        A file is refused when its times are not finite numbers, when it was written in the future
        (the clock ran ahead then and was corrected since), or when its refresh time is more than
        `_MAX_STORED_TOKEN_SECONDS` after it was written. Without those checks a bad `refresh_at`
        would keep a dead token in use on every run, since the file is rewritten only after a fetch.
        """
        if self._token_cache_file is None:
            return None
        try:
            document = json.loads(Path(self._token_cache_file).read_text(encoding='utf-8'))
        except (OSError, ValueError, RecursionError):
            return None
        if not isinstance(document, dict):
            return None
        token = document.get('access_token')
        if not isinstance(token, str) or not token:
            return None
        written_at = document.get('written_at')
        refresh_at = document.get('refresh_at')
        if not isinstance(written_at, (int, float)) or not isinstance(refresh_at, (int, float)):
            return None
        try:
            written_at, refresh_at = float(written_at), float(refresh_at)
        except OverflowError:  # an integer too large for a float
            return None
        # NaN fails every comparison and an infinity exceeds the gap, so both are refused here too.
        if (
            written_at > time.time() + _CLOCK_TOLERANCE_SECONDS
            or not 0.0 <= refresh_at - written_at <= _MAX_STORED_TOKEN_SECONDS
        ):
            return None
        return token, refresh_at

    def _store_token(self, token: str, refresh_at: float) -> None:
        """Write the file whole under a temporary name, then rename it, so a reader never sees half a file."""
        if self._token_cache_file is None:
            return
        written_at = time.time()
        cache_path = Path(self._token_cache_file)
        directory = cache_path.parent
        temporary_path: str | None = None
        try:
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            file_descriptor, temporary_path = tempfile.mkstemp(dir=directory, suffix='.tmp')
            with os.fdopen(file_descriptor, 'w', encoding='utf-8') as temporary_file:
                json.dump({'access_token': token, 'written_at': written_at, 'refresh_at': refresh_at}, temporary_file)
            os.replace(temporary_path, cache_path)
            temporary_path = None
        except OSError as error:
            warnings.warn(
                f'could not write the ComboCurve token cache {cache_path}: {error}',
                RuntimeWarning,
                stacklevel=2,
            )
        finally:
            if temporary_path is not None:
                with contextlib.suppress(OSError):
                    os.remove(temporary_path)

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
    both credential files are present the OAuth one is used, with a `DeprecationWarning`; that raises
    in a 3.x release, not before 2027-01-31. Each download carries its own `api-key.txt`, and a key
    works only with its own credential (verified 2026-10-27: the service account with the OAuth
    download's key answers 403), so one directory cannot serve both.
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
                'In a 3.x release, not before 2027-01-31, this raises: each download has its own API key, '
                'so keep one per directory.'
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
        'removed in a 3.x release, not before 2027-01-31. '
        f'Unzip the ComboCurve credential download into {config.COMBOCURVE_DIRECTORY} '
        f'({config.API_KEY_TXT} with {config.API_CREDENTIALS_JSON} or {config.SERVICE_ACCOUNT_KEY_JSON}).'
    )
    return auth_from_credentials_file(config.COMBOCURVE_JSON, config.cfg.apikey)
