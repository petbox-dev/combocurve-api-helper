# Forecast output `slope` is now a sign

Closed: 2026-11-21 -- settled by: live check over 3,695 dev forecast outputs: `slope` is the sign for every segment type and `slopeValue` exists only on `linear` segments; no consumer in `src/` reads a forecast-output `slope`; the forecast-output docstrings state the split. The write side is a new item (`forecast-segment-parameter-slope-on-write-is-unverified`)
If this was wrong, you will see: a forecast-output segment whose `slope` is outside -1/0/1, or a non-linear segment carrying `slopeValue`

Severity: low
Opened: 2026-11-05

## What happens now

Per the ComboCurve forum post of 2026-10-29, the `slope` field of a forecast-output segment is the
sign of the slope (-1, 0 or 1) since 2026-10. The value is in `slopeValue`.

## What is unverified

No consumer in this package was checked. The docstring examples in `forecasts.py` show both
`slope` and `slopeValue` with the same spoofed number, which does not show which one carries the sign.
The v2 `linear` fit segment has the same split (read `slope` = sign, write `slope` = value); that case
is handled by `fits_for_put`.

## What to do

Search every consumer of a forecast segment in this package for `slope`. Replace a read of `slope`
that needs the value with `slopeValue`. Verify against live data before changing code.

## Files

`src/combocurve_api_helper/forecasts.py`, `src/combocurve_api_helper/type_curve_conversions.py`

## Status (2026-11-21)

Verified on dev over 3,695 forecast outputs (`get_forecast_outputs`, first page of up to 100 outputs
for up to 6 forecasts per project): `slope` is the sign for every segment type (`arps`,
`arps_modified`, `exp_dec`: -1; `arps_inc`, `exp_inc`: 1; `flat`, `empty`: 0), and `slopeValue` is
present only on `linear` segments, where it is the value (`qStart` 350, `qEnd` 940 over 30 days:
`slope` 1, `slopeValue` 19.67).

No consumer in `src/` reads a forecast-output `slope`. The only code that reads `slope` is
`type_curve_conversions.fits_for_put` (v2 type-curve fits, already handled) and
`fits_to_v1` (copies it unchanged, documented). The split is now stated in the docstrings of
`get_forecast_outputs` and `get_forecast_output_by_id`.

Unverified: whether `post/put_forecast_segment_parameters` read `slope` on write as the value (as v2
type-curve fits do). Checking it needs a write to a forecast the test creates.
