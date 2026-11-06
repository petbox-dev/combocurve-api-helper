# Forecast output `slope` is now a sign

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
