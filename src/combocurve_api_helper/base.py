import warnings
from pathlib import Path
import json
from itertools import chain
from more_itertools import chunked
from typing import List, Dict, Optional, Union, Any, Iterable, Iterator, Mapping
from typing_extensions import Self

import requests  # type: ignore
from requests import Response
from combocurve_api_v1 import ServiceAccount, ComboCurveAuth  # type: ignore
from combocurve_api_v1.pagination import get_next_page_url  # type: ignore

from . import config


PrimativeValue = Union[str, int, float, bool]
IterableValue = Union[List[str], List[int], List[float], List[bool], Dict[str, Union[PrimativeValue, 'IterableValue']]]
Item = Dict[str, Union[PrimativeValue, IterableValue]]
ItemList = List[Item]


class APIBase:
    API_BASE_URL = 'https://api.combocurve.com/v1'


    def __init__(self) -> None:
        account = ServiceAccount.from_file(str(config.COMBOCURVE_JSON))
        self.auth = ComboCurveAuth(account, config.cfg.apikey)

        ref_wells_json = json.loads(Path(config.REFRENCE_WELLS_JSON).read_text())
        self.ref_wells: Dict[str, Union[str, int, float]] = {k.lower(): k for k in ref_wells_json.keys()}


    @classmethod
    def from_alternate_config(
            cls,
            combocurve_json_path: Union[str, Path],
            cc_api_config_json_path: Union[str, Path]) -> Self:
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


    def _request_items_pages(
            self, method: str, url: str,
            params: Optional[Mapping[str, Union[str, int, float]]] = None) -> Iterator[Response]:
        """
        Generic method for dispatching GET requests for the given `url` yielding
        response of each page
        """
        # keep fetching while there are more records to be returned
        while True:
            headers = self.auth.get_auth_headers()
            response = requests.request(method, url, headers=headers, params=params)
            try:
                response.raise_for_status()
            except Exception as e:
                print(f'\nURL: {url}\nParams: {params}\n')
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
            self, method: str, url: str, data: ItemList, chunksize: Optional[int] = None,
            params: Optional[Mapping[str, Union[str, int, float]]] = None) -> ItemList:
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
                headers = self.auth.get_auth_headers()
                response = requests.request(method, url, headers=headers, json=chunk, params=params_)
                try:
                    response.raise_for_status()
                except Exception as e:
                    print(f'\nURL: {url}\n')
                    raise e

                yield response

                next_page_url: Optional[str] = get_next_page_url(response.headers)
                if next_page_url is None:
                    # no more pages to process
                    break
                else:
                    url = next_page_url

                params_ = None


    def _get_responses_iterator(
            self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> Iterator[Response]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages('get', url, params)


    def _get_responses(
            self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> List[Response]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages('get', url, params))


    def _get_items_iterator(
            self, url: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages('get', url, params):
            yield self._extract_json(response)


    def _get_items(
            self, url: str,
            params: Optional[Mapping[str, Union[str, int, float]]] = None) -> ItemList:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages('get', url, params):
            items.extend(self._extract_json(response))

        return items


    def _post_responses_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[Response]:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('post', url, data, chunksize)


    def _post_responses(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('post', url, data, chunksize))


    def _post_items_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('post', url, data, chunksize):
            yield self._extract_json(response)


    def _post_items(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching POST requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('post', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items


    def _patch_responses_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[Response]:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('patch', url, data, chunksize)


    def _patch_responses(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('patch', url, data, chunksize))


    def _patch_items_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('patch', url, data, chunksize):
            yield self._extract_json(response)


    def _patch_items(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('patch', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items


    def _put_responses_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[Response]:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('put', url, data, chunksize)


    def _put_responses(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('put', url, data, chunksize))


    def _put_items_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('put', url, data, chunksize):
            yield self._extract_json(response)


    def _put_items(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching PUT requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('put', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items


    def _delete_responses_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[Response]:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning a generator of requests.Response
        """
        yield from self._request_items_pages_chunks('delete', url, data, chunksize)


    def _delete_responses(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> List[Response]:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning a list of requests.Response
        """
        return list(self._request_items_pages_chunks('delete', url, data, chunksize))


    def _delete_items_iterator(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> Iterator[ItemList]:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning a generator of JSON of type: list of objects
        """
        for response in self._request_items_pages_chunks('delete', url, data, chunksize):
            yield self._extract_json(response)


    def _delete_items(
            self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching DELETE requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        items: ItemList = []
        for response in self._request_items_pages_chunks('delete', url, data, chunksize):
            items.extend(self._extract_json(response))

        return items


    @staticmethod
    def _keysort(items: ItemList, order: Dict[str, int], reverse: bool = False
                 ) -> ItemList:
        """
        Return an iterable of dictionaries where each dictionary has
        its keys sorted by the given `order`. The `order` is a mapping
        that defines the key => integer index to order by.
        """
        def sort_by_key(kv: Item) -> List[str]:
            """
            Returns a sort order for a dictionary key.
            """
            keys, values = zip(*((k, v) for k, v in kv.items() if k in order))

            for k in order.keys():
                if k not in keys:
                    raise KeyError(f'Order Key `{k}` not found in response: {kv.keys()}')

            values_pre: List[str] = []
            for value in values:
                if not isinstance(value, str):
                    continue

                values_pre.append(value)

            orders = (order[k] for k in keys)
            return [values_pre[o] for o in orders]

        return list(sorted(items, key=sort_by_key, reverse=reverse))


    @staticmethod
    def extract_id(items: Union[Item, ItemList],
                   name: str, name_key: str = 'name', id_key: str = 'id') -> Optional[str]:
        id_: Optional[str] = None

        if not isinstance(items, (dict, list)):
            warnings.warn(  # type: ignore
                f'Expected items to be a dict or list, got {type(items)}', RuntimeWarning)
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
