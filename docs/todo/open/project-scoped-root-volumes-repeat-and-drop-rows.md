# Project-scoped root volume listing repeats and drops rows

Severity: medium
Opened: 2026-11-20
Updated: 2026-11-21 (second investigation on dev; per-forecast fallback implemented and verified, below)

## What happens now

`get_root_forecast_daily_volumes({'project': P})` and the monthly variant return the wrong rows on
every dev project with more than 200 rows. Two failure shapes, both silent:

1. **Repeated and missing pairs on full pages.** On a project of 3,983 monthly rows (12 forecasts)
   the listing returns 3,983 rows covering 3,635 distinct `(forecast, well)` pairs: 348 pairs appear
   twice and 348 are absent. The row total matches the count, so a count check passes.
2. **Short page, no next link: early stop.** On four projects (216, 263, 573 and 1,107 rows) the
   first page holds fewer than `take` rows (36, 84, 140 and 123) and its `Link` header has only
   `rel="first"`, no `rel="next"`. `_get_items` stops there. The method returns 6% to 24% of the
   project with no error. Walking `skip` by hand past the short page finds more rows, but still not
   all of them (52 of 216, 136 of 263, 416 of 573, 722 of 1,107, no repeats): rows are lost inside
   each page, not only at the end.

The first page of a short-page project held the rows of one forecast, or two (on the 84-row project
the first page held 25 of one forecast's 36 rows and 34 of the other's 48).

The count is right: on all 9 dev projects the project-scoped count equals the sum of the
forecast-scoped counts (daily and monthly; the daily count equals the monthly count on every project).

This explains the earlier unexplained daily result, "84 from the count, 59 rows from the list": the
dev project with 84 rows (2 forecasts) returns a short first page of 59 monthly rows with no next link
(the daily listing of that project was not re-run).

## Measurements (dev, 2026-11-21, read-only)

Projects are named by size. "Truth" is the union of the forecast-scoped listings
(`{'forecast': F}`) of the project's forecasts.

| Project rows (count) | Forecasts | Monthly, `take` 200 | Daily, `take` 200 |
|---|---|---|---|
| 216 | 6 | 1 page, 36 rows, 180 missing | not run |
| 263 | 6 | 1 page, 84 rows, 179 missing | 1 page, 84 rows, 179 missing |
| 573 | 19 | 1 page, 140 rows, 433 missing | 1 page, 140 rows, 433 missing |
| 1,107 | 9 | 1 page, 123 rows, 984 missing | 1 page, 123 rows, 984 missing |
| 3,983 | 12 | 20 pages, 3,983 rows, 3,635 distinct, 348 repeated, 348 missing | page 6 (`skip` 1000) answers HTTP 500 with an empty body, twice; `take` 100: 40 pages, 3,983 rows, 3,715 distinct, 268 repeated |
| 24,798 | 36 | 7 pages, 1,399 rows (2 of 36 forecasts), 1,361 distinct, 38 repeated, 23,437 missing; page 7 had no next link | not run |
| 29,306 | 24 | 7 pages, 1,399 rows (6 of 24 forecasts), no repeats, 27,907 missing; page 7 had no next link | not run |

On the projects compared with their truth set, no project-scoped row was outside it (nothing is
mislabelled).

Page size changes which rows go wrong, never fixes it (monthly):

| Project rows | `take` 200 | `take` 100 | `take` 50 |
|---|---|---|---|
| 84 | 59 rows, 1 page | 59 rows, 1 page | 36 rows, 1 page |
| 216 | 36 rows, 1 page | 36 rows, 1 page | 36 rows, 1 page |
| 263 | 84 rows, 1 page | 84 rows, 1 page | 263 rows, 235 distinct, 28 repeated |
| 573 | 140 rows, 1 page | 185 rows, 140 distinct, 45 repeated | 195 rows, 184 distinct, 11 repeated |
| 1,107 | 123 rows, 1 page | 1,107 rows, 951 distinct, 156 repeated | 1,107 rows, 995 distinct, 112 repeated |
| 3,983 | 3,983 rows, 348 repeated | 3,983 rows, 268 repeated | 3,983 rows, 114 repeated |

Ordering cannot be requested: the collection documents no `sort` for the root volume routes, and
`sort=well` or `sort=-forecast` returns 400 `FieldNameFilterError: Unrecognized filter `sort``. The
collection documents no `cursor` for them either (the path-level routes document both).

The forecast-scoped listing is clean on every dev forecast checked: rows equal the count, no repeated
pair, for every forecast of every dev project (38 forecasts above 400 rows; the largest 6,890 rows).

## Reproduce

Needs dev credentials in `~/.combocurve/dev`. Read-only. Run from the repo root with
`PYTHONPATH=src`. `PROJECT_ID` is any dev project with more than 200 root rows.

```python
from collections import Counter
from pathlib import Path
from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import _next_page_url_on_request_origin

api = ComboCurveAPI.from_credentials_directory(Path.home() / '.combocurve' / 'dev')
PROJECT_ID = '...'


def page_pairs(url):
    params = {'take': 200}
    rows = []
    while True:
        response = api._request_with_retry('get', url, params=params)
        response.raise_for_status()
        rows.extend((str(r['forecast']), str(r['well'])) for r in response.json())
        next_url = _next_page_url_on_request_origin(response.headers, url)
        if next_url is None:
            return rows
        url, params = next_url, None


rows = page_pairs(api.get_root_forecast_monthly_volumes_url({'project': PROJECT_ID}))
truth = set()
for forecast in api.get_forecasts(PROJECT_ID):
    truth |= set(page_pairs(api.get_root_forecast_monthly_volumes_url({'forecast': str(forecast['id'])})))
pairs = Counter(rows)
print('count', api.count_root_forecast_monthly_volumes({'project': PROJECT_ID}), 'rows', len(rows),
      'distinct', len(pairs), 'repeated', sum(1 for c in pairs.values() if c > 1), 'missing', len(truth - set(pairs)))
```

## Example (one well, forecasts named by role)

The project-scoped listing returns one forecast ("Forecast A") twice for a well, each copy with
`phases: []`. The path-level route returns Forecast A once, also with `phases: []`. The path-level
route returns a second forecast ("Forecast B") for the same well with populated `phases`
(oil, gas, water; volumes present). The project-scoped listing omits Forecast B for that well.

## What was ruled out

- Paging links on full pages: each `Link` keeps `project=` and advances `skip` by 200.
- Paging instability: two full passes return the same rows in the same order.
- Rows mislabelled under another forecast: no project-scoped row falls outside the forecast-scoped union.
- A single larger page: `take` above 200 returns 400.
- A page size that avoids it: 50, 100 and 200 all fail (table above).
- Requesting an order: `sort` is refused (400).

## What is still unverified

- The server-side cause. The short pages suggest the server takes a window of `take` documents and
  drops some before it answers, then omits `rel="next"` because the page is short; the repeats suggest
  a non-unique sort key with offset paging. Neither is confirmed; only ComboCurve can say.
- Whether the production tenant behaves the same (only dev was read).

## Fallback implemented and verified on dev (2026-11-21)

`get_root_forecast_daily_volumes` and `..._monthly_volumes` now read `project` without `forecast`
one forecast at a time (alternative 1 below): one HEAD count of the project, `get_forecasts`, then one
forecast-scoped listing per forecast with the caller's other filters (`project` replaced by
`forecast`, so `well` with `project` now works). Rows are grouped by forecast in `get_forecasts`
order. A row total that differs from the project count raises `RuntimeError`; the check (and the
count) is skipped when `well`, `startDate`, `endDate` or any other filter except `take` and a `skip`
of 0 has a value. `skip` other than 0 and `cursor` are refused with this scope. The counts are
unchanged. Offline tests: `tests/test_root_volumes_per_forecast.py`.

Live check, dev, read-only, through the new method with `{'project': P}`:

| Project rows (count) | Forecasts | Resolution | Rows | Repeated pairs | Forecasts whose rows differ from their forecast count | Time |
|---|---|---|---|---|---|---|
| 3,983 | 12 | monthly | 3,983 | 0 | 0 | 92 s |
| 3,983 | 12 | daily | 3,983 | 0 | 0 | 78 s |
| 24,798 | 36 | monthly | 24,798 | 0 | 0 | 639 s |

`{'project': P, 'well': [3 wells]}` on the 3,983-row project: 33 rows over 12 forecasts, equal to
the sum of the forecast-and-well counts, no repeats, no row outside the filter.

The item stays open: the server defect itself is unreported to ComboCurve, and the fallback costs a
listing per forecast (the 24,798-row project took about 11 minutes). When ComboCurve fixes the
project-scoped listing, the fallback can go.

## Fix: alternatives

Before 2026-11-21 the method did not correct this; its docstring stated the defect and pointed to
the forecast-scoped call. Alternative 1 is now implemented (section above).

1. **Client-side per-forecast fallback (recommended).** When `filters` has `project` and no
   `forecast`, list the project's forecasts (`get_forecasts`, paged) and call the forecast-scoped
   listing once per forecast with the other filters (`startDate`, `endDate`), concatenating the rows.
   Same signature, correct rows on every dev forecast tested. Costs one list call plus one listing per
   forecast (a 36-forecast project: 37 listings instead of one). Can check its own result against
   `count_root_forecast_*_volumes({'project': P})` and raise on a mismatch. Caller-visible change: row
   order becomes grouped by forecast.
2. **Refuse `project` without `forecast`** (`ValueError`, like the `well` rule). Honest and cheap,
   but breaking for current callers; the count method can keep accepting `project`.
3. **Warn** (`RuntimeWarning`) and return the server's rows. Not a fix: the data stays wrong, and
   warnings are often filtered.
4. **Detect only**: compare the rows with the count and the distinct-pair count and raise
   on a mismatch. Catches the short-page case (rows < count) and the repeat case (distinct < rows),
   but leaves the caller with no data.

Recommendation: 1, because it returns correct data without a signature change and the cost is a
call per forecast; report the defect to ComboCurve support so the fallback can go when it is fixed.

## Blast radius

- `Root.get_root_forecast_daily_volumes` and `..._monthly_volumes` with a `project` filter and no
  `forecast`. Their counts are right.
- Forecast-scoped root calls and the path-level `Forecasts.get_forecast_*_volumes` are not affected as
  far as checked.

## Files

- `src/combocurve_api_helper/root.py`: `get_root_forecast_daily_volumes`, `get_root_forecast_monthly_volumes`
- `src/combocurve_api_helper/forecasts.py`: path-level volume methods; cross-reference docstrings
- `src/combocurve_api_helper/base.py`: `_request_items_pages`, `_next_page_url_on_request_origin`
