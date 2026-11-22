import threading
import time
import warnings
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Optional, Union, cast
from urllib.parse import parse_qsl, quote, urlencode, urlsplit

import requests
from more_itertools import chunked
from requests import Response
from requests.structures import CaseInsensitiveDict
from typing_extensions import Self, TypeAlias, TypedDict

from . import config
from ._batch import BatchChunk, BatchWriteResult, ChunkSpec, _RateLimitState
from ._deprecation import warn_deprecated

# The transport policy and I/O (timeouts, connection and status retries, the call deadline, `Link`
# pagination, the batch-chunk send loop) live in `_transport`. These names are re-exported because tests
# and callers import them from `base`.
from ._transport import _CALL_DEADLINE_SECONDS as _CALL_DEADLINE_SECONDS
from ._transport import _CONNECTION_BACKOFF_SECONDS as _CONNECTION_BACKOFF_SECONDS
from ._transport import _GATEWAY_BACKOFF_SECONDS as _GATEWAY_BACKOFF_SECONDS
from ._transport import _MAX_CONNECTION_RETRIES as _MAX_CONNECTION_RETRIES
from ._transport import _MAX_REQUEST_RETRIES as _MAX_REQUEST_RETRIES
from ._transport import _MAX_RETRY_AFTER_SECONDS as _MAX_RETRY_AFTER_SECONDS
from ._transport import _RATE_LIMIT_DEFAULT_PAUSE_SECONDS as _RATE_LIMIT_DEFAULT_PAUSE_SECONDS
from ._transport import _READ_ONLY_METHODS as _READ_ONLY_METHODS
from ._transport import _REQUEST_TIMEOUT_SECONDS as _REQUEST_TIMEOUT_SECONDS
from ._transport import _RETRYABLE_GATEWAY_STATUSES as _RETRYABLE_GATEWAY_STATUSES
from ._transport import _CallDeadlinePassed as _CallDeadlinePassed
from ._transport import _gateway_retry_allowed as _gateway_retry_allowed
from ._transport import _is_read_only as _is_read_only
from ._transport import _next_page_url_on_request_origin as _next_page_url_on_request_origin
from ._transport import _request_was_never_sent as _request_was_never_sent
from ._transport import _retry_after_seconds as _retry_after_seconds
from ._transport import _retry_delay_seconds as _retry_delay_seconds
from ._transport import _retry_fits_before_deadline as _retry_fits_before_deadline
from ._transport import _safe_to_send_again as _safe_to_send_again
from ._transport import _send_batch_chunk, _send_with_status_retries
from ._transport import _send_request as _send_request
from ._transport import _timeout_within as _timeout_within
from ._transport import get_next_page_url as get_next_page_url
from .auth import APIAuth, auth_from_credentials_directory, auth_from_credentials_file, default_auth

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

# The query filters `_build_params_string` renders and the `*_url` builders take. A value is one string, an
# int (`take`, `skip`; rendered with `str`, so a `bool` would arrive as `True`: pass `'true'`), a sequence of
# strings (the key is repeated once per element, `?well=a&well=b`, for the routes that take several values
# of one key), or `None` (the key is left out). Spelled with `Union`/`Optional` because a `TypeAlias`
# right-hand side is evaluated at runtime on Python 3.9.
QueryFilters: TypeAlias = Mapping[str, Union[str, int, Sequence[str], None]]

# The name the repeated-`well` builders used before `QueryFilters` (2026-11-20); kept as an alias of it
# because it is importable from this public module.
WellFilters: TypeAlias = QueryFilters

# The most repeated `well` (or `wellId`) values one request takes on the production, forecast-output and
# scenario model-assignment routes. Verified live 2026-11-20 on dev: 100 accepted, 101 refused with a 400.
# The `wells` filter of the scenario well-assignments DELETE and the econ-model unassign DELETE has the same
# limit (verified live 2026-11-21 on dev: 100 -> 204, 101 -> 400 `RequestStructureError`
# "`[object Object]` is not a valid ObjectId", 500 -> 431 at a 15.6k-character url).
WELL_FILTER_LIMIT = 100

# A job in one of these statuses has not finished (`APIBase._wait_for_job`). Seen live: shapefile and
# formations jobs go `pending` -> `running` -> `successful` (2026-11-21 and 2026-11-22).
RUNNING_JOB_STATUSES = frozenset({'pending', 'running'})

# Paging filters that a request split by `_filter_value_batches` cannot honour: each batch request would
# apply them on its own.
_PAGING_FILTER_KEYS = ('skip', 'cursor')

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


class APIBase:
    API_BASE_URL = 'https://api.combocurve.com/v1'
    API_BASE_URL_V2 = 'https://api.combocurve.com/v2'  # async export and type-curve routes are the /v2 routes
    REFERENCE_WELLHEADER = config.REFERENCE_WELLHEADER
    WELLHEADER_COLUMNS: ClassVar[dict[str, str]] = {
        header_key.lower(): header_key for header_key in config.REFERENCE_WELLHEADER
    }
    ECON_MODELS = config.ECON_MODELS

    def __init__(self, auth: Optional[APIAuth] = None) -> None:
        """
        With no `auth`, read the credentials in `~/.combocurve`: the files of the unzipped ComboCurve
        credential download (`api-key.txt` with `api-credentials.json` or
        `api-service-account-key.json`), else the deprecated `combocurve.json` + `cc-api.config.json`.
        """
        self.auth: APIAuth = auth if auth is not None else default_auth()
        self._auth_lock = threading.Lock()

    @classmethod
    def from_credentials_directory(cls, directory: Union[str, Path]) -> Self:
        """
        Read the credentials from an unzipped ComboCurve credential download in `directory`: either
        type (OAuth `api-credentials.json` or legacy `api-service-account-key.json`) with
        `api-key.txt`, at the top of `directory` or in the ZIP's `combocurve/` folder.
        """
        return cls(auth=auth_from_credentials_directory(directory))

    @classmethod
    def from_alternate_config(
        cls, combocurve_json_path: Union[str, Path], cc_api_config_json_path: Union[str, Path]
    ) -> Self:
        """
        Deprecated; removed in a 3.x release, not before 2027-01-31. Use `from_credentials_directory`.
        `combocurve_json_path` may hold either credential type; its `type` field selects the auth.
        """
        warn_deprecated(
            'from_alternate_config is deprecated and is removed in a 3.x release, not before 2027-01-31; '
            'use from_credentials_directory with the directory of the unzipped ComboCurve credential download.'
        )
        api_key = config.Configuration.from_file(cc_api_config_json_path).apikey
        return cls(auth=auth_from_credentials_file(combocurve_json_path, api_key))

    def __getstate__(self) -> dict[str, Any]:
        """Pickle / deepcopy state without `_auth_lock`: a lock cannot be pickled, and a copy needs its own."""
        state = dict(self.__dict__)
        state.pop('_auth_lock', None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore pickled state and give the copy a new `_auth_lock`."""
        self.__dict__.update(state)
        self._auth_lock = threading.Lock()

    def _auth_headers(self) -> dict[str, str]:
        """Auth headers for one request, fetched under a lock.

        `ComboCurveAuth.get_auth_headers` refreshes an expired token IN PLACE, and two
        threads refreshing at once is undefined. Every header fetch goes through here so it
        is serialised; the lock is held only for that fetch, never across the
        HTTP request itself. `aries pull` fans GETs across a thread pool, so several threads
        can hit an expired token in the same instant -- without this they refresh concurrently.
        The batched-write workers (`_send_one_chunk`) fetch through here per request too.
        """
        with self._auth_lock:
            return dict(self.auth.get_auth_headers())

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

        Retries HTTP 429 (waiting `Retry-After` or the default quota pause) and, for a
        GET or HEAD, transient gateway errors 502/503/504 (exponential backoff), for up to
        `_MAX_REQUEST_RETRIES` retries. Any other response (success or a
        non-transient error) is returned immediately for the caller to handle
        (e.g. `raise_for_status`). The status retries are `_transport._send_with_status_retries`;
        a connection failure is handled one level down, in `_transport._send_request` (timeout,
        and a second send only when it cannot write twice).

        Every verb funnels through here EXCEPT the batched-write path (`_send_one_chunk` ->
        `_transport._send_batch_chunk` calls `_send_request` directly and carries its own status
        retry loop), so this is also
        where `params` is reconciled against a query string already present on
        `url` -- see `_drop_params_already_in_url`. The batch path passes no `params`,
        so it has nothing to reconcile today; a future change that adds one there would
        NOT be covered by this.
        """
        params = _drop_params_already_in_url(url, params)
        return _send_with_status_retries(method, url, self._auth_headers, params=params, json_body=json_body)

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

            next_page_url: Optional[str] = _next_page_url_on_request_origin(response.headers, url)
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

                next_page_url: Optional[str] = _next_page_url_on_request_origin(response.headers, chunk_url)
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
        chunk_spec: ChunkSpec,
        rate_limit: _RateLimitState,
    ) -> BatchChunk:
        """Send one batch chunk with transient-failure retries; parse its 207 body.

        Runs on a worker thread. Auth headers are fetched through `_auth_headers` for every attempt.
        The retry policy (429 pauses shared through `rate_limit`, gateway statuses for read-only methods
        only, `may_have_applied` on a write that may have reached the server, the call deadline) is
        `_transport._send_batch_chunk`'s.
        """
        return _send_batch_chunk(method, url, self._auth_headers, chunk_spec, rate_limit)

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

        Auth headers are fetched per request through `_auth_headers`, whose lock keeps
        the workers from refreshing the token concurrently. A chunk that failed with
        `may_have_applied=True` must not be sent again before checking the server.
        """
        chunk_specs: list[ChunkSpec] = []
        offset = 0
        for index, chunk in enumerate(chunked(data, chunksize)):
            records: ItemList = list(chunk)
            chunk_specs.append(ChunkSpec(index=index, offset=offset, records=records))
            offset += len(records)

        rate_limit = _RateLimitState(pause_seconds=_RATE_LIMIT_DEFAULT_PAUSE_SECONDS)
        completed: list[BatchChunk] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._send_one_chunk, method, url, chunk_spec, rate_limit) for chunk_spec in chunk_specs
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

    def _count_items(self, url: str, method: str = 'head') -> int:
        """Send a HEAD request to `url` and return its `X-Query-Count` header as an int.

        Every list route has a HEAD twin that returns no body, only the total number of
        documents matching the url's filters (verified live 2026-09-29: `take` does not
        change it, and a filter that matches nothing gives 0). A response without the
        header raises instead of reading as 0, so "could not count" never looks like
        "counted nothing".

        `method='get'` sends a GET instead, for the `.../head` sub-routes that formations and
        shapefiles publish for clients that cannot send HEAD: same header, no body, same
        contract. A keyword rather than a second method, so the header contract is in one place.
        """
        response = self._request_with_retry(method, url)
        response.raise_for_status()
        count = response.headers.get('X-Query-Count')
        if count is None:
            raise ValueError(f'{method.upper()} {url} returned no X-Query-Count header')

        return int(count)

    def _send_for_item(self, method: str, url: str, body: Optional[Item] = None) -> Item:
        """Send one request with a single-object JSON body (or none) and return the single-object response.

        For the routes whose body and answer are one object, not the list that `_post_items` and the
        other list helpers chunk and page: one `_request_with_retry` call, `raise_for_status`, then the
        first object of `_extract_json`. No next page is followed.
        """
        response = self._request_with_retry(method, url, json_body=body)
        response.raise_for_status()
        return self._extract_json(response)[0]

    @staticmethod
    def _wait_for_job(
        read_job: Callable[[], Item], timeout_seconds: float, poll_seconds: float, description: str
    ) -> Item:
        """Call `read_job` every `poll_seconds` until the job's `status` is not in `RUNNING_JOB_STATUSES`
        (`pending`, `running`), and return the last job read; the caller checks its `status`. Raises
        `TimeoutError` when the next poll would come after `timeout_seconds` (counted with
        `time.monotonic` from this call); `description` names the job in that message
        (`'shapefile job <id>'`). A job read with no `status` (absent or null) raises `ValueError`
        naming `description` and the keys it has: a missing status is not a finished job. Sleeps with
        `time.sleep`, which tests patch.
        """
        deadline = time.monotonic() + timeout_seconds
        while True:
            job = read_job()
            if job.get('status') is None:
                raise ValueError(f'{description} was read with no status; its keys are {sorted(job)}')
            if job.get('status') not in RUNNING_JOB_STATUSES:
                return job
            if time.monotonic() + poll_seconds > deadline:
                raise TimeoutError(f'{description} is still {job.get("status")!r} after {timeout_seconds} seconds')
            time.sleep(poll_seconds)

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

        The same generator as the public `iter_pages`, which holds the code and the documentation.
        Downstream code calls this name, so it stays without a deprecation warning.
        """
        yield from self.iter_pages(url, params)

    def iter_pages(self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> Iterator[ItemList]:
        """
        Yield one page of a GET list route at a time: the parsed JSON list of each response, so a
        caller can stop early and bound its memory or bytes while it reads.

        Next pages are followed through the `Link` response header, with the scheme and host of the
        request (never the host the header names), and with the same retries and timeouts as every
        other GET. Pages come in ComboCurve's order and are not sorted: the `get_*` list methods sort
        their combined result with `_keysort`, and this iterator does not.

        Pass the `url` from a public `get_*_url` builder and a `take` page size, in the url or in
        `params`. A `take` above the route's maximum is answered with 400. Maximums to use (the
        module `GET_LIMIT*` constants): 200 for most list routes (projects, scenarios, forecasts,
        econ runs, econ models, embedded lookup tables, formations, shapefiles); wells 1,000;
        forecast outputs for ARIES 1,000; type-curve list 2,500 (type-curve volumes 2,500, type-curve
        wells 1,000); scenario model assignments and well incrementals 500; econ-run monthly
        exports 100; directional surveys 100; production 20,000. Read the constant in the module
        that builds the route; this list can go stale.

        The generator is lazy: no request is sent until the first page is read, and a caller that
        stops reading stops the requests, so a request is sent only for the pages consumed.

        `params` goes to `requests` apart from the query string of `url`. A key in both is sent once:
        the url wins (see `_drop_params_already_in_url`).
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

    def _delete_headers(self, url: str, data: Optional[ItemList] = None) -> CaseInsensitiveDict[str]:
        """
        DELETE `url`, with `data` as the body when given, and return the headers of its one response.
        A delete by id sends no body.
        """
        responses = self._delete_responses(url, [] if data is None else data)
        return responses[0].headers

    @staticmethod
    def _require_records(data: ItemList, noun: str) -> None:
        """
        Refuse empty `data` before any request. An empty list would reach the transport's no-body
        branch, so the route would receive a request with no records.
        """
        if not data:
            raise ValueError(f'data must hold at least one {noun}')

    @staticmethod
    def _records_from(data: Union[Item, ItemList], noun: str) -> ItemList:
        """
        Return `data` as a list of records for a route whose body is an array: a single record (a `dict`)
        becomes a one-item list, and any other iterable is materialised with `list()`, so a one-shot
        iterable is read once. An empty result is refused by `_require_records`, with `noun` in the message.
        """
        records = [data] if isinstance(data, dict) else list(data)
        APIBase._require_records(records, noun)
        return records

    @staticmethod
    def _require_id_sequence(ids: Sequence[str], argument: str) -> list[str]:
        """
        Return `ids` as a list, or raise when it names no id: a bare `str` (it would be sent one
        character per id), an empty sequence, or an empty id (an unresolved lookup). The whitespace around
        each `str` id is stripped, so `' a '` is sent as `'a'` and an id of only whitespace counts as empty.
        The list is taken FIRST, so a one-shot iterable cannot pass the check and then arrive empty, which
        would widen a delete to the whole group.
        """
        if isinstance(ids, str):
            raise ValueError(f'{argument} must be a sequence of ids, not a str')
        id_list = [value.strip() if isinstance(value, str) else value for value in ids]
        if not id_list or not all(id_list):
            raise ValueError(f'{argument} must be a non-empty sequence of non-empty ids')
        return id_list

    @staticmethod
    def _require_at_most(count: int, limit: int, argument: str, noun: str) -> None:
        """
        Refuse a `count` above `limit` before any request: the route takes at most `limit` per request,
        and the methods that call this send one request rather than split it (a split write can leave
        its earlier batches applied when a later one fails, and the helper returns nothing that tells
        the caller which were sent). `argument` and `noun` name the parameter and what is counted in
        the message (`data holds 501 records; ...`).
        """
        if count > limit:
            raise ValueError(f'{argument} holds {count} {noun}; the route takes at most {limit} per request')

    @staticmethod
    def _count_well_ids(data: ItemList) -> int:
        """The number of `wellIds` across the records of `data`; a record without a list `wellIds` counts 0."""
        count = 0
        for record in data:
            well_ids = record.get('wellIds')
            if isinstance(well_ids, list):
                count += len(well_ids)
        return count

    @staticmethod
    def _split_ids(ids: Union[str, Sequence[str]], argument: str) -> list[str]:
        """
        Return `ids` as a list of ids, or raise when it names no id or holds an empty one.

        A sequence is checked by `_require_id_sequence` (empty, an empty id, or a bare `str`
        refused; the whitespace around each id stripped). A `str` is taken as one id or a list the caller
        joined with `,`, and is split on `,`, with the whitespace around each element stripped
        (`'a, b'` gives `['a', 'b']`): it is refused when it is empty or when an element is empty after
        stripping (`'a,'`, `','`, `'a,,b'`, `' '`, `'a, ,b'`). Either would send a blank id (`wells=` or
        `wells=a,`).
        """
        if isinstance(ids, str):
            id_list = [element.strip() for element in ids.split(',')]
            if not all(id_list):
                raise ValueError(f'{argument} must name at least one id, with no empty id between commas')
            return id_list
        return APIBase._require_id_sequence(ids, argument)

    @staticmethod
    def _require_assignment_wells(data: ItemList) -> None:
        """
        Refuse an assignment record that names no well: one without `allWells: true` whose `wellIds`
        is absent, empty, a bare `str`, or holds an empty id (an unresolved lookup). Checked for every
        record before any request.
        """
        for index, record in enumerate(data):
            if record.get('allWells') is True:
                continue
            well_ids = record.get('wellIds')
            if not isinstance(well_ids, Sequence):
                raise ValueError(f'data[{index}] must have allWells: true or a non-empty wellIds')
            APIBase._require_id_sequence(cast('Sequence[str]', well_ids), f'data[{index}].wellIds')

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
    def _build_params_string(filters: Optional[QueryFilters] = None) -> str:
        """Render `filters` as a query string, or `''` when there is nothing to send.

        `None` values are DROPPED rather than rendered, matching how `requests` treats a
        `None` in `params`. The previous f-string interpolation emitted the literal text
        `None` (`?take=None`), which the API rejects on any numeric field.

        Values are percent-encoded, so a filter carrying `&`, `=`, `#`, a space or a
        non-ASCII character (a project or well name, say) no longer corrupts the query.

        `,` is deliberately left LITERAL via `safe`, and `quote` is used instead of the
        `urlencode` default `quote_plus` so a space encodes as `%20` rather than `+`.
        `econ_runs` comma-joins its `columns` filter, and `scenarios.delete_scenario_qualifiers`
        forwards `econNames`/`qualifierNames` as strings the caller has already comma-joined.
        Those comma-separated wire formats were verified live against the API in their
        unencoded form, so encoding the separator would break a request known to work,
        for no benefit: `,` is a legal unencoded query character (RFC 3986 sub-delim). Not
        every route takes a comma list: the econ-model assignment DELETE (`_econ_model_base`)
        answers a comma-joined `wells` of two or more ids with 400 (verified live 2026-11-21),
        so it sends one repeated `wells` key per id (the sequence rule below). Do
        NOT add `+` to `safe` to match -- a literal `+` is decoded as a space under
        form-urlencoded query rules, so `quote` correctly emits it as `%2B`.

        A non-`str` sequence value repeats its key once per element (`{'well': ['a', 'b']}` ->
        `?well=a&well=b`), which is how the forecast-outputs `well` filter and the v2 type-curve
        `phase` filter take several values; a comma-joined `well` is a 400 (verified live
        2026-11-05). A `str` value is never split. An `int` value is rendered with `str`.
        """
        pairs = [(key, value) for key, value in (filters or {}).items() if value is not None]

        return '?' + urlencode(pairs, doseq=True, safe=',', quote_via=quote) if pairs else ''

    @staticmethod
    def _filter_value_batches(
        filters: Optional[QueryFilters], key: str, limit: int = WELL_FILTER_LIMIT
    ) -> list[Optional[QueryFilters]]:
        """Split a repeated-key filter list longer than `limit` into filters of at most `limit` values each.

        `None`, a single string, and a list at or under the limit pass through as one batch. A longer list is
        de-duplicated first, so a repeated id does not return its rows twice, then cut with `more_itertools.chunked`
        (the same chunker the batched writes use). The batches cover disjoint values, so their rows concatenate and
        their counts add.

        A split into more than one batch refuses a `skip` or `cursor` filter with `ValueError`, before any
        request: each batch request would carry it, so `skip=10` would skip 10 rows per batch and a cursor
        from one batch means nothing to the next. A single batch keeps them. A `skip` of `0` or `'0'` skips
        nothing, so it is not refused; every batch carries it.
        """
        if filters is None:
            return [None]

        values = filters.get(key)
        if values is None or isinstance(values, (str, int)) or len(values) <= limit:
            return [filters]

        batches: list[Optional[QueryFilters]] = []
        for batch_values in chunked(dict.fromkeys(values), limit):
            batch: dict[str, Union[str, int, Sequence[str], None]] = {**filters, key: list(batch_values)}
            batches.append(batch)

        if len(batches) > 1:
            paging_keys = APIBase._paging_filters_in(filters)
            if paging_keys:
                raise ValueError(
                    f'{paging_keys[0]!r} cannot be combined with more than {limit} distinct {key!r} values: the '
                    f'{key!r} list is split into requests of {limit} values each, and every request would apply '
                    f'{paging_keys[0]!r} on its own. Page through fewer {key!r} values, or drop {paging_keys[0]!r}.'
                )

        return batches

    @staticmethod
    def _paging_filters_in(filters: Optional[QueryFilters]) -> list[str]:
        """The paging filters (`skip`, `cursor`) that `filters` sets, in that order. A `skip` of 0 (or '0') is a
        no-op and is not counted. A caller that splits one read into several requests refuses these, because each
        request would apply them on its own."""
        if filters is None:
            return []
        return [
            key
            for key in _PAGING_FILTER_KEYS
            if filters.get(key) is not None and not (key == 'skip' and str(filters.get(key)) == '0')
        ]

    def _get_items_in_value_batches(
        self,
        build_url: Callable[[Optional[QueryFilters]], str],
        filters: Optional[QueryFilters],
        key: str,
        params: Optional[Mapping[str, Union[str, int, float]]] = None,
    ) -> ItemList:
        """GET every row matching `filters`, splitting a `key` list longer than `WELL_FILTER_LIMIT` into
        requests of at most that many distinct values (`_filter_value_batches`, which also refuses `skip` and
        `cursor` on a split). `build_url` turns one batch's filters into the request url; `params` goes with
        every request. The rows of the batches are concatenated in request order, unsorted.
        """
        items: ItemList = []
        for batch_filters in self._filter_value_batches(filters, key):
            items.extend(self._get_items(build_url(batch_filters), params))

        return items

    def _count_items_in_value_batches(
        self, build_url: Callable[[Optional[QueryFilters]], str], filters: Optional[QueryFilters], key: str
    ) -> int:
        """Count the rows matching `filters` with one HEAD request per batch of `_filter_value_batches` (see
        `_get_items_in_value_batches`) and return the sum. The batches cover disjoint values, so the counts add.
        """
        return sum(
            self._count_items(build_url(batch_filters)) for batch_filters in self._filter_value_batches(filters, key)
        )

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

        duplicated = sorted(position for position, count in Counter(order.values()).items() if count > 1)
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
