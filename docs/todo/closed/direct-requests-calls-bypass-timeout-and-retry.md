# Direct requests.* calls bypass the request timeout and every retry

Closed: 2026-11-05 -- settled by: all eight call sites send through `_request_with_retry` (2.7.1 `52095b8` on `2.x`; 3.0.0 `0748709` on `feature/type-curves-v2`), plus a 600 s deadline per
call and a 120 s `Retry-After` cap (2.7.1 `755cb9e`). Test: `tests/test_single_object_requests_use_the_transport.py`.
If this was wrong, you will see: a single-object call (directional surveys, exports, forecast PATCH,
forecast wells, forecast run) that hangs without a timeout, or a 429 that raises at once.
3.0.0 was not published when this was fixed, so the fix is in 3.0.0 itself; all eight sites went to
2.7.1, not only the two export helpers.

Severity: medium
Opened: 2026-09-29

Raised from low on 2026-11-05: a hosted MCP server now consumes the v2 export wrappers (below), so
the missing timeout has a live caller. Release plan: fix in 3.0.0 (or the first 3.0.x if 3.0.0 is
already published), and backport the export part to a 2.7.1.

## What happens now

Eight call sites (six public methods and the two private v2-export helpers behind eight more public
wrappers, 14 public methods in all) call `requests.get/post/put/patch` themselves instead of going through
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
| `forecasts.py:1006` | `post_forecast_run` | POST (line was 992 when opened) |

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

## Blast radius (added 2026-11-05)

A downstream MCP server runs helper calls in a worker-thread pool with a 240 s read deadline. It
answers the user at the deadline, but it cannot stop the thread. A stalled `_post_v2_export` or
`_get_v2_export` therefore holds one pool thread for ever; enough of them fill the pool. That server
holds back its export tools until a helper release has the fix.

## Release plan

- **3.0.0 (or first 3.0.x):** the full fix above, all eight call sites.
- **2.7.1 backport:** at least `exports.py` `_post_v2_export` and `_get_v2_export`, so a 2.7.x
  consumer gets bounded exports without the 3.0.0 type-curve changes. Smallest form: pass
  `timeout=_REQUEST_TIMEOUT_SECONDS` (`base.py`) to both calls; the full move to
  `_request_with_retry` is also acceptable if it applies cleanly to 2.7.0.
- Base the backport on the 2.7.0 release commit `cbb21ec`; it needs a branch, which is the
  maintainer's call.
- Test for either release: patch `exports.requests.post/get` (or `_send_request`) and assert the
  timeout reaches the call; one test per helper.

## What is still unverified

- Whether the v2 export routes and `post_forecast_run` return a `Link` next-page header (they use
  `_extract_json` directly, not the paginated helpers). `_request_with_retry` does not follow pages,
  so this does not block the move.
- Whether any caller catches a raw `requests.ConnectionError` from these methods and would behave
  differently once a GET is retried.
- Whether 3.0.0 is already published: the release commit `a8d65f7` exists locally, but the
  internal index listed 2.7.0 as the newest version on 2026-11-05. This decides 3.0.0 or 3.0.1.

## Files

- `src/combocurve_api_helper/directional.py`, `exports.py`, `forecasts.py`: the methods above
- `src/combocurve_api_helper/base.py`: `_request_with_retry`, `_send_request`, `_gateway_retry_allowed`
- `tests/test_connection_retry.py`: the policy tests to extend
