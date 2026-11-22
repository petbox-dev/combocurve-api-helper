"""Deletes by id whose route answers success with 204 and an empty body return the response headers.

`delete_project_by_id` (dev, 2026-11-22) and `delete_forecast_configuration_by_id` (the collection's saved
success response) used to parse that empty body and raise `JSONDecodeError` after the delete went through.
"""

from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from tests.http_fakes import V1, FakeResponse, install_recording_transport, make_offline_api

ID = '0' * 23 + '1'


@pytest.mark.parametrize(
    ('method_name', 'url'),
    [
        ('delete_project_by_id', f'{V1}/projects/{ID}'),
        ('delete_forecast_configuration_by_id', f'{V1}/forecast-configurations/{ID}'),
    ],
)
def test_empty_204_returns_the_headers(monkeypatch: pytest.MonkeyPatch, method_name: str, url: str) -> None:
    transport = install_recording_transport(monkeypatch, FakeResponse(204, None, headers={'X-Delete-Count': '1'}))

    headers: Any = getattr(make_offline_api(), method_name)(ID)

    assert headers['X-Delete-Count'] == '1'
    assert [(call.method, call.url) for call in transport.calls] == [('DELETE', url)]


def test_forecast_configuration_delete_raises_on_a_404(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recording_transport(monkeypatch, FakeResponse(404, {'name': 'NotFound', 'message': 'x'}))

    with pytest.raises(requests.HTTPError):
        make_offline_api().delete_forecast_configuration_by_id(ID)


@pytest.mark.parametrize(
    'delete_by_id',
    [
        lambda api: api.delete_company_production_comment_by_id(''),
        lambda api: api.delete_project_production_comment_by_id('p', ''),
        lambda api: api.delete_company_formation_by_id(''),
        lambda api: api.delete_econ_setting_by_id(''),
        lambda api: api.delete_project_by_id(''),
        lambda api: api.delete_forecast_configuration_by_id(''),
        lambda api: api.delete_type_curve_by_id('p', ''),
        lambda api: api.delete_company_shapefile_by_id(''),
        lambda api: api.delete_scenario_lookup_table_assignment_by_id('p', 's', '', ['w1']),
        lambda api: api.delete_project_by_id('.'),
        lambda api: api.delete_econ_model_assignments_by_type_by_id('p', 'FluidModel', '', 'sc'),
        lambda api: api.delete_scenario_wells('', 'sc', ['w1']),
    ],
)
def test_a_delete_by_a_blank_id_is_refused_before_sending(monkeypatch: MonkeyPatch, delete_by_id: Any) -> None:
    """A blank id would send DELETE to the collection url with a trailing slash: an unfiltered delete if the
    server reads it as the collection route."""
    transport = install_recording_transport(monkeypatch)
    with pytest.raises(ValueError, match='no id'):
        delete_by_id(make_offline_api())
    assert transport.calls == []
