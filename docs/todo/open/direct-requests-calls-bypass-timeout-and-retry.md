# Direct requests.* calls bypass the request timeout and every retry

Severity: low
Opened: 2026-09-29

## What happens now

Eight public methods call `requests.get/post/put/patch` themselves instead of going through
`APIBase._request_with_retry` (and so `base._send_request`). They send one request with no timeout
and no retry of any kind: no 429 pause, no 502/503/504 backoff for the GET, no connection retry. A
connection that stalls without a reset blocks the call forever; a dropped connection or a 429 raises
at once.

| File:line | Method | Verb |
|---|---|---|
| `directional.py:197` | `post_directional_surveys` | POST |
| `directional.py:289` | `put_directional_survey_by_id` | PUT |
| `exports.py:46` | `_post_v2_export` | POST |
| `exports.py:58` | `_get_v2_export` | GET |
| `exports.py:140` | `post_export` | POST |
| `forecasts.py:257` | `post_forecast_wells` (one request per chunk) | POST |
| `forecasts.py:336` | `patch_forecast_by_id` | PATCH |
| `forecasts.py:992` | `post_forecast_run` | POST |

Each one fetches `self._auth_headers()` once, sends, and calls `raise_for_status()`.

## Evidence

Found by `grep -n "requests\.\(get\|post\|put\|patch\)" src/` on 2026-09-29, while adding the
timeout and the connection-failure policy to `base.py` (branch `feature/connection-retry`, b2a02e6
and 5d3791a). Not observed failing live.

## Why they were left out

Out of scope for that change: its consumer (`cc-migration`) uses none of them. Each method needs its
own check of how it builds the request (a single-object body, not an `ItemList`; `_get_v2_export` is
polled by the caller) before it is moved.

## Fix

Send each one through `self._request_with_retry(method, url, json_body=data)`. That gives the
timeout, the 429 retry, the GET/HEAD-only gateway retry and the never-sent connection retry. The
writes then keep the rule: never sent again after they were sent. `_get_v2_export` is a GET, so it
also gets the connection and gateway retry.

## What is still unverified

- Whether the v2 export routes and `post_forecast_run` return a `Link` next-page header (they use
  `_extract_json` directly, not the paginated helpers). `_request_with_retry` does not follow pages,
  so this does not block the move.
- Whether any caller catches a raw `requests.ConnectionError` from these methods and would behave
  differently once a GET is retried.

## Files

- `src/combocurve_api_helper/directional.py`, `exports.py`, `forecasts.py`: the methods above
- `src/combocurve_api_helper/base.py`: `_request_with_retry`, `_send_request`, `_gateway_retry_allowed`
- `tests/test_connection_retry.py`: the policy tests to extend
