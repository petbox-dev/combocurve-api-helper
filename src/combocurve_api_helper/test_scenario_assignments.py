import pytest
from combocurve_api_helper.scenarios import Scenarios


def test_scenario_assignments_url_and_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, "get_scenario_by_id_url", lambda p, sc: f"BASE/{p}/{sc}")
    assert s.get_scenario_econ_model_assignments_url("p", "sc") == "BASE/p/sc/assignments/econ-models"
    monkeypatch.setattr(s, "_get_items", lambda url: [("grid", url)])
    result: object = s.get_scenario_econ_model_assignments("p", "sc")
    assert result == [("grid", "BASE/p/sc/assignments/econ-models")]
