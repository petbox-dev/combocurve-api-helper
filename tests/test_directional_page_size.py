"""`get_directional_surveys` asks for at most 100 surveys per page.

The API answers `take=1000` with `400 ... Must be between 1 and 100` (verified live 2026-11-05), so
every call failed before any survey was returned
(docs/todo/closed/directional-surveys-page-size-above-api-maximum.md).
"""

from typing import Any

import requests
from pytest import MonkeyPatch

from combocurve_api_helper.directional import GET_LIMIT
from tests.http_fakes import FakeResponse, make_offline_api

API_MAXIMUM_TAKE = 100


def test_the_page_size_is_within_the_api_maximum() -> None:
    assert 1 <= GET_LIMIT <= API_MAXIMUM_TAKE


def test_get_directional_surveys_sends_take_100(monkeypatch: MonkeyPatch) -> None:
    sent: list[Any] = []

    def recorder(
        method: str, url: str, headers: Any = None, params: Any = None, json: Any = None, timeout: Any = None
    ) -> FakeResponse:
        sent.append(params)
        return FakeResponse(200, [])

    monkeypatch.setattr(requests, 'request', recorder)

    make_offline_api().get_directional_surveys({'well': '000000000000000000000001'})

    assert sent == [{'take': API_MAXIMUM_TAKE}]
