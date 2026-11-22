# Production-comment routes are unverified live

Closed: 2026-11-22 -- settled by: ComboCurve enabled production comments on dev; every comment route verified live
If this was wrong, you will see: a comment write or delete answering 400 (`RecordCountError`, `RequiredFilterError`) or a list page short of the count

Severity: low
Opened: 2026-11-21

## What happens now

`production_comments.py` wraps the 16 production-comment operations (company and project scope) and the
2 comment-type operations. Only the comment-type routes were verified live. Every comment route answers
404 `ProductionCommentsDisabledError` ("Production comments are not enabled for this tenant") on the dev
tenant and on the production tenant (read-only probe, 2026-11-21).

## What is unverified

- The page size: `GET_LIMIT = 200` is a guess. A wrong maximum makes every list call answer 400.
- Write, update and delete behavior, the `id` filter, and a bulk DELETE with `well` and no dates (allowed
  locally, as the description implies).

## What would unblock it

A tenant with production comments enabled. Then run `CC_LIVE_TEST=1 pytest tests/test_production_comments_live.py`,
probe `take` 200/201 (and higher) on the list route, and record the cap in `production_comments.py`.

## Files

`src/combocurve_api_helper/production_comments.py`, `tests/test_production_comments_live.py`

## Requested from ComboCurve (2026-11-22)

The maintainer asked ComboCurve to enable production comments on the dev tenant and to confirm the list routes' maximum `take` (`docs/local/2026-11-21-combocurve-request-enable-production-comments.md`, git-ignored).

## Settled (2026-11-22, dev)

Both scopes pass `tests/test_production_comments_live.py` (POST, list, count, by id, PUT, PATCH, delete by id).
Probed with 205 throwaway comments on the dev project, all deleted:

- Page size: `take` up to 1001 returned all 205 rows; `take=200` pages through the next link. `GET_LIMIT = 200`
  stays, documented as a choice.
- Writes: a 201-record POST answers 400 `RecordCountError` (at most 200 per request). The helper sent all of
  `data` in one request; it now sends batches of `WRITE_LIMIT = 200` (POST, PUT and PATCH of 205 records: two
  requests, no failures). A 201-record PUT and PATCH answer the same 400.
- The list route has no `id` filter (400 `FieldNameFilterError`); the DELETE `id` filter works.
- A DELETE by `well` needs `startDate` and `endDate` both (400 `RequiredFilterError`), and they match the
  comment's stored dates exactly; a wider range or date-only values delete nothing. The helper now refuses
  `well_id` without both dates.
- A company comment needs a company well (`WellNotFoundError ... in company scope` for a project well).
- `endDate` must be strictly after `startDate`.
