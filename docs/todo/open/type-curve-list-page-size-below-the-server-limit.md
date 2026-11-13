# Type-curve list page size is below the server limit

Severity: low
Opened: 2026-11-13

## What happens now

`get_type_curves` (`typecurves.py`) pages with `GET_LIMIT = 200`. The comment on the module's
constants says "the type-curve list and volumes accept 2,500 although their schemas say 200", and
`get_type_curve_volumes` uses `VOLUMES_GET_LIMIT = 2500`. A project with n type curves costs
ceil(n/200) requests instead of ceil(n/2500).

Separately, the forecast-outputs route is read at 1,000 per page by `forecasts.get_forecast_outputs`
(`GET_LIMIT_OUTPUTS_ARIES`) and at 200 by `type_curves_v1_compatibility.py`
(`FORECAST_OUTPUTS_GET_LIMIT`).

## Unverified

That the list route accepts 2,500 today. The comment records an observation of 2026-11-05.

## What would unblock it

One live `GET /v2/projects/{id}/type-curves?take=2500` against a project with more than 200 type
curves. Then use the larger page size, or correct the comment.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phase 1 efficiency pass.
