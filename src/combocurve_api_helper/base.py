import warnings
from pathlib import Path
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import chain
from more_itertools import chunked
from typing import Callable, List, Dict, Optional, Sequence, Tuple, Union, Any, Iterable, Iterator, Mapping
from typing_extensions import Self, TypeAlias, TypedDict

import requests
from requests import Response
from combocurve_api_v1 import ServiceAccount, ComboCurveAuth
from combocurve_api_v1.pagination import get_next_page_url

from . import config
from ._batch import BatchChunk, BatchWriteResult, _RateLimitState


# A single JSON value: the recursive union of everything `json.loads` can yield.
# Models real API payloads faithfully -- `null` (None), arrays of objects, and
# nested objects are all representable, which the former `PrimativeValue` /
# `IterableValue` split could not express (it allowed lists of scalars only, and
# no nulls). The container arms are the COVARIANT `Sequence` / `Mapping`, not
# `List` / `Dict`: because `List`/`Dict` are invariant, a concrete `list[str]` or
# `list[dict[...]]` (e.g. a payload built by a caller, or a `list[str]` variable
# assigned into an item) is NOT a `List[JsonValue]` and would fail to type-check;
# `Sequence`/`Mapping` accept them. Self-references are quoted forward refs; mypy
# resolves the recursive alias.
JsonValue: TypeAlias = Union[None, str, int, float, bool, Sequence['JsonValue'], Mapping[str, 'JsonValue']]

# One API object (a JSON object) and a list of them -- the shapes every endpoint
# method takes and returns. These stay the mutable, invariant `Dict`/`List` (we
# build, extend, and index them internally); only the nested value arms above are
# the read-covariant `Sequence`/`Mapping`. Responses stay plain dicts, not custom
# model classes.
Item: TypeAlias = Dict[str, JsonValue]
ItemList: TypeAlias = List[Item]


class WriteError(TypedDict, total=False):
    """One entry in a write response's `generalErrors` list."""

    name: str
    message: str
    location: str


class WriteResponse(TypedDict):
    """The 207 envelope every create/update endpoint (POST/PUT/PATCH) returns.

    `_post_items` / `_put_items` / `_patch_items` yield one of these per request
    chunk, so a write method returns `List[WriteResponse]` (usually one element).

    `results` stays the generic `Item`: the per-record shape varies by resource
    (its id key is `id`, `forecastId`, `wellId`, ...; productions add `date`/`well`,
    wells add `chosenID`/`dataSource`, etc.), so no single TypedDict fits it and a
    generic dict avoids forcing casts to read a resource's own id/fields.
    """

    successCount: int
    failedCount: int
    results: ItemList
    generalErrors: List[WriteError]


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
    WELLHEADER_COLUMNS = {k.lower(): k for k in config.REFERENCE_WELLHEADER.keys()}
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
        """
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

        for chunk in chunked(data, chunksize):
            # keep fetching while there are more records to be returned
            params_ = params
            while True:
                response = self._request_with_retry(method, url, params=params_, json_body=chunk)
                try:
                    response.raise_for_status()
                except Exception as e:
                    print(f'\nException occured during request:\nURL: {url}\n')
                    raise e

                yield response

                next_page_url: Optional[str] = get_next_page_url(response.headers)
                if next_page_url is None:
                    # no more pages to process
                    break
                else:
                    url = next_page_url

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
        chunk_specs: List[Tuple[int, int, ItemList]] = []
        offset = 0
        for index, chunk in enumerate(chunked(data, chunksize)):
            chunk_list: ItemList = list(chunk)
            chunk_specs.append((index, offset, chunk_list))
            offset += len(chunk_list)

        headers = self.auth.get_auth_headers()
        rate_limit = _RateLimitState(pause_seconds=_RATE_LIMIT_DEFAULT_PAUSE_SECONDS)
        completed: List[BatchChunk] = []

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

    def _get_responses(self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> List[Response]:
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

    def _post_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
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

    def _patch_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
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

    def _put_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
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

    def _delete_responses(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
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
    def _build_params_string(filters: Optional[Dict[str, str]] = None) -> str:
        if filters is None or len(filters) == 0:
            return ''

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        return '?' + '&'.join(parameters)

    @staticmethod
    def _keysort(items: ItemList, order: Dict[str, int], reverse: bool = False) -> ItemList:
        """
        Return an iterable of dictionaries where each dictionary has
        its keys sorted by the given `order`. The `order` is a mapping
        that defines the key => integer index to order by.
        """

        def sort_by_key(item: Item) -> List[str]:
            """
            Returns a sort order for a dictionary key.
            """
            keys, values = zip(*((k, v) for k, v in item.items() if k in order))

            for k in order.keys():
                if k not in keys:
                    try:
                        raise KeyError(f'Order Key `{k}` not found in response: {item.keys()}')
                    except KeyError as e:
                        chosen_id = item.get('chosenId')
                        # print(f'Error for Chosen Id `{chosen_id}`:', e)
                        item.setdefault(k, None)
                        keys += (k,)
                        values += (None,)

            values_pre: List[str] = []
            for value in values:
                if value is None:
                    values_pre.append('')

                elif not isinstance(value, str):
                    values_pre.append(str(value))

                values_pre.append(value)

            orders = (order[k] for k in keys)
            return [values_pre[o] for o in orders]

        return list(sorted(items, key=sort_by_key, reverse=reverse))

    @staticmethod
    def extract_id(
        items: Union[Item, ItemList], name: str, name_key: str = 'name', id_key: str = 'id'
    ) -> Optional[str]:
        id_: Optional[str] = None

        if not isinstance(items, (dict, list)):
            warnings.warn(  # type: ignore
                f'Expected items to be a dict or list, got {type(items)}', RuntimeWarning
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
            warnings.warn(f'Could not find `id` for {name}', UserWarning)
        return id_

    @staticmethod
    def index_of(items: ItemList, value: str, key: str = 'id') -> Union[int, None]:
        id_: Optional[str] = None

        if not isinstance(items, list):
            warnings.warn(  # type: ignore
                f'Expected items to be a list, got {type(items)}', RuntimeWarning
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
            warnings.warn(f'Key `{key}` does not exist in items', UserWarning)
        else:
            warnings.warn(f'Could not find {value} for {key}', UserWarning)

        return None
