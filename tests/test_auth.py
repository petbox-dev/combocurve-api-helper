"""Unit tests for the two credential types and how a client finds them -- no live API.

OAuth (v2) tokens come from a fake token endpoint; legacy (v1) JWTs are signed with an RSA key
generated per test session and decoded back with its public half.
"""

import json
import pickle
import time
import warnings
from pathlib import Path
from typing import Any, Optional

import jwt
import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI, auth, base, config
from tests.http_fakes import FakeResponse, make_offline_api

API_KEY = 'sample-api-key'
# The shape of the `api-credentials.json` ComboCurve ships (verified 2026-10-27): snake_case ids.
OAUTH_CREDENTIALS: dict[str, str] = {
    'type': 'combocurve_oauth2_client',
    'client_id': 'sample-client-id',
    'client_secret': 'sample-client-secret',
    'token_uri': 'https://api.combocurve.com/v1/oauth/token',
    'audience': 'https://api.combocurve.com',
}
# The spelling the docs page shows.
OAUTH_CREDENTIALS_AS_DOCUMENTED: dict[str, str] = {
    'type': 'combocurve_oauth2_client',
    'clientId': 'sample-client-id',
    'clientSecret': 'sample-client-secret',
}


@pytest.fixture(scope='session')
def rsa_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def service_account_credentials(rsa_private_key: rsa.RSAPrivateKey) -> dict[str, str]:
    private_key_pem = rsa_private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    return {
        'type': 'service_account',
        'private_key_id': 'sample-key-id',
        'private_key': private_key_pem,
        'client_email': 'sample@example.iam.gserviceaccount.com',
        'client_id': '000000000000000000000',
    }


class FakeTokenEndpoint:
    """Replaces `requests.post` for the token request; records each call and returns `responses` in turn."""

    def __init__(self, *responses: FakeResponse) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({'url': url, **kwargs})
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


def token_response(token: str = 'token-1', expires_in: Any = 3600) -> FakeResponse:
    return FakeResponse(200, body={'access_token': token, 'token_type': 'Bearer', 'expires_in': expires_in})


def write_json(path: Path, document: dict[str, str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document))
    return path


def write_native_directory(
    directory: Path,
    oauth_credentials: Optional[dict[str, str]] = None,
    service_account_credentials: Optional[dict[str, str]] = None,
) -> Path:
    """Lay out the files of an unzipped ComboCurve credential download."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'api-key.txt').write_text(API_KEY + '\n')
    if oauth_credentials is not None:
        write_json(directory / 'api-credentials.json', oauth_credentials)
    if service_account_credentials is not None:
        write_json(directory / 'api-service-account-key.json', service_account_credentials)
    return directory


def oauth_auth(endpoint: FakeTokenEndpoint, monkeypatch: MonkeyPatch) -> auth.OAuthClientAuth:
    monkeypatch.setattr(requests, 'post', endpoint)
    return auth.OAuthClientAuth(auth.OAuthClientCredentials.from_mapping(OAUTH_CREDENTIALS), API_KEY)


class TestOAuthClientAuth:
    def test_headers_carry_token_api_key_and_v2_backend(self, monkeypatch: MonkeyPatch) -> None:
        client_auth = oauth_auth(FakeTokenEndpoint(token_response('token-1')), monkeypatch)
        assert client_auth.get_auth_headers() == {
            'Authorization': 'Bearer token-1',
            'x-api-key': API_KEY,
            'x-backend-version': 'v2',
        }

    def test_token_request_matches_the_documented_contract(self, monkeypatch: MonkeyPatch) -> None:
        endpoint = FakeTokenEndpoint(token_response())
        oauth_auth(endpoint, monkeypatch).get_auth_headers()
        [call] = endpoint.calls
        assert call['url'] == 'https://api.combocurve.com/v1/oauth/token'
        assert call['json'] == {
            'grant_type': 'client_credentials',
            'clientId': 'sample-client-id',
            'clientSecret': 'sample-client-secret',
        }
        assert call['timeout'] is not None

    def test_token_is_fetched_once_for_many_requests(self, monkeypatch: MonkeyPatch) -> None:
        endpoint = FakeTokenEndpoint(token_response())
        client_auth = oauth_auth(endpoint, monkeypatch)
        for _ in range(50):
            client_auth.get_auth_headers()
        assert len(endpoint.calls) == 1

    def test_token_is_refreshed_60_seconds_before_expiry(self, monkeypatch: MonkeyPatch) -> None:
        now = [1_000_000.0]
        monkeypatch.setattr(time, 'time', lambda: now[0])
        endpoint = FakeTokenEndpoint(token_response('token-1'), token_response('token-2'))
        client_auth = oauth_auth(endpoint, monkeypatch)

        assert client_auth.get_auth_headers()['Authorization'] == 'Bearer token-1'
        now[0] += 3600 - 60 - 1
        assert client_auth.get_auth_headers()['Authorization'] == 'Bearer token-1'
        now[0] += 1
        assert client_auth.get_auth_headers()['Authorization'] == 'Bearer token-2'
        assert len(endpoint.calls) == 2

    def test_short_lifetime_does_not_refresh_on_every_request(self, monkeypatch: MonkeyPatch) -> None:
        """A lifetime under the 60 s margin must not make every request fetch a token: the endpoint allows
        10 requests per client per 15 minutes."""
        now = [1_000_000.0]
        monkeypatch.setattr(time, 'time', lambda: now[0])
        endpoint = FakeTokenEndpoint(token_response(expires_in=30))
        client_auth = oauth_auth(endpoint, monkeypatch)
        client_auth.get_auth_headers()
        now[0] += 14
        client_auth.get_auth_headers()
        assert len(endpoint.calls) == 1

    @pytest.mark.parametrize('status', [400, 401, 429])
    def test_refused_token_request_raises_with_status(self, status: int, monkeypatch: MonkeyPatch) -> None:
        refusal = FakeResponse(status, body={'error': 'invalid credentials'})
        client_auth = oauth_auth(FakeTokenEndpoint(refusal), monkeypatch)
        with pytest.raises(auth.ComboCurveAuthError, match=str(status)):
            client_auth.get_auth_headers()

    def test_auth_error_is_not_a_requests_exception(self) -> None:
        """`_send_request` retries some `requests.RequestException`s; a refused token must not be retried."""
        assert not issubclass(auth.ComboCurveAuthError, requests.RequestException)

    @pytest.mark.parametrize(
        'body',
        [
            {'token_type': 'Bearer', 'expires_in': 3600},
            {'access_token': 't', 'expires_in': 'soon'},
            ['not', 'a', 'dict'],
        ],
    )
    def test_unusable_token_body_raises(self, body: Any, monkeypatch: MonkeyPatch) -> None:
        client_auth = oauth_auth(FakeTokenEndpoint(FakeResponse(200, body=body)), monkeypatch)
        with pytest.raises(auth.ComboCurveAuthError):
            client_auth.get_auth_headers()

    def test_secret_is_not_in_repr(self) -> None:
        credentials = auth.OAuthClientCredentials.from_mapping(OAUTH_CREDENTIALS)
        assert 'sample-client-secret' not in repr(credentials)
        assert 'sample-client-secret' not in repr(auth.OAuthClientAuth(credentials, API_KEY))

    def test_pickled_auth_keeps_its_token(self, monkeypatch: MonkeyPatch) -> None:
        endpoint = FakeTokenEndpoint(token_response())
        client_auth = oauth_auth(endpoint, monkeypatch)
        client_auth.get_auth_headers()
        copy = pickle.loads(pickle.dumps(client_auth))
        assert copy.get_auth_headers()['Authorization'] == 'Bearer token-1'
        assert len(endpoint.calls) == 1

    def test_missing_field_names_the_field(self) -> None:
        incomplete = {key: value for key, value in OAUTH_CREDENTIALS.items() if key != 'client_secret'}
        with pytest.raises(ValueError, match='client_secret'):
            auth.OAuthClientCredentials.from_mapping(incomplete)

    def test_documented_camel_case_file_is_read_the_same(self) -> None:
        shipped = auth.OAuthClientCredentials.from_mapping(OAUTH_CREDENTIALS)
        documented = auth.OAuthClientCredentials.from_mapping(OAUTH_CREDENTIALS_AS_DOCUMENTED)
        assert shipped == documented


class TestServiceAccountAuth:
    def test_headers_carry_signed_jwt_and_no_backend_version(
        self, service_account_credentials: dict[str, str], rsa_private_key: rsa.RSAPrivateKey
    ) -> None:
        account = auth.ServiceAccount.from_mapping(service_account_credentials)
        headers = auth.ServiceAccountAuth(account, API_KEY).get_auth_headers()
        assert set(headers) == {'Authorization', 'x-api-key'}
        assert headers['x-api-key'] == API_KEY

        token = headers['Authorization'].removeprefix('Bearer ')
        claims = jwt.decode(
            token, rsa_private_key.public_key(), algorithms=['RS256'], audience='https://api.combocurve.com'
        )
        assert claims['iss'] == claims['sub'] == 'sample@example.iam.gserviceaccount.com'
        assert claims['exp'] - claims['iat'] == 3600
        assert jwt.get_unverified_header(token) == {'alg': 'RS256', 'typ': 'JWT', 'kid': 'sample-key-id'}

    def test_token_is_signed_once_until_near_expiry(
        self, service_account_credentials: dict[str, str], monkeypatch: MonkeyPatch
    ) -> None:
        now = [1_000_000.0]
        monkeypatch.setattr(time, 'time', lambda: now[0])
        signatures: list[int] = []
        real_encode = jwt.encode

        def counting_encode(*args: Any, **kwargs: Any) -> str:
            signatures.append(1)
            token: str = real_encode(*args, **kwargs)
            return token

        monkeypatch.setattr(jwt, 'encode', counting_encode)
        service_account_auth = auth.ServiceAccountAuth(
            auth.ServiceAccount.from_mapping(service_account_credentials), API_KEY
        )
        for _ in range(10):
            service_account_auth.get_auth_headers()
        assert len(signatures) == 1
        now[0] += 3600 - 60
        service_account_auth.get_auth_headers()
        assert len(signatures) == 2

    def test_private_key_is_not_in_repr(self, service_account_credentials: dict[str, str]) -> None:
        account = auth.ServiceAccount.from_mapping(service_account_credentials)
        assert 'PRIVATE KEY' not in repr(account)


class TestCredentialsFile:
    def test_oauth_type_gives_oauth_auth(self, tmp_path: Path) -> None:
        path = write_json(tmp_path / 'credentials.json', OAUTH_CREDENTIALS)
        assert isinstance(auth.auth_from_credentials_file(path, API_KEY), auth.OAuthClientAuth)

    def test_service_account_type_gives_service_account_auth(
        self, tmp_path: Path, service_account_credentials: dict[str, str]
    ) -> None:
        path = write_json(tmp_path / 'credentials.json', service_account_credentials)
        assert isinstance(auth.auth_from_credentials_file(path, API_KEY), auth.ServiceAccountAuth)

    def test_missing_type_is_read_as_service_account(
        self, tmp_path: Path, service_account_credentials: dict[str, str]
    ) -> None:
        """`combocurve-api-v1` never read `type`, so a legacy file without it must keep working."""
        untyped = {key: value for key, value in service_account_credentials.items() if key != 'type'}
        path = write_json(tmp_path / 'credentials.json', untyped)
        assert isinstance(auth.auth_from_credentials_file(path, API_KEY), auth.ServiceAccountAuth)

    def test_unknown_type_raises_naming_the_accepted_types(self, tmp_path: Path) -> None:
        path = write_json(tmp_path / 'credentials.json', {'type': 'something_else'})
        with pytest.raises(ValueError, match='combocurve_oauth2_client'):
            auth.auth_from_credentials_file(path, API_KEY)


class TestCredentialsDirectory:
    def test_oauth_directory(self, tmp_path: Path) -> None:
        write_native_directory(tmp_path, oauth_credentials=OAUTH_CREDENTIALS)
        assert isinstance(auth.auth_from_credentials_directory(tmp_path), auth.OAuthClientAuth)

    def test_service_account_directory(self, tmp_path: Path, service_account_credentials: dict[str, str]) -> None:
        write_native_directory(tmp_path, service_account_credentials=service_account_credentials)
        assert isinstance(auth.auth_from_credentials_directory(tmp_path), auth.ServiceAccountAuth)

    def test_zip_folder_inside_the_directory_is_found(self, tmp_path: Path) -> None:
        """The download unzips to a `combocurve/` folder; unzipping in place must work."""
        write_native_directory(tmp_path / 'combocurve', oauth_credentials=OAUTH_CREDENTIALS)
        assert isinstance(auth.auth_from_credentials_directory(tmp_path), auth.OAuthClientAuth)

    def test_api_key_is_read_from_api_key_txt_stripped(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        write_native_directory(tmp_path, oauth_credentials=OAUTH_CREDENTIALS)
        monkeypatch.setattr(requests, 'post', FakeTokenEndpoint(token_response()))
        assert auth.auth_from_credentials_directory(tmp_path).get_auth_headers()['x-api-key'] == API_KEY

    def test_both_types_use_oauth_and_warn(self, tmp_path: Path, service_account_credentials: dict[str, str]) -> None:
        write_native_directory(
            tmp_path, oauth_credentials=OAUTH_CREDENTIALS, service_account_credentials=service_account_credentials
        )
        with pytest.warns(DeprecationWarning, match=r'3.1.0') as recorded:
            client_auth = auth.auth_from_credentials_directory(tmp_path)
        assert isinstance(client_auth, auth.OAuthClientAuth)
        # Attributed to this test, not to a frame inside the package.
        assert recorded[0].filename == __file__

    def test_no_api_key_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match=r'api-key.txt'):
            auth.auth_from_credentials_directory(tmp_path)

    def test_no_credentials_file_raises(self, tmp_path: Path) -> None:
        write_native_directory(tmp_path)
        with pytest.raises(FileNotFoundError, match=r'api-credentials.json'):
            auth.auth_from_credentials_directory(tmp_path)


@pytest.fixture
def home_directory(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Points the package's default `~/.combocurve` paths at an empty temporary directory."""
    directory = tmp_path / '.combocurve'
    directory.mkdir()
    monkeypatch.setattr(config, 'COMBOCURVE_DIRECTORY', directory)
    monkeypatch.setattr(config, 'COMBOCURVE_JSON', directory / 'combocurve.json')
    monkeypatch.setattr(config, 'CC_API_CONFIG_JSON', directory / 'cc-api.config.json')
    monkeypatch.setattr(config, 'cfg', config.Configuration(apikey='legacy-layout-key'))
    return directory


class TestClientConstruction:
    def test_default_constructor_reads_native_files(self, home_directory: Path) -> None:
        write_native_directory(home_directory, oauth_credentials=OAUTH_CREDENTIALS)
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            api = ComboCurveAPI()
        assert isinstance(api.auth, auth.OAuthClientAuth)

    def test_default_constructor_prefers_native_files_over_the_old_layout(
        self, home_directory: Path, service_account_credentials: dict[str, str]
    ) -> None:
        write_native_directory(home_directory, oauth_credentials=OAUTH_CREDENTIALS)
        write_json(home_directory / 'combocurve.json', service_account_credentials)
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            api = ComboCurveAPI()
        assert isinstance(api.auth, auth.OAuthClientAuth)

    @pytest.mark.parametrize('credentials_type', ['oauth', 'service_account'])
    def test_default_constructor_reads_the_old_layout_with_a_warning(
        self, credentials_type: str, home_directory: Path, service_account_credentials: dict[str, str]
    ) -> None:
        document = OAUTH_CREDENTIALS if credentials_type == 'oauth' else service_account_credentials
        write_json(home_directory / 'combocurve.json', document)
        with pytest.warns(DeprecationWarning, match=r'3.0.0'):
            api = ComboCurveAPI()
        expected = auth.OAuthClientAuth if credentials_type == 'oauth' else auth.ServiceAccountAuth
        assert isinstance(api.auth, expected)

    def test_from_credentials_directory(self, tmp_path: Path) -> None:
        write_native_directory(tmp_path, oauth_credentials=OAUTH_CREDENTIALS)
        api = ComboCurveAPI.from_credentials_directory(tmp_path)
        assert isinstance(api, ComboCurveAPI)
        assert isinstance(api.auth, auth.OAuthClientAuth)

    @pytest.mark.parametrize('path_type', [str, Path])
    def test_from_alternate_config_reads_either_type_with_a_warning(
        self, path_type: Any, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        credentials_path = write_json(tmp_path / 'combocurve.json', OAUTH_CREDENTIALS)
        config_path = write_json(tmp_path / 'cc-api.config.json', {'apikey': API_KEY})
        monkeypatch.setattr(requests, 'post', FakeTokenEndpoint(token_response()))
        with pytest.warns(DeprecationWarning, match='from_credentials_directory'):
            api = ComboCurveAPI.from_alternate_config(path_type(credentials_path), path_type(config_path))
        assert api._auth_headers()['x-api-key'] == API_KEY
        assert api._auth_headers()['x-backend-version'] == 'v2'

    def test_auth_argument_is_used_as_given(self) -> None:
        stand_in = auth.ServiceAccountAuth.__new__(auth.ServiceAccountAuth)
        assert ComboCurveAPI(auth=stand_in).auth is stand_in


class TestDefaultConfiguration:
    def test_native_api_key_is_preferred(self, home_directory: Path) -> None:
        write_native_directory(home_directory)
        write_json(home_directory / 'cc-api.config.json', {'apikey': 'old-key'})
        assert config._load_default_configuration().apikey == API_KEY

    def test_old_config_file_is_the_fallback(self, home_directory: Path) -> None:
        write_json(home_directory / 'cc-api.config.json', {'apikey': 'old-key'})
        assert config._load_default_configuration().apikey == 'old-key'

    def test_neither_file_raises(self, home_directory: Path) -> None:
        with pytest.raises(FileNotFoundError):
            config._load_default_configuration()


class TestNextPageUrl:
    @pytest.mark.parametrize(
        ('link_header', 'expected'),
        [
            ('<https://api.example/v1/wells?skip=25>;rel="next"', 'https://api.example/v1/wells?skip=25'),
            ('<https://api.example/v1/wells?skip=25>; rel="next"', 'https://api.example/v1/wells?skip=25'),
            ('<https://api.example/a>;rel="prev", <https://api.example/b>;rel="next"', 'https://api.example/b'),
            ('<https://api.example/a>;rel=next', 'https://api.example/a'),
            ('<https://api.example/a>;rel="prev"', None),
            ('', None),
        ],
    )
    def test_next_link(self, link_header: str, expected: Optional[str]) -> None:
        headers = {'Link': link_header} if link_header else {}
        assert base.get_next_page_url(headers) == expected

    @pytest.mark.parametrize(
        'link_url',
        [
            'https://external-api-000000000000.us-central1.run.app/v1/projects?take=200&cursor=abc',
            '/v1/projects?take=200&cursor=abc',
            'https://api.combocurve.com/v1/projects?take=200&cursor=abc',
        ],
    )
    def test_next_page_keeps_the_request_host(self, link_url: str) -> None:
        """The v2 backend links to its internal Cloud Run host; the credentials must not go there."""
        next_page_url = base._next_page_url_on_request_origin(
            {'Link': f'<{link_url}>;rel="next"'}, 'https://api.combocurve.com/v1/projects?take=200'
        )
        assert next_page_url == 'https://api.combocurve.com/v1/projects?take=200&cursor=abc'

    def test_page_loop_requests_every_page_on_the_api_host(self, monkeypatch: MonkeyPatch) -> None:
        requested_urls: list[str] = []
        internal_link = '<https://external-api-000000000000.us-central1.run.app/v1/projects?cursor=abc>;rel="next"'
        pages = [FakeResponse(200, [{'id': 'a'}], headers={'Link': internal_link}), FakeResponse(200, [{'id': 'b'}])]

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            requested_urls.append(url)
            return pages.pop(0)

        monkeypatch.setattr(requests, 'request', fake_request)
        api = make_offline_api()
        items = api._get_items('https://api.combocurve.com/v1/projects', params={'take': 200})
        assert [item['id'] for item in items] == ['a', 'b']
        assert requested_urls == [
            'https://api.combocurve.com/v1/projects',
            'https://api.combocurve.com/v1/projects?cursor=abc',
        ]
