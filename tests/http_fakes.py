"""Shared offline test doubles for the HTTP transport: a fake response, a recording transport, a stub
auth object, and a client built without credentials.

One copy, so a double cannot drift from production on its own. `FakeResponse` matches the parts of
`requests.Response` the transport reads, including the error paths: `headers` is case-insensitive,
`raise_for_status` raises `HTTPError` at 400 and above, and `json()` raises
`requests.exceptions.JSONDecodeError` for a body that is not JSON (a gateway's HTML error page).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional

import requests
from pytest import MonkeyPatch
from requests.structures import CaseInsensitiveDict

from combocurve_api_helper import ComboCurveAPI


class FakeResponse:
    """Stand-in for `requests.Response`. Pass `body` for a JSON body, or `text` alone for a body that
    is not JSON, so that `json()` raises as the real object does."""

    def __init__(
        self,
        status_code: int = 200,
        body: Any = None,
        *,
        headers: Optional[Mapping[str, str]] = None,
        text: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self._body = body
        self._body_is_json = text is None
        self.text = str(body) if text is None else text
        self.headers: CaseInsensitiveDict[str] = CaseInsensitiveDict(headers or {})
        # `requests.Response` carries both; code that reports an `HTTPError` reads them (the
        # `tests/conftest.py` report hook). `request` is None, as on a hand-built `Response`.
        self.url = ''
        self.request: Optional[requests.PreparedRequest] = None

    @property
    def ok(self) -> bool:
        """True below 400, as `requests.Response.ok`."""
        return self.status_code < 400

    def json(self) -> Any:
        """The JSON body; raises `JSONDecodeError` (a `ValueError`) when the body is not JSON."""
        if not self._body_is_json:
            raise requests.exceptions.JSONDecodeError('Expecting value', self.text, 0)
        return self._body

    def raise_for_status(self) -> None:
        """Raise `HTTPError` for a 4xx or 5xx status, as `requests.Response.raise_for_status`."""
        if self.status_code >= 400:
            raise requests.HTTPError(f'{self.status_code} error', response=self)  # type: ignore[arg-type]


class StubAuth:
    """Stands in for the auth object; the transport only asks it for headers. Counts the fetches."""

    def __init__(self) -> None:
        self.fetches = 0

    def get_auth_headers(self) -> dict[str, str]:
        """No headers: the transport tests model HTTP responses, not the token request."""
        self.fetches += 1
        return {}


@dataclass(frozen=True)
class RecordedCall:
    """One request the transport sent: the verb (upper case, as `requests` sends it), the url, the
    `params` mapping, the JSON body and the timeout."""

    method: str
    url: str
    params: Any
    body: Any
    timeout: Any


@dataclass
class RecordingTransport:
    """Stands in for `requests.request`: answers the queued `responses` in order and keeps every call.
    The signature is the keyword set `base._send_request` passes, so an unexpected keyword fails. One
    request more than there are responses raises `IndexError`, so an extra request does not pass
    unseen."""

    responses: list[FakeResponse]
    calls: list[RecordedCall] = field(default_factory=list)

    def __call__(
        self,
        method: str,
        url: str,
        headers: Any = None,
        params: Optional[Any] = None,
        json: Any = None,
        timeout: Any = None,
    ) -> FakeResponse:
        self.calls.append(RecordedCall(method.upper(), url, params, json, timeout))
        return self.responses.pop(0)


def install_recording_transport(monkeypatch: MonkeyPatch, *responses: FakeResponse) -> RecordingTransport:
    """Patch `requests.request` with a `RecordingTransport` that answers `responses` in order; returns
    it."""
    transport = RecordingTransport(list(responses))
    monkeypatch.setattr(requests, 'request', transport)
    return transport


def make_offline_api(auth: Optional[StubAuth] = None) -> ComboCurveAPI:
    """A client that reads no credentials from disk. (Importing the package still needs an API key in
    `~/.combocurve`: `config.py` reads it at import.)"""
    return ComboCurveAPI(auth=auth if auth is not None else StubAuth())
