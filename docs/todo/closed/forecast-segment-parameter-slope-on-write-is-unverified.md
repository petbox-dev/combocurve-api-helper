# Forecast segment parameter `slope` on write is unverified

Closed: 2026-11-22 -- settled by: live dev probe 2026-11-22: on a `linear` segment write, `slope` is the value per day (not the sign), `slopeValue` is refused, `slope` and `qEnd` are both required and the server checks `qEnd = qStart + slope * days` within 1e-5; POST and PUT behave the same; only deterministic forecasts accept segment writes. Both docstrings document it and `tests/test_forecast_segment_parameters.py` pins that the body is sent unchanged. The probe also fixed `delete_forecast_by_id` and `delete_forecast_segment_parameters`, which raised on their empty success body
If this was wrong, you will see: a `linear` segment written with its value in `slope` answered with 400 `ParameterRangeError`, or read back with `slopeValue` different from the `slope` sent

Severity: low
Opened: 2026-11-21

## What happens now

Forecast-output reads carry the sign of the slope in `slope` and the value in `slopeValue` (only on
`linear` segments), verified over 3,695 dev outputs on 2026-11-21. The write side has not been checked:
whether `post_forecast_segment_parameters` / `put_forecast_segment_parameters` read `slope` as the value
(as the v2 type-curve `linear` fit does, see `fits_for_put`) or as the sign.

## What would unblock it

On a dev forecast the test creates: write a `linear` segment with a known slope, read it back with
`get_forecast_outputs`, compare `slopeValue`, delete the forecast. Then document the write form in both
method docstrings.

## Findings 2026-11-22 (live, dev)

Probe: a throwaway `API Helper Fixture` forecast with two project wells; one `linear` oil `best` segment per
variant, each written by POST and by PUT (after a segment delete), read back with `get_forecast_outputs`, and
the forecast deleted at the end (none left). POST and PUT behaved the same in every case.

- A probabilistic forecast refuses both writes: 400 `Only deterministic forecasts are supported`.
- `slope` on write is the VALUE in rate units per day. `qStart` 100, `qEnd` 400, 2025-01-01 to 2025-01-31,
  `slope` 10: 201, read back `slope` 1, `slopeValue` 10, `qEnd` 400. `qStart` 400, `qEnd` 100, `slope` -10:
  201, read back `slope` -1, `slopeValue` -10.
- `slope` 1 (the sign) with `qEnd` 400: 400 `ParameterRangeError`, acceptable `qEnd` 129.99999 to 130.00001.
  `slope` 5: the same, range 249.99999 to 250.00001. So `qEnd = qStart + slope * days` is checked, and
  neither field wins: a mismatch is refused.
- `slopeValue` 10 instead of `slope`: 400, `slopeValue provided for the linear segment` and
  `Missing required segment parameter(s): slope`.
- `slope` omitted: 400 `Missing required segment parameter(s): slope`. `qEnd` omitted: 400, the same for
  `qEnd`. The server derives neither.
- A write answers 201 `{"status": "Created", "segmentsCount": 1, "id": <output id>}`: `segmentsCount`, not
  the collection's `segmentCount`.
- Helper defect found: `delete_forecast_segment_parameters` and `delete_forecast_by_id` raised
  `JSONDecodeError` on success, because both routes answer with an empty body. Both now return the response
  headers (`tests/test_forecast_segment_parameters.py`).

The helper sends the segment body unchanged, which is correct. Both write docstrings and the
`get_forecast_outputs` docstring now state the rule.

## Files

`src/combocurve_api_helper/forecasts.py`
