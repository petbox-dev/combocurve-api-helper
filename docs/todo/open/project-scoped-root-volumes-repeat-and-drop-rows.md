# Project-scoped root volume listing repeats and drops rows

Severity: high
Opened: 2026-11-20

## What happens now

`get_root_forecast_daily_volumes({'project': P})` and the monthly variant return rows whose
`(forecast, well)` pairs are partly repeated and partly missing. On the reference dev project the
listing holds 3,983 monthly rows covering 3,635 distinct pairs: 348 pairs appear twice and the same
number are absent. The total matches the count and the sum of the per-forecast path-level counts, so
a count check passes while the per-forecast split is wrong. The listing is repeatable: two full
passes return identical rows in identical order.

The defect is specific to this listing so far. The forecast-scoped root listing
(`{'forecast': F}`, 361 rows over two pages) and the path-level route
(`get_forecast_monthly_volumes`, one page) are clean for the forecast tested.

## Reproduce

Needs dev credentials in `~/.combocurve/dev` and `CC_DEV_PROJECT_ID` set to a dev project with
monthly volumes under 12 forecasts. Read-only. Run from the repo root with `PYTHONPATH=src`.

```python
import os
from collections import Counter
from pathlib import Path
from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import _next_page_url_on_request_origin

api = ComboCurveAPI.from_credentials_directory(Path.home() / '.combocurve' / 'dev')
project_id = os.environ['CC_DEV_PROJECT_ID']

# 1. Page through the project-scoped root listing (take is capped at 200; 400 above that).
url = api.get_root_forecast_monthly_volumes_url({'project': project_id})
params = {'take': 200}
rows = []
while True:
    response = api._request_with_retry('get', url, params=params)
    response.raise_for_status()
    rows.extend(response.json())
    next_url = _next_page_url_on_request_origin(response.headers, url)
    if next_url is None:
        break
    url, params = next_url, None
pairs = Counter((str(r['forecast']), str(r['well'])) for r in rows)
print('rows', len(rows), 'distinct', len(pairs), 'repeated', sum(1 for c in pairs.values() if c > 1))

# 2. Compare with the path-level route, forecast by forecast (one page each).
forecasts = api.get_forecasts(project_id, {'take': '50'})
path_total = sum(api.count_forecast_monthly_volumes(project_id, str(f.get('_id') or f.get('id'))) for f in forecasts)
print('path-level total', path_total, 'project-scoped count', api.count_root_forecast_monthly_volumes({'project': project_id}))
```

Expected on the reference project: 3,983 rows, 3,635 distinct, 348 repeated; path-level total 3,983.

## Example (one well, forecasts named by role)

The project-scoped listing returns one forecast ("Forecast A") twice for a well, each copy with
`phases: []`. The path-level route returns Forecast A once, also with `phases: []`. The path-level
route returns a second forecast ("Forecast B") for the same well with populated `phases`
(oil, gas, water; volumes present). The project-scoped listing omits Forecast B for that well.
Forecast B's row is not present under any label. The copy of Forecast A is identical to the path row.

## What was ruled out

- Paging links: each `Link` keeps `project=` and advances `skip` by 200; no cursor is lost.
- Paging instability: two full passes return the same rows in the same order.
- Page-boundary artifact: no; every duplicate's two copies sit on different pages, 200 to 350 rows apart.
- Rows mislabelled under another forecast: no; the omitted row's content does not appear under any label.
- A single larger page: `take` above 200 returns 400, so this cannot be bypassed.

## What is still unverified

- The server-side sort key. A non-unique key with offset paging would produce this pattern, but I have
  not confirmed it.
- Whether the daily listing and the company-scoped and forecast-scoped listings behave the same
  across more projects. One project has been checked in full.
- An earlier daily result, 84 from the count and 59 rows from the list for the same project, is not
  explained.
- Whether the defect appears on any other project with more than 200 rows.

## Blast radius

- `Root.get_root_forecast_daily_volumes` and `..._monthly_volumes` with a `project` filter, and their
  counts. The docstrings in `root.py` and `forecasts.py` cross-reference this call as the way to read
  several forecasts at once; they must stop doing that until this is settled.
- Forecast-scoped and path-level calls are not affected as far as checked.

## What would unblock it

- A second project with more than 200 root rows checked for repeated pairs.
- The server's ordering for the listing, from the ComboCurve docs or support.
- A forecast-scoped listing with more than 400 rows, to test whether paging alone causes the defect.

## Files

- `src/combocurve_api_helper/root.py`: `get_root_forecast_daily_volumes`, `get_root_forecast_monthly_volumes`
- `src/combocurve_api_helper/forecasts.py`: path-level volume methods; cross-reference docstrings
- `src/combocurve_api_helper/base.py`: `_request_items_pages`, `_next_page_url_on_request_origin`
