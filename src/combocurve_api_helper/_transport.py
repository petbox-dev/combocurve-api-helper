"""HTTP transport policy and I/O: timeouts, connection and status retries, the per-call deadline,
`Link`-header pagination, and the send loop of one batch-write chunk.

`APIBase` (`base.py`) calls these; it keeps the client surface and the request shapes. Nothing here
imports `base` at runtime (it imports this module).
"""

from __future__ import annotations

import math
import re
import time
from collections.abc import Mapping
from typing import Any, Callable, Union
from urllib.parse import urlsplit, urlunsplit

import requests
import urllib3.exceptions
from requests import Response
from typing_extensions import TypeAlias

from ._batch import BatchChunk, ChunkSpec, _RateLimitState, _whole_chunk_failure, chunk_from_207_body

# `requests` query parameters, as `APIBase` passes them (the `params` channel; see `base._drop_params_already_in_url`).
QueryParams: TypeAlias = Mapping[str, Union[str, int, float]]

# HTTP retry policy. Two retryable conditions:
#   * 429 (Too Many Requests) -- ComboCurve's write quota is enforced by Google
#     Cloud and resets ~every 60s, so a fixed 60s pause is the safe fallback when
#     the response carries no `Retry-After` header.
#   * 502/503/504 -- transient gateway errors, retried with exponential backoff,
#     for a GET or HEAD ONLY (`_READ_ONLY_METHODS`). The gateway gives up waiting
#     while the server behind it may still apply the request, so a POST sent again
#     after a gateway status can create the records twice; a write gets the gateway
#     status back instead, and its caller must check what the server holds.
#     A 429 is retried for every method: the quota refuses the request before it runs.
_MAX_REQUEST_RETRIES = 5
_RATE_LIMIT_DEFAULT_PAUSE_SECONDS = 60.0
# Ceiling on an honoured `Retry-After`: `time.sleep` raises OverflowError near 1e10 s, which would
# abort a batch and lose the results of chunks already applied. 120 s (chosen 2026-11-05; it was
# 3600 s) so that one 429 cannot hold a caller for an hour.
_MAX_RETRY_AFTER_SECONDS = 120.0
# Wall-clock budget for ONE call (one url, one body) across every connection retry and every status
# retry, measured with `time.monotonic()` from the start of the call. Without it the status retry (6
# attempts) around the connection retry (3 sends) could send one GET 18 times: about 91 min worst
# case, so a caller with a 240 s budget was held far past it (arithmetic in
# docs/todo/closed/request-retries-have-no-overall-deadline.md). Chosen 2026-11-05. A retry whose
# pause would pass the deadline is not made. The budget is per request, not per multi-page listing:
# each page is its own call through `_request_with_retry`.
_CALL_DEADLINE_SECONDS = 600.0
_RETRYABLE_GATEWAY_STATUSES = frozenset({502, 503, 504})
_GATEWAY_BACKOFF_SECONDS = 1.0  # sleep before a gateway retry = _GATEWAY_BACKOFF_SECONDS * 2**attempt


# Connection-failure policy: a request that raised instead of returning a response.
#   * Every request carries a timeout. `requests` has none by default, so a connection that stalls
#     without a reset blocked forever and no retry could start. (connect, read) seconds; a large
#     paginated GET or a big POST can take minutes to answer.
#   * A request that was never sent (connect timeout, refused connection, DNS failure) is sent again,
#     whatever its method: the server received nothing.
#   * A GET or HEAD that failed after it was sent (reset, read timeout, truncated body) is sent again:
#     it changes nothing on the server. A POST/PUT/PATCH/DELETE that failed after it was sent is NOT:
#     the server may have applied it and only the response was lost, so a second send could write the
#     records twice. The error goes to the caller, who must check what the server holds.
_REQUEST_TIMEOUT_SECONDS = (30.0, 300.0)
_MAX_CONNECTION_RETRIES = 2
_CONNECTION_BACKOFF_SECONDS = 2.0  # sleep before a connection retry = _CONNECTION_BACKOFF_SECONDS * 2**failure
_READ_ONLY_METHODS = frozenset({'get', 'head'})


def _request_was_never_sent(error: requests.RequestException) -> bool:
    """True when `error` happened before the request reached the server: a connect timeout, or a
    connection that could not be opened (refused, DNS failure). `requests` wraps the second as a
    `ConnectionError` around urllib3's `MaxRetryError(reason=NewConnectionError)`."""
    if isinstance(error, requests.ConnectTimeout):
        return True
    if not isinstance(error, requests.ConnectionError) or not error.args:
        return False
    cause = error.args[0]
    if isinstance(cause, urllib3.exceptions.MaxRetryError):
        cause = cause.reason
    return isinstance(cause, urllib3.exceptions.NewConnectionError)


def _safe_to_send_again(method: str, error: requests.RequestException) -> bool:
    """True when the request that raised `error` can be sent again without a risk of applying it twice."""
    if _request_was_never_sent(error):
        return True
    connection_lost = isinstance(
        error, (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError)
    )
    return connection_lost and _is_read_only(method)


def _is_read_only(method: str) -> bool:
    """True when `method` cannot write, so sending it twice cannot apply anything twice."""
    return method.lower() in _READ_ONLY_METHODS


class _CallDeadlinePassed(requests.ConnectTimeout):
    """No time remained for a send. A `ConnectTimeout`, because that class says "never sent", which is
    true here, so a caller does not report a write as possibly applied."""


def _retry_fits_before_deadline(method: str, pause_seconds: float, deadline: float) -> bool:
    """True when a status retry of `method` after `pause_seconds` may start. A GET or HEAD needs the
    pause to end before `deadline`; its read timeout then shrinks to the time that remains. A write
    also needs the full read timeout to fit after the pause: a shortened timeout could turn a
    known-not-applied 429 into a lost connection, and then "the server may have applied it"."""
    if not _is_read_only(method):
        return time.monotonic() + pause_seconds + _REQUEST_TIMEOUT_SECONDS[1] <= deadline
    return time.monotonic() + pause_seconds < deadline


def _timeout_within(deadline: float) -> tuple[float, float]:
    """The (connect, read) timeout for a send that must end by `deadline` (a `time.monotonic()` time):
    `_REQUEST_TIMEOUT_SECONDS`, each part cut to the time that remains. Connect and read can each use
    the whole remainder, so one late send can run up to about twice the remainder. Raises
    `_CallDeadlinePassed` when none remains."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _CallDeadlinePassed(f'call deadline of {_CALL_DEADLINE_SECONDS:.0f} s passed before the request was sent')
    connect_seconds, read_seconds = _REQUEST_TIMEOUT_SECONDS
    return min(connect_seconds, remaining), min(read_seconds, remaining)


def _send_request(
    method: str,
    url: str,
    auth_headers: Callable[[], Mapping[str, str]],
    *,
    params: QueryParams | None = None,
    json_body: Any = None,
    deadline: float | None = None,
) -> Response:
    """Send one HTTP request with the timeout, and send it again after a connection failure when
    `_safe_to_send_again` allows it, up to `_MAX_CONNECTION_RETRIES` times. `auth_headers` is called
    for each attempt. Any other error, and the last one, is raised to the caller. A response is
    returned whatever its status: status retries are the caller's (`_retry_delay_seconds`).

    `deadline` is an absolute `time.monotonic()` time, or None for no overall limit. Each send's timeout
    is cut to the time that remains (connect and read can each use the remainder, so one late send can
    run up to about twice the remainder). A connection retry whose pause would reach the deadline is
    not made: the last error is raised. A send with no time left is not made (`requests.ConnectTimeout`)."""

    def send_once() -> Response:
        # The token fetch is inside the retried call: its connection failure is retried like this
        # request's (see auth.py). It runs first, so its time counts against the deadline.
        headers = dict(auth_headers())
        return requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=_send_timeout(deadline),
        )

    return _retry_connection_failures(method, send_once, deadline)


def _send_to_external_url(method: str, url: str, headers: Mapping[str, str], content: bytes) -> Response:
    """Send `content` as the raw body to `url` on a host that is not ComboCurve (a signed storage url),
    with only `headers`: no auth header is fetched or sent. Same timeout and connection-failure policy as
    `_send_request` (`_retry_connection_failures`): a request that never reached the server is sent
    again, a GET or HEAD is sent again after a lost connection, and a write that may have reached the
    server is not. The call has `_CALL_DEADLINE_SECONDS` from now (see `_send_request` for how a deadline
    cuts each send). No status is retried: the response is returned whatever its status."""
    call_deadline = time.monotonic() + _CALL_DEADLINE_SECONDS

    def send_once() -> Response:
        return requests.request(method, url, headers=dict(headers), data=content, timeout=_send_timeout(call_deadline))

    return _retry_connection_failures(method, send_once, call_deadline)


def _send_timeout(deadline: float | None) -> tuple[float, float]:
    """`_REQUEST_TIMEOUT_SECONDS`, or with a `deadline` the part of it that fits (`_timeout_within`)."""
    return _REQUEST_TIMEOUT_SECONDS if deadline is None else _timeout_within(deadline)


def _retry_connection_failures(method: str, send_once: Callable[[], Response], deadline: float | None) -> Response:
    """Call `send_once` and call it again after a connection failure when `_safe_to_send_again` allows
    it, up to `_MAX_CONNECTION_RETRIES` times, pausing `_CONNECTION_BACKOFF_SECONDS * 2**failure`
    between. Any other error, and the last one, is raised. A retry whose pause would reach `deadline`
    is not made, and `_CallDeadlinePassed` is never retried. The policy of `_send_request` and
    `_send_to_external_url`."""
    for failure in range(_MAX_CONNECTION_RETRIES + 1):
        try:
            return send_once()
        except _CallDeadlinePassed:
            raise  # a refusal is final: it is a ConnectTimeout, which the branch below would retry
        except requests.RequestException as error:
            if failure == _MAX_CONNECTION_RETRIES or not _safe_to_send_again(method, error):
                raise
            pause_seconds = _CONNECTION_BACKOFF_SECONDS * (2.0**failure)
            if deadline is not None and time.monotonic() + pause_seconds >= deadline:
                raise
            time.sleep(pause_seconds)
    raise RuntimeError('unreachable: the loop returns or raises on the final attempt')


def _retry_after_seconds(response: Response) -> float | None:
    """Return the `Retry-After` header as seconds if present in delta-seconds form.

    The HTTP-date form is not parsed here; callers fall back to the default pause. A value that
    is negative or not finite (`-1`, `nan`, `inf`) is treated the same way: `time.sleep` raises on it.
    A value above `_MAX_RETRY_AFTER_SECONDS` is capped to it.
    """
    value = response.headers.get('Retry-After')
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    if not math.isfinite(seconds) or seconds < 0:
        return None
    return min(seconds, _MAX_RETRY_AFTER_SECONDS)


def _retry_delay_seconds(response: Response, attempt: int, method: str) -> float | None:
    """Seconds to wait before retrying the `method` request that got `response`, or None if it is not
    retryable.

    Retryable: HTTP 429 for every method (wait `Retry-After` or the default quota pause), and the
    transient gateway errors 502/503/504 for a GET or HEAD only (exponential backoff; see the policy
    comment above). Any other status, and a gateway status on a write, returns None for the caller.
    """
    status = response.status_code
    if status == 429:
        retry_after = _retry_after_seconds(response)
        # `is None`, not `or`: `Retry-After: 0` is a valid "retry now", not a missing header.
        return _RATE_LIMIT_DEFAULT_PAUSE_SECONDS if retry_after is None else retry_after
    if _gateway_retry_allowed(status, method):
        return _GATEWAY_BACKOFF_SECONDS * (2.0**attempt)
    return None


def _gateway_retry_allowed(status: int, method: str) -> bool:
    """True when `status` is a transient gateway error and `method` cannot write twice."""
    return status in _RETRYABLE_GATEWAY_STATUSES and _is_read_only(method)


def _send_with_status_retries(
    method: str,
    url: str,
    auth_headers: Callable[[], Mapping[str, str]],
    *,
    params: QueryParams | None = None,
    json_body: Any = None,
) -> Response:
    """Send one request through `_send_request` and retry the statuses `_retry_delay_seconds` allows, up to
    `_MAX_REQUEST_RETRIES` retries, within `_CALL_DEADLINE_SECONDS` counted from this call. The last response
    is returned whatever its status; a retry that does not fit the deadline is not made."""
    deadline = time.monotonic() + _CALL_DEADLINE_SECONDS
    for attempt in range(_MAX_REQUEST_RETRIES + 1):
        response = _send_request(method, url, auth_headers, params=params, json_body=json_body, deadline=deadline)
        delay = _retry_delay_seconds(response, attempt, method)
        if delay is None or attempt == _MAX_REQUEST_RETRIES:
            return response
        if not _retry_fits_before_deadline(method, delay, deadline):
            return response  # the caller reports this status
        time.sleep(delay)
    raise RuntimeError('unreachable: retry loop always returns')


def _chunk_failure_after_connection_error(
    chunk_spec: ChunkSpec, method: str, error: requests.RequestException, last_status: int | None
) -> BatchChunk:
    """The whole-chunk failure for a chunk whose send raised `error`. `last_status` is the status of
    the chunk's previous attempt, or None on the first."""
    if isinstance(error, _CallDeadlinePassed) and last_status is not None:
        # A shared 429 pause of another worker used the time left: report the status
        # this chunk last got, not a connection failure.
        return _whole_chunk_failure(
            chunk_spec,
            http_status=last_status,
            error_message=f'call deadline passed after status {last_status}: {error}',
            may_have_applied=last_status in _RETRYABLE_GATEWAY_STATUSES and not _is_read_only(method),
        )
    never_sent = _request_was_never_sent(error)
    may_have_applied = not _is_read_only(method) and not never_sent
    if may_have_applied:
        outcome = 'the server may have applied this chunk'
    elif never_sent:
        outcome = 'the chunk was not sent'
    else:
        outcome = 'a read-only request changes nothing on the server'
    return _whole_chunk_failure(
        chunk_spec,
        http_status=0,  # no response was received
        error_message=f'connection failed ({type(error).__name__}): {outcome}; {error}',
        may_have_applied=may_have_applied,
    )


def _chunk_failure_from_status(chunk_spec: ChunkSpec, method: str, response: Response) -> BatchChunk:
    """The whole-chunk failure for a chunk whose last response has a 4xx/5xx status."""
    status = response.status_code
    try:
        detail: Any = response.json()
    except ValueError:
        detail = response.text
    error_message = str(detail)
    may_have_applied = status in _RETRYABLE_GATEWAY_STATUSES and not _is_read_only(method)
    if may_have_applied:
        error_message = f'gateway status {status}: the server may have applied this chunk; {error_message}'
    return _whole_chunk_failure(
        chunk_spec,
        http_status=status,
        error_message=error_message,
        may_have_applied=may_have_applied,
    )


def _send_batch_chunk(
    method: str,
    url: str,
    auth_headers: Callable[[], Mapping[str, str]],
    chunk_spec: ChunkSpec,
    rate_limit: _RateLimitState,
) -> BatchChunk:
    """Send one batch chunk with transient-failure retries; parse its 207 body.

    Runs on a worker thread. `auth_headers` is called for every attempt, so a batch that outlives its
    token (a 429 pause is 60 s) sends a refreshed one. A 429 pauses every worker via `rate_limit` (for
    the response's `Retry-After` when present) and retries up to `_MAX_REQUEST_RETRIES`. A gateway
    error (502/503/504) is retried only for a read-only method, which a batch write never is. Any other
    4xx/5xx, and a 429 that survives all retries, is recorded as a whole-chunk failure.

    A write that got a gateway status, or whose connection was lost after it was sent, is recorded as a
    whole-chunk failure with `may_have_applied=True`: the server may have applied it. A connection
    failure does not raise out of the batch, so the other chunks' results still reach the caller.

    The whole chunk has `_CALL_DEADLINE_SECONDS`, counted from this call, across every status and
    connection retry. A pause that would reach the deadline is not taken: the last status is recorded
    as the chunk failure.
    """
    deadline = time.monotonic() + _CALL_DEADLINE_SECONDS
    last_status: int | None = None
    for attempt in range(_MAX_REQUEST_RETRIES + 1):
        rate_limit.wait_if_limited()
        try:
            response = _send_request(method, url, auth_headers, json_body=chunk_spec.records, deadline=deadline)
        except requests.RequestException as error:
            return _chunk_failure_after_connection_error(chunk_spec, method, error, last_status)
        status = response.status_code
        last_status = status

        if attempt < _MAX_REQUEST_RETRIES:
            # A retry that does not fit the deadline is not made: the status is recorded below.
            if status == 429:
                retry_after = _retry_after_seconds(response)
                pause_seconds = rate_limit.pause_seconds if retry_after is None else retry_after
                if _retry_fits_before_deadline(method, pause_seconds, deadline):
                    rate_limit.set_limited(retry_after)
                    continue
            elif _gateway_retry_allowed(status, method):
                pause_seconds = _GATEWAY_BACKOFF_SECONDS * (2.0**attempt)
                if _retry_fits_before_deadline(method, pause_seconds, deadline):
                    time.sleep(pause_seconds)
                    continue

        if status >= 400:
            return _chunk_failure_from_status(chunk_spec, method, response)

        try:
            body: Any = response.json()
        except ValueError:
            body = None
        return chunk_from_207_body(chunk_spec, status, body)

    raise RuntimeError('unreachable: retry loop always returns on the final attempt')


# One `<url>` and the parameters after it, up to the next `<`. URLs cannot hold `<` or `>`.
_LINK_HEADER_ENTRY = re.compile(r'<([^<>]*)>([^<]*)')


def get_next_page_url(response_headers: Mapping[str, str]) -> str | None:
    """The `rel="next"` url of the `Link` header (RFC 8288), or None on the last page.

    Replaces `combocurve_api_v1.pagination.get_next_page_url`, whose pattern required `;rel=` with no
    space: `; rel="next"`, legal in the RFC, matched nothing and ended pagination with no error. This
    accepts optional whitespace, an unquoted value, and a space-separated list of relation types.
    """
    for url, parameters in _LINK_HEADER_ENTRY.findall(response_headers.get('Link', '')):
        for parameter in parameters.split(';'):
            name, _, value = parameter.partition('=')
            relation_types = value.strip().rstrip(',').strip().strip('"').split()
            if name.strip().lower() == 'rel' and 'next' in relation_types:
                return str(url)
    return None


def _next_page_url_on_request_origin(response_headers: Mapping[str, str], request_url: str) -> str | None:
    """The next-page url with the scheme and host of `request_url`; only its path and query come from
    the `Link` header.

    The OAuth (v2) backend writes its internal Cloud Run host into `Link`
    (`https://external-api-<n>.us-central1.run.app/v1/...`, verified 2026-10-27), not
    `api.combocurve.com`. Following it as given answers 401, and it sends the bearer token and API key to
    a host taken from a response header. The same path and query on the request's own host answer 200.
    """
    next_page_url = get_next_page_url(response_headers)
    if next_page_url is None:
        return None
    request_parts = urlsplit(request_url)
    link_parts = urlsplit(next_page_url)
    return urlunsplit((request_parts.scheme, request_parts.netloc, link_parts.path, link_parts.query, ''))
