"""The forecast volume PUTs send one request to the volumes url and refuse an empty body before sending."""

from typing import Any

import pytest

from combocurve_api_helper.forecasts import Forecasts


def test_put_forecast_volumes_send_one_request_each(monkeypatch: pytest.MonkeyPatch) -> None:
    f = Forecasts.__new__(Forecasts)
    monkeypatch.setattr(f, 'get_forecast_daily_volumes_url', lambda p, fc: f'DAILY/{p}/{fc}')
    monkeypatch.setattr(f, 'get_forecast_monthly_volumes_url', lambda p, fc: f'MONTHLY/{p}/{fc}')
    calls: list[tuple[str, int]] = []

    def fake_put_items(url: str, data: Any, chunksize: Any = None) -> list[Any]:
        calls.append((url, len(data)))
        return [{'status': 'ok'}]

    monkeypatch.setattr(f, '_put_items', fake_put_items)
    daily: Any = [{'well': 'w1'}]
    monthly: Any = [{'well': 'w1'}, {'well': 'w2'}]
    daily_result: Any = f.put_forecast_daily_volumes('p', 'fc', daily)
    monthly_result: Any = f.put_forecast_monthly_volumes('p', 'fc', monthly)
    assert daily_result == [{'status': 'ok'}]
    assert monthly_result == [{'status': 'ok'}]
    assert calls == [('DAILY/p/fc', 1), ('MONTHLY/p/fc', 2)]

    with pytest.raises(ValueError):
        f.put_forecast_daily_volumes('p', 'fc', [])
    with pytest.raises(ValueError):
        f.put_forecast_monthly_volumes('p', 'fc', [])
    assert len(calls) == 2
