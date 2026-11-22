from __future__ import annotations

from typing import TYPE_CHECKING

from combocurve_api_helper.models import Models
from tests.http_fakes import V1, FakeResponse, install_recording_transport, make_offline_api

if TYPE_CHECKING:
    import pytest

    from combocurve_api_helper.base import ItemList

ASSIGNMENTS = f'{V1}/projects/p/econ-models/capex/id/assignments'


def test_post_put_delete_assignment_generics_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    api = make_offline_api()
    transport = install_recording_transport(
        monkeypatch,
        FakeResponse(207, [{'results': ['posted']}]),
        FakeResponse(207, [{'results': ['put']}]),
        *[FakeResponse(200, [], headers={'X-Delete-Count': '1'})] * 4,
    )

    # Two records: each assignment write goes as ONE request (no chunking), so both are in one body.
    body: ItemList = [
        {'scenario': 's', 'qualifierName': 'P50', 'wells': ['w'], 'allWells': False},
        {'scenario': 's', 'qualifierName': 'P50', 'wells': ['v'], 'allWells': False},
    ]
    post_result: object = api.post_econ_model_assignments_by_type_by_id('p', 'Capex', 'id', body)
    assert post_result == [{'results': ['posted']}]
    put_result: object = api.put_econ_model_assignments_by_type_by_id('p', 'Capex', 'id', body)
    assert put_result == [{'results': ['put']}]

    # DELETE takes query filters, not a body: scenarioId is required, the rest
    # are optional and only added to the filters when provided.
    delete_result: object = api.delete_econ_model_assignments_by_type_by_id(
        'p', 'Capex', 'id', 'scenario1', qualifier_name='P50', wells='w1,w2', all_wells=True
    )
    assert [response.headers['X-Delete-Count'] for response in delete_result] == ['1']  # type: ignore[attr-defined]
    api.delete_econ_model_assignments_by_type_by_id('p', 'Capex', 'id', 'scenario2')

    # `wells` accepts a sequence or a comma-joined str; both become a list, which the
    # url builder sends as one repeated `wells` key per id. The route refuses a
    # comma-joined value (400, verified live 2026-11-21).
    api.delete_econ_model_assignments_by_type_by_id('p', 'Capex', 'id', 'scenario3', wells=['w1', 'w2'])
    api.delete_econ_model_assignments_by_type_by_id('p', 'Capex', 'id', 'scenario4', wells='w1')

    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('POST', ASSIGNMENTS, body),
        ('PUT', ASSIGNMENTS, body),
        ('DELETE', f'{ASSIGNMENTS}?scenarioId=scenario1&qualifierName=P50&wells=w1&wells=w2&allWells=true', None),
        ('DELETE', f'{ASSIGNMENTS}?scenarioId=scenario2', None),
        ('DELETE', f'{ASSIGNMENTS}?scenarioId=scenario3&wells=w1&wells=w2', None),
        ('DELETE', f'{ASSIGNMENTS}?scenarioId=scenario4&wells=w1', None),
    ]


def test_assignment_url_uses_kebab_route_not_econ_model_type() -> None:
    """The assignment {econName} path segment must be the kebab `route`, NOT the
    PascalCase econModelType. FluidModel is the canary: the server rejects
    `FluidModel` (InvalidEconName: fluidmodel) and accepts only `fluid-models`.
    Exercises the real URL builder (no mock)."""
    m = Models.__new__(Models)

    fluid_url = m.get_econ_model_assignments_by_type_by_id_url('proj', 'FluidModel', 'mid')
    assert '/econ-models/fluid-models/mid/assignments' in fluid_url
    assert '/FluidModel/' not in fluid_url  # must NOT use the PascalCase type

    # multi-word type -> hyphenated route, not the run-together PascalCase
    own_url = m.get_econ_model_assignments_by_type_by_id_url('proj', 'OwnershipReversion', 'mid')
    assert '/econ-models/ownership-reversions/mid/assignments' in own_url
    assert '/OwnershipReversion/' not in own_url
