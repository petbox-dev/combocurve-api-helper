import pytest

from combocurve_api_helper.base import ItemList
from combocurve_api_helper.models import Models


def test_post_put_delete_assignment_generics_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    m = Models.__new__(Models)  # no auth/__init__
    monkeypatch.setattr(m, "get_econ_model_assignments_by_type_by_id_url",
                        lambda pid, t, mid, filters=None: f"URL/{pid}/{t}/{mid}")
    monkeypatch.setattr(m, "_post_items", lambda url, data: ("POST", url, data))
    monkeypatch.setattr(m, "_put_items", lambda url, data: ("PUT", url, data))
    monkeypatch.setattr(m, "_delete_responses", lambda url, data: ("DEL", url, data))
    body: ItemList = [{"scenario": "s", "qualifierName": "P50", "wells": ["w"], "allWells": False}]
    post_result: object = m.post_econ_model_assignments_by_type_by_id("p", "Capex", "id", body)
    assert post_result == ("POST", "URL/p/Capex/id", body)
    put_result: object = m.put_econ_model_assignments_by_type_by_id("p", "Capex", "id", body)
    assert put_result == ("PUT", "URL/p/Capex/id", body)
    delete_result: object = m.delete_econ_model_assignments_by_type_by_id("p", "Capex", "id", body)
    assert delete_result == ("DEL", "URL/p/Capex/id", body)
