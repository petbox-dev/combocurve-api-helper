"""A recording stand-in for `requests.request`: returns queued responses, keeps every call."""

from dataclasses import dataclass, field
from typing import Any, Optional

from tests.http_fakes import FakeResponse


@dataclass
class RecordedCall:
    method: str
    url: str
    params: Any
    body: Any


@dataclass
class RecordingTransport:
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
        self.calls.append(RecordedCall(method.upper(), url, params, json))
        return self.responses.pop(0)
