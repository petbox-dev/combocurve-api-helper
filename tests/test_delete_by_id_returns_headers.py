"""Deletes by id whose route answers success with 204 and an empty body return the response headers.

`delete_project_by_id` (dev, 2026-11-22) and `delete_forecast_configuration_by_id` (the collection's saved
success response) used to parse that empty body and raise `JSONDecodeError` after the delete went through.
"""

from typing import Any

import pytest
import requests

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
