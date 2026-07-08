from typing import Any, Dict, List

import pytest
from combocurve_api_helper.scenarios import Scenarios


def test_scenario_assignments_url_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, "get_scenario_by_id_url", lambda p, sc: f"BASE/{p}/{sc}")
    assert s.get_scenario_econ_model_assignments_url("p", "sc") == "BASE/p/sc/assignments/econ-models"
    monkeypatch.setattr(s, "_get_items", lambda url: [("grid", url)])
    result: object = s.get_scenario_econ_model_assignments("p", "sc")
    assert result == [("grid", "BASE/p/sc/assignments/econ-models")]


class _StubResponse:
    def __init__(self, headers: Dict[str, str]) -> None:
        self.headers = headers


def test_delete_scenario_qualifiers_uses_plural_econ_names(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, "get_scenario_by_id_url", lambda p, sc: f"BASE/{p}/{sc}")

    captured_urls: List[str] = []

    def fake_delete_responses(url: str, data: Any) -> List[_StubResponse]:
        captured_urls.append(url)
        return [_StubResponse(headers={"X-Delete-Count": "1"})]

    monkeypatch.setattr(s, "_delete_responses", fake_delete_responses)

    headers: Any = s.delete_scenario_qualifiers("p", "sc", "dates", "P50")

    assert headers == {"X-Delete-Count": "1"}
    assert len(captured_urls) == 1
    url = captured_urls[0]
    assert "econNames=dates" in url
    assert "qualifierNames=P50" in url
    assert "econName=" not in url.replace("econNames=", "")
