"""The forecast volume PUTs send one request to the volumes url and refuse an empty body before sending."""

from typing import Any

import pytest

from tests.http_fakes import FakeResponse, install_recording_transport, make_offline_api


def test_put_forecast_volumes_send_one_request_each(monkeypatch: pytest.MonkeyPatch) -> None:
    api = make_offline_api()
    transport = install_recording_transport(
        monkeypatch, FakeResponse(207, [{'status': 'ok'}]), FakeResponse(207, [{'status': 'ok'}])
    )
    daily: Any = [{'well': 'w1'}]
    monthly: Any = [{'well': 'w1'}, {'well': 'w2'}]
    daily_result: Any = api.put_forecast_daily_volumes('p', 'fc', daily)
    monthly_result: Any = api.put_forecast_monthly_volumes('p', 'fc', monthly)
    assert daily_result == [{'status': 'ok'}]
    assert monthly_result == [{'status': 'ok'}]
    assert [(call.method, call.url, call.body) for call in transport.calls] == [
        ('PUT', api.get_forecast_daily_volumes_url('p', 'fc'), daily),
        ('PUT', api.get_forecast_monthly_volumes_url('p', 'fc'), monthly),
    ]

    with pytest.raises(ValueError):
        api.put_forecast_daily_volumes('p', 'fc', [])
    with pytest.raises(ValueError):
        api.put_forecast_monthly_volumes('p', 'fc', [])
    assert len(transport.calls) == 2


def test_put_forecast_volumes_send_one_record_as_a_one_item_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """`data` may be one well record (the docstring says so): it is sent as a one-item list, not as the
    record's key names."""
    api = make_offline_api()
    transport = install_recording_transport(monkeypatch, FakeResponse(207, []), FakeResponse(207, []))
    record: Any = {'well': 'w1', 'phases': []}
    api.put_forecast_daily_volumes('p', 'fc', record)
    api.put_forecast_monthly_volumes('p', 'fc', record)
    assert [call.body for call in transport.calls] == [[record], [record]]
