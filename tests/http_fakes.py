"""Shared offline test doubles for the HTTP transport: a fake response, a stub auth object, and a
client built without credentials.

One copy, so a double cannot drift from production on its own. `FakeResponse` matches the parts of
`requests.Response` the transport reads, including the error paths: `headers` is case-insensitive,
`raise_for_status` raises `HTTPError` at 400 and above, and `json()` raises
`requests.exceptions.JSONDecodeError` for a body that is not JSON (a gateway's HTML error page).
"""

from collections.abc import Mapping
from typing import Any, Optional

import requests
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


def make_offline_api(auth: Optional[StubAuth] = None) -> ComboCurveAPI:
    """A client that reads no credentials from disk. (Importing the package still needs an API key in
    `~/.combocurve`: `config.py` reads it at import.)"""
    return ComboCurveAPI(auth=auth if auth is not None else StubAuth())
