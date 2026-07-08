from typing import Dict, List, Optional, Tuple

import pytest

from combocurve_api_helper.base import ItemList
from combocurve_api_helper.models import Models


def test_post_put_delete_assignment_generics_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    m = Models.__new__(Models)  # no auth/__init__
    captured_url_calls: List[Tuple[str, str, str, Optional[Dict[str, str]]]] = []

    def fake_url(pid: str, t: str, mid: str, filters: Optional[Dict[str, str]] = None) -> str:
        captured_url_calls.append((pid, t, mid, filters))
        return f"URL/{pid}/{t}/{mid}"

    monkeypatch.setattr(m, "get_econ_model_assignments_by_type_by_id_url", fake_url)
    monkeypatch.setattr(m, "_post_items", lambda url, data: ("POST", url, data))
    monkeypatch.setattr(m, "_put_items", lambda url, data: ("PUT", url, data))
    monkeypatch.setattr(m, "_delete_responses", lambda url, data: ("DEL", url, data))

    body: ItemList = [{"scenario": "s", "qualifierName": "P50", "wells": ["w"], "allWells": False}]
    post_result: object = m.post_econ_model_assignments_by_type_by_id("p", "Capex", "id", body)
    assert post_result == ("POST", "URL/p/Capex/id", body)
    put_result: object = m.put_econ_model_assignments_by_type_by_id("p", "Capex", "id", body)
    assert put_result == ("PUT", "URL/p/Capex/id", body)

    # DELETE takes query filters, not a body: scenarioId is required, the rest
    # are optional and only added to the filters dict when provided.
    delete_result: object = m.delete_econ_model_assignments_by_type_by_id(
        "p", "Capex", "id", "scenario1", qualifier_name="P50", wells="w1,w2", all_wells=True)
    assert delete_result == ("DEL", "URL/p/Capex/id", [])
    assert captured_url_calls[-1] == (
        "p", "Capex", "id",
        {"scenarioId": "scenario1", "qualifierName": "P50", "wells": "w1,w2", "allWells": "true"})

    minimal_delete_result: object = m.delete_econ_model_assignments_by_type_by_id("p", "Capex", "id", "scenario2")
    assert minimal_delete_result == ("DEL", "URL/p/Capex/id", [])
    assert captured_url_calls[-1] == ("p", "Capex", "id", {"scenarioId": "scenario2"})

    # `wells` accepts a sequence too -- e.g. a list reused from a POST/PUT body
    # by a JSON-driven caller not protected by mypy's `Optional[str]` type --
    # and must be normalized to the same comma-separated string filter, not
    # passed through as a Python list-repr that matches nothing server-side.
    list_delete_result: object = m.delete_econ_model_assignments_by_type_by_id(
        "p", "Capex", "id", "scenario3", wells=["w1", "w2"])
    assert list_delete_result == ("DEL", "URL/p/Capex/id", [])
    assert captured_url_calls[-1] == ("p", "Capex", "id", {"scenarioId": "scenario3", "wells": "w1,w2"})

    str_delete_result: object = m.delete_econ_model_assignments_by_type_by_id(
        "p", "Capex", "id", "scenario4", wells="w1")
    assert str_delete_result == ("DEL", "URL/p/Capex/id", [])
    assert captured_url_calls[-1] == ("p", "Capex", "id", {"scenarioId": "scenario4", "wells": "w1"})
