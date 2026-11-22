# Forecast segment parameter `slope` on write is unverified

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

## Files

`src/combocurve_api_helper/forecasts.py`
