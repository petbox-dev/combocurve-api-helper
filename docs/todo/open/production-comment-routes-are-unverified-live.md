# Production-comment routes are unverified live

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
