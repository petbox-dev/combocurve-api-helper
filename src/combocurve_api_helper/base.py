import time
import warnings
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Optional, Union
from urllib.parse import parse_qsl, quote, urlencode, urlsplit

import requests
from combocurve_api_v1 import ComboCurveAuth, ServiceAccount
from combocurve_api_v1.pagination import get_next_page_url
from more_itertools import chunked
from requests import Response
from typing_extensions import Self, TypeAlias, TypedDict

from . import config
from ._batch import BatchChunk, BatchWriteResult, _RateLimitState

# A single JSON value: the recursive union of everything `json.loads` can yield.
# Models real API payloads faithfully -- `null` (None), arrays of objects, and
# nested objects are all representable, which the former `PrimativeValue` /
# `IterableValue` split could not express (it allowed lists of scalars only, and
# no nulls). The container arms are the COVARIANT `Sequence` / `Mapping`, not
# `list` / `dict`: because `list`/`dict` are invariant, a concrete `list[str]` or
# `list[dict[...]]` (e.g. a payload built by a caller, or a `list[str]` variable
# assigned into an item) is NOT a `list[JsonValue]` and would fail to type-check;
# `Sequence`/`Mapping` accept them. Self-references are quoted forward refs; mypy
# resolves the recursive alias.
JsonValue: TypeAlias = Union[str, int, float, bool, Sequence['JsonValue'], Mapping[str, 'JsonValue'], None]

# One API object (a JSON object) and a list of them -- the shapes every endpoint
# method takes and returns. These stay the mutable, invariant `dict`/`list` (we
# build, extend, and index them internally); only the nested value arms above are
# the read-covariant `Sequence`/`Mapping`. Responses stay plain dicts, not custom
# model classes.
Item: TypeAlias = dict[str, JsonValue]
ItemList: TypeAlias = list[Item]

# The comparison orders `_keysort` is called with. Single-sourced here because the
# same mapping was previously spelled out at a dozen call sites across six modules
# with nothing keeping them in sync, and `_keysort`'s correctness argument depends
# on the exact positions (see `sort_by_key`).
#
# Wrapped in MappingProxyType, not merely annotated `Mapping`: an annotation is not a
# runtime guard, and these are now shared by 23 call sites across 7 modules, so one
# stray `SORT_ORDER['name'] = x` would corrupt every list endpoint at once. The proxy
# raises TypeError instead.
#
# Positions read: name/wellName first, then updatedAt, createdAt, and id last.
LIST_SORT_ORDER: Mapping[str, int] = MappingProxyType({'name': 0, 'id': 3, 'createdAt': 2, 'updatedAt': 1})

# Same shape, for the well endpoints whose display name field is `wellName`.
WELL_LIST_SORT_ORDER: Mapping[str, int] = MappingProxyType({'wellName': 0, 'id': 3, 'createdAt': 2, 'updatedAt': 1})


class WriteError(TypedDict, total=False):
    """One entry in a write response's `generalErrors` list."""

    name: str
    message: str
    location: str


class WriteResponse(TypedDict):
    """The 207 envelope every create/update endpoint (POST/PUT/PATCH) returns.

    `_post_items` / `_put_items` / `_patch_items` yield one of these per request
    chunk, so a write method returns `list[WriteResponse]` (usually one element).

    `results` stays the generic `Item`: the per-record shape varies by resource
    (its id key is `id`, `forecastId`, `wellId`, ...; productions add `date`/`well`,
    wells add `chosenID`/`dataSource`, etc.), so no single TypedDict fits it and a
    generic dict avoids forcing casts to read a resource's own id/fields.
    """

    successCount: int
    failedCount: int
    results: ItemList
    generalErrors: list[WriteError]


# HTTP retry policy. Two retryable conditions:
#   * 429 (Too Many Requests) -- ComboCurve's write quota is enforced by Google
#     Cloud and resets ~every 60s, so a fixed 60s pause is the safe fallback when
#     the response carries no `Retry-After` header.
#   * 502/503/504 -- transient gateway errors, retried with exponential backoff.
#     This mirrors the retry strategy consumers previously applied at the session
#     level (e.g. VDR's make_session), so nothing is lost by routing requests
#     through the helper.
_MAX_REQUEST_RETRIES = 5
_RATE_LIMIT_DEFAULT_PAUSE_SECONDS = 60.0
_RETRYABLE_GATEWAY_STATUSES = frozenset({502, 503, 504})
_GATEWAY_BACKOFF_SECONDS = 1.0  # sleep before a gateway retry = _GATEWAY_BACKOFF_SECONDS * 2**attempt


def _retry_after_seconds(response: Response) -> Optional[float]:
    """Return the `Retry-After` header as seconds if present in delta-seconds form.

    The HTTP-date form is not parsed here; callers fall back to the default pause.
    """
    value = response.headers.get('Retry-After')
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _drop_params_already_in_url(
    url: str, params: Optional[Mapping[str, Union[str, int, float]]]
) -> Optional[Mapping[str, Union[str, int, float]]]:
    """Strip keys from `params` that the `url` already carries in its query string.

    Query parameters reach a request through two independent channels: the `filters`
    a caller hands a `*_url(...)` builder, which `_build_params_string` bakes into the
    url, and the `params` mapping the api method supplies (in practice `take`, plus
    `concurrency` on the econ-run monthly-export routes). `requests` APPENDS `params`
    to an existing query rather
    than merging, so a caller-supplied `take` produced `?take=50&take=200` and the API
    rejected the pair outright (`TypeError: `50,200` is not a valid number`) instead of
    honouring either value.

    The url wins, so an explicit filter overrides the method's default page size.
    """
    if not params:
        return params

    # `keep_blank_values` is load-bearing: without it a valueless `?take=` would not
    # register as present and the duplicate-key bug returns for that spelling.
    existing = {key for key, _ in parse_qsl(urlsplit(url).query, keep_blank_values=True)}

    return {key: value for key, value in params.items() if key not in existing}


def _retry_delay_seconds(response: Response, attempt: int) -> Optional[float]:
    """Seconds to wait before retrying `response`, or None if it is not retryable.

    Retryable: HTTP 429 (wait `Retry-After` or the default quota pause) and
    transient gateway errors 502/503/504 (exponential backoff). Any other status
    (2xx success, other 4xx/5xx) returns None for the caller to handle.
    """
    status = response.status_code
    if status == 429:
        return _retry_after_seconds(response) or _RATE_LIMIT_DEFAULT_PAUSE_SECONDS
    if status in _RETRYABLE_GATEWAY_STATUSES:
        return _GATEWAY_BACKOFF_SECONDS * (2.0**attempt)
    return None


class APIBase:
    API_BASE_URL = 'https://api.combocurve.com/v1'
    API_BASE_URL_V2 = 'https://api.combocurve.com/v2'  # async export routes are the only /v2 routes
    REFERENCE_WELLHEADER = config.REFERENCE_WELLHEADER
    WELLHEADER_COLUMNS: ClassVar[dict[str, str]] = {k.lower(): k for k in config.REFERENCE_WELLHEADER}
    ECON_MODELS = config.ECON_MODELS

    def __init__(self) -> None:
        account = ServiceAccount.from_file(str(config.COMBOCURVE_JSON))
        self.auth = ComboCurveAuth(account, config.cfg.apikey)

    @classmethod
    def from_alternate_config(
        cls, combocurve_json_path: Union[str, Path], cc_api_config_json_path: Union[str, Path]
    ) -> Self:
        api_base = cls.__new__(cls)
        super(APIBase, api_base).__init__()

        cfg = config.Configuration.from_file(cc_api_config_json_path)

        if isinstance(combocurve_json_path, str):
            account = ServiceAccount.from_file(combocurve_json_path)
        elif isinstance(combocurve_json_path, Path):
            account = ServiceAccount.from_file(combocurve_json_path.absolute())

        api_base.auth = ComboCurveAuth(account, cfg.apikey)

        return api_base

    def _extract_json(self, response: requests.Response) -> ItemList:
        """
        Ensure returned JSON is a list of objects
        """
        json_ = response.json()
        if isinstance(json_, dict):
            json_ = [json_]
        elif not isinstance(json_, list):
            json_ = list(json_)

        return json_

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Union[str, int, float]]] = None,
        json_body: Any = None,
    ) -> Response:
        """Issue a single HTTP request, refreshing auth headers each attempt and
        retrying transient failures.

        Retries HTTP 429 (waiting `Retry-After` or the default quota pause) and
        transient gateway errors 502/503/504 (exponential backoff), for up to
        `_MAX_REQUEST_RETRIES` retries. Any other response (success or a
        non-transient error) is returned immediately for the caller to handle
        (e.g. `raise_for_status`).

        Every verb funnels through here EXCEPT the batched-write path (`_send_one_chunk`
        calls `requests.request` directly and carries its own retry loop), so this is
        also where `params` is reconciled against a query string already present on
        `url` -- see `_drop_params_already_in_url`. The batch path passes no `params`,
        so it has nothing to reconcile today; a future change that adds one there would
        NOT be covered by this.
        """
        params = _drop_params_already_in_url(url, params)
        for attempt in range(_MAX_REQUEST_RETRIES + 1):
            headers = self.auth.get_auth_headers()
            response = requests.request(method, url, headers=headers, params=params, json=json_body)
            delay = _retry_delay_seconds(response, attempt)
            if delay is None or attempt == _MAX_REQUEST_RETRIES:
                return response
            time.sleep(delay)
        raise RuntimeError('unreachable: retry loop always returns')

    def _request_items_pages(
        self, method: str, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None
    ) -> Iterator[Response]:
        """
        Generic method for dispatching GET requests for the given `url` yielding
        response of each page
        """
        # keep fetching while there are more records to be returned
        while True:
            response = self._request_with_retry(method, url, params=params)
            try:
                response.raise_for_status()
            except Exception as e:
                print(f'\nException occured during request:\nURL: {url}\nParams: {params}\n')
                raise e

            yield response

            next_page_url: Optional[str] = get_next_page_url(response.headers)
            if next_page_url is None:
                # no more pages to process
                break
            else:
                url = next_page_url

            params = None

    def _request_items_pages_chunks(
        self,
        method: str,
        url: str,
        data: ItemList,
        chunksize: Optional[int] = None,
        params: Optional[Mapping[str, Union[str, int, float]]] = None,
    ) -> Iterator[Response]:
        """
        Generic method for dispatching POST/PATCH/PUT requests for the given
        `url` yielding response of each page
        """
        if chunksize is None:
            chunksize = len(data)

        if chunksize == 0:
            yield from self._request_items_pages(method, url, params=params)
            return

        for chunk in chunked(data, chunksize):
            # Page-following rebinds a LOCAL copy: `url` itself must survive the chunk
            # loop unchanged, or chunk N+1 posts to chunk N's next-page url -- which
            # already carries that page's `skip`/`take`. That leak used to surface as a
            # duplicate `take` the API rejected outright; `_drop_params_already_in_url`
            # would now reconcile it silently, so the wrong-url write has to be
            # prevented here rather than caught downstream.
            chunk_url = url
            params_ = params
            while True:
                response = self._request_with_retry(method, chunk_url, params=params_, json_body=chunk)
                try:
                    response.raise_for_status()
                except Exception as e:
                    print(f'\nException occured during request:\nURL: {chunk_url}\n')
                    raise e

                yield response

                next_page_url: Optional[str] = get_next_page_url(response.headers)
                if next_page_url is None:
                    # no more pages to process
                    break
                else:
                    chunk_url = next_page_url

                params_ = None

    def _send_one_chunk(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        index: int,
        offset: int,
        chunk: ItemList,
        rate_limit: _RateLimitState,
    ) -> BatchChunk:
        """Send one batch chunk with transient-failure retries; parse its 207 body.

        Runs on a worker thread and uses pre-fetched `headers` (shared across
        workers) rather than re-authenticating per request. A 429 pauses every
        worker via `rate_limit`; transient gateway errors (502/503/504) back off
        and retry just this chunk. Both retry up to `_MAX_REQUEST_RETRIES`; any
        other 4xx/5xx (and a transient status that survives all retries) is
        recorded as a whole-chunk failure.
        """
        count = len(chunk)
        for attempt in range(_MAX_REQUEST_RETRIES + 1):
            rate_limit.wait_if_limited()
            response = requests.request(method, url, headers=dict(headers), json=chunk)
            status = response.status_code

            if attempt < _MAX_REQUEST_RETRIES:
                if status == 429:
                    rate_limit.set_limited()
                    continue
                if status in _RETRYABLE_GATEWAY_STATUSES:
                    time.sleep(_GATEWAY_BACKOFF_SECONDS * (2.0**attempt))
                    continue

            if status >= 400:
                try:
                    detail: Any = response.json()
                except ValueError:
                    detail = response.text
                return BatchChunk(
                    index=index,
                    offset=offset,
                    count=count,
                    http_status=status,
                    failed_count=count,
                    error_message=str(detail),
                )

            try:
                body: Any = response.json()
            except ValueError:
                body = {}
            if not isinstance(body, dict):
                body = {}
            results_raw = body.get('results') or []
            general_raw = body.get('generalErrors') or []
            return BatchChunk(
                index=index,
                offset=offset,
                count=count,
                http_status=status,
                success_count=int(body.get('successCount', 0) or 0),
                failed_count=int(body.get('failedCount', 0) or 0),
                results=[r for r in results_raw if isinstance(r, dict)],
                general_errors=[e for e in general_raw if isinstance(e, dict)],
            )

        raise RuntimeError('unreachable: retry loop always returns on the final attempt')

    def _request_batched(
        self,
        method: str,
        url: str,
        data: ItemList,
        *,
        chunksize: int,
        max_workers: int = 10,
        on_progress: Optional[Callable[[BatchChunk], None]] = None,
    ) -> BatchWriteResult:
        """Send `data` to `url` in parallel chunks, returning the stitched 207 envelope.

        Each chunk is one `method` request of up to `chunksize` records, sent
        across a `max_workers` thread pool with coordinated 429 backoff. Unlike
        `_post_items` / `_put_items` (which flatten to `ItemList`), this preserves
        per-record success/failure: ``BatchWriteResult.results[i]`` corresponds to
        ``data[i]`` (results are stitched back into input order across chunks).
        ``on_progress``, if given, is invoked once per completed chunk from the
        calling thread.

        Auth headers are fetched once up front and shared across workers (avoids
        concurrent token refreshes); a batch is expected to finish well within a
        token's lifetime.
        """
        chunk_specs: list[tuple[int, int, ItemList]] = []
        offset = 0
        for index, chunk in enumerate(chunked(data, chunksize)):
            chunk_list: ItemList = list(chunk)
            chunk_specs.append((index, offset, chunk_list))
            offset += len(chunk_list)

        headers = self.auth.get_auth_headers()
        rate_limit = _RateLimitState(pause_seconds=_RATE_LIMIT_DEFAULT_PAUSE_SECONDS)
        completed: list[BatchChunk] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._send_one_chunk, method, url, headers, index, off, chunk_list, rate_limit)
                for index, off, chunk_list in chunk_specs
            ]
            for future in as_completed(futures):
                chunk_result = future.result()
                completed.append(chunk_result)
                if on_progress is not None:
                    on_progress(chunk_result)

        completed.sort(key=lambda c: c.index)

        results: ItemList = []
        general_errors: ItemList = []
        success_count = 0
        failed_count = 0
        for chunk_result in completed:
            results.extend(chunk_result.results)
            general_errors.extend(chunk_result.general_errors)
            success_count += chunk_result.success_count
            failed_count += chunk_result.failed_count

        return BatchWriteResult(
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            general_errors=general_errors,
            chunks=completed,
        )

    def _get_responses_iterator(
        self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None
    ) -> Iterator[Response]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages('get', url, params)

    def _get_responses(self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> list[Response]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages('get', url, params))

    def _get_items_iterator(
        self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None
    ) -> Iterator[ItemList]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages('get', url, params):
            yield self._extract_json(response)

    def _get_items(self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> ItemList:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages('get', url, params):
            items.extend(self._extract_json(response))

        return items

    def _post_responses_iterator(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[Response]:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('post', url, data, chunksize)

    def _post_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> list[Response]:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('post', url, data, chunksize))

    def _post_items_iterator(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('post', url, data, chunksize):
            yield self._extract_json(response)

    def _post_items(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('post', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items

    def _patch_responses_iterator(
        self, url: str, data: ItemList, chunksize: Optional[int] = None
    ) -> Iterator[Response]:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('patch', url, data, chunksize)

    def _patch_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> list[Response]:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('patch', url, data, chunksize))

    def _patch_items_iterator(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('patch', url, data, chunksize):
            yield self._extract_json(response)

    def _patch_items(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('patch', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items

    def _put_responses_iterator(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[Response]:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('put', url, data, chunksize)

    def _put_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> list[Response]:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('put', url, data, chunksize))

    def _put_items_iterator(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('put', url, data, chunksize):
            yield self._extract_json(response)

    def _put_items(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('put', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items

    def _delete_responses_iterator(
        self, url: str, data: ItemList, chunksize: Optional[int] = None
    ) -> Iterator[Response]:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('delete', url, data, chunksize)

    def _delete_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> list[Response]:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('delete', url, data, chunksize))

    def _delete_items_iterator(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('delete', url, data, chunksize):
            yield self._extract_json(response)

    def _delete_items(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('delete', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items

    @staticmethod
    def _require_any_filter(filters: Mapping[str, Optional[str]], parameters: str) -> dict[str, str]:
        """Return the non-empty entries of `filters`, or raise if none survive.

        Shared by every delete the API refuses to run unfiltered -- company/project/
        project-company wells, scenarios, type curves. The same guard-then-build block
        was inlined at each of those sites in two spellings, and both let an empty
        string through: `chosen_id=''` from an unresolved lookup, paired with a real
        `data_source`, sent `?chosenID=&dataSource=...` and deleted on a filter the
        caller never meant. Empty values are dropped here rather than forwarded.

        `filters` is keyed by API query name; `parameters` names the caller-facing
        keyword arguments for the error message, because the two differ (`well_id` is
        the parameter, `id` is the query key).

        Distinct from `production._delete_filters`, which is NOT this shape: that
        endpoint requires one SPECIFIC filter (`well`) rather than any one of several,
        and additionally type-checks it. Don't unify them.
        """
        present = {key: value for key, value in filters.items() if value}
        if not present:
            raise ValueError(f'Must provide at least one of {parameters}')

        return present

    @staticmethod
    def _build_params_string(filters: Optional[Mapping[str, Optional[str]]] = None) -> str:
        """Render `filters` as a query string, or `''` when there is nothing to send.

        `None` values are DROPPED rather than rendered, matching how `requests` treats a
        `None` in `params`. The previous f-string interpolation emitted the literal text
        `None` (`?take=None`), which the API rejects on any numeric field.

        Values are percent-encoded, so a filter carrying `&`, `=`, `#`, a space or a
        non-ASCII character (a project or well name, say) no longer corrupts the query.

        `,` is deliberately left LITERAL via `safe`, and `quote` is used instead of the
        `urlencode` default `quote_plus` so a space encodes as `%20` rather than `+`.
        Three internal callers join list filters on commas -- `econ_runs` `columns`,
        `_econ_model_base` `wells`, `scenarios` `econNames`/`qualifierNames` -- and each
        of those wire formats was verified live against the API in its unencoded form.
        Encoding the separator would change a request that is known to work into one
        that is not, for no benefit: `,` and `+` are legal unencoded query characters
        (RFC 3986 sub-delims), so they were never the corruption this fix targets.
        """
        pairs = [(key, value) for key, value in (filters or {}).items() if value is not None]

        return '?' + urlencode(pairs, safe=',', quote_via=quote) if pairs else ''

    @staticmethod
    def _keysort(items: ItemList, order: Mapping[str, int], reverse: bool = False) -> ItemList:
        """
        Return an iterable of dictionaries where each dictionary has
        its keys sorted by the given `order`. The `order` is a mapping
        that defines the key => integer index to order by.

        `order` positions must be non-negative, distinct, non-`bool` integers; gaps are
        allowed and sort as empty strings. Validated once here rather than per item,
        because a negative position would index from the end of the key and silently
        drop another key's value, and a duplicate would silently discard one of the
        two. `bool` and other `int` subclasses are rejected rather than coerced, so a
        stray `True` cannot tie with position 1.
        """
        # `bool` is an `int` subclass and `True == 1`, so a bool position would slip through
        # the distinctness check by comparing equal to a real position. Excluded by name
        # rather than via `type(...) is int`, which would also reject `IntEnum` and
        # `numpy.int64` -- both genuine ints that satisfy the `Mapping[str, int]` annotation.
        non_integer = sorted(
            key for key, position in order.items() if not isinstance(position, int) or isinstance(position, bool)
        )
        if non_integer:
            raise ValueError(f'`order` positions must be non-bool ints; got other types for {non_integer}')

        negative = sorted(key for key, position in order.items() if position < 0)
        if negative:
            raise ValueError(f'`order` positions must be non-negative; got negative for {negative}')

        duplicated = sorted({position for position in order.values() if list(order.values()).count(position) > 1})
        if duplicated:
            raise ValueError(f'`order` positions must be distinct; positions {duplicated} are reused')

        # A constant of `order`, so computed once rather than per item.
        key_width = max(order.values(), default=-1) + 1

        def sort_by_key(item: Item) -> list[str]:
            """
            Build one item's comparison key: each ordering value placed at the
            position `order` assigns it, stringified so the keys are comparable.

            Assembled by WRITING to `order[key]`. Reading `values[order[key]]`
            instead applies the inverse permutation, and the two agree only when
            `order` composed with the item's own key sequence is self-inverse --
            a property of the payload, not of `order` alone. ComboCurve does NOT
            serialize keys uniformly -- projects/scenarios/forecasts lead with
            `createdAt` (self-inverse), while econ models, type curves and wells
            lead with `id` and econ runs arrive `id, runDate, status`. Those were
            therefore sorted by `updatedAt` / `status` instead of the declared key.
            """
            sortable_by_position: list[str] = [''] * key_width

            for key, position in order.items():
                if key not in item:
                    # Absent ordering key: record it on the item, which callers have always
                    # seen padded in. (`item.setdefault(key, None)` would work equally well
                    # here; what must NOT happen is binding its RETURN value -- typeshed
                    # collapses that to `None` for a value type that already admits None,
                    # which makes the branches below unreachable under warn_unreachable.)
                    item[key] = None

                value = item[key]
                if value is None:
                    sortable_by_position[position] = ''

                elif not isinstance(value, str):
                    sortable_by_position[position] = str(value)

                else:
                    sortable_by_position[position] = value

            return sortable_by_position

        return list(sorted(items, key=sort_by_key, reverse=reverse))

    @staticmethod
    def extract_id(
        items: Union[Item, ItemList], name: str, name_key: str = 'name', id_key: str = 'id'
    ) -> Optional[str]:
        id_: Optional[str] = None

        if not isinstance(items, (dict, list)):
            # Statically unreachable given the annotation, kept as a runtime guard
            # for untyped callers.
            warnings.warn(  # type: ignore[unreachable]
                f'Expected items to be a dict or list, got {type(items)}', RuntimeWarning, stacklevel=2
            )
            return

        elif isinstance(items, dict):
            id_ = str(items.get(id_key))

        elif isinstance(items, list):
            # iterate over the list of dict until name is found, and extract id
            for item in items:
                if item.get(name_key) == name:
                    id_ = str(item.get(id_key))
                    break

        if id_ is None:
            warnings.warn(f'Could not find `id` for {name}', UserWarning, stacklevel=2)
        return id_

    @staticmethod
    def index_of(items: ItemList, value: str, key: str = 'id') -> Union[int, None]:
        if not isinstance(items, list):
            # Statically unreachable given the annotation, kept as a runtime guard
            # for untyped callers.
            warnings.warn(  # type: ignore[unreachable]
                f'Expected items to be a list, got {type(items)}', RuntimeWarning, stacklevel=2
            )
            return

        # iterate over the list of dict until value is found, return index
        key_exists = False
        for i, item in enumerate(items):
            if key in item:
                key_exists = True

                if item[key] == value:
                    return i

        if not key_exists:
            warnings.warn(f'Key `{key}` does not exist in items', UserWarning, stacklevel=2)
        else:
            warnings.warn(f'Could not find {value} for {key}', UserWarning, stacklevel=2)

        return None
