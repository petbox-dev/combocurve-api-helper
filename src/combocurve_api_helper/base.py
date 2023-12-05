import warnings
from pathlib import Path
from functools import cache
import json
from more_itertools import chunked
from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, Sequence, cast

import requests # type: ignore
from combocurve_api_v1 import ServiceAccount, ComboCurveAuth  # type: ignore
from combocurve_api_v1.pagination import get_next_page_url  # type: ignore

from . import config


Item = Dict[str, Union[str, int, float, bool, List[str], List[int], List[float], List[bool]]]
ItemList = List[Item]


@cache
def combocurve_auth() -> ComboCurveAuth:
    """
    Returns an instance of the ComboCurve authorization object.
    """
    account = ServiceAccount.from_file(str(config.COMBOCURVE_JSON))
    auth = ComboCurveAuth(account, config.cfg.apikey)

    return auth


class APIBase:
    API_BASE_URL = 'https://api.combocurve.com/v1'


    def __init__(self) -> None:
        self.auth: ComboCurveAuth = combocurve_auth()
        self.onelines: Dict[str, ItemList] = dict()

        ref_wells_json = json.loads(Path(config.REFRENCE_WELLS_JSON).read_text())
        self.ref_wells: Dict[str, Union[str, int, float]] = {k.lower(): k for k in ref_wells_json.keys()}


    def authenticate(self) -> None:
        """
        Force re-authentication with the API
        """
        self.auth = combocurve_auth()


    def _get_items(self, url: str,
                   params: Optional[Mapping[str, Union[str, int, float]]] = None) -> List[Dict[str, Any]]:
        """
        Generic method for dispatching GET requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        _url: Optional[str] = url
        # dumb shit to keep mypy happy
        if _url is None:
            raise ValueError('url is None')

        headers = self.auth.get_auth_headers()

        items: List[Dict[str, Any]] = list()

        # keep fetching while there are more records to be returned
        while True:
            response = requests.get(_url, headers=headers, params=params)
            try:
                response.raise_for_status()
            except Exception as e:
                print(f'URL: {url}')
                raise e

            json = response.json()
            if isinstance(json, dict):
                json = [json]
            elif not isinstance(json, list):
                json = list(json)

            items.extend(json)

            _url = get_next_page_url(response.headers)
            if _url is None:
                # no more pages to process
                break

            if params is not None and 'take' in params.keys():
                _ = params.pop('take')  # type: ignore

        return items


    def _patch_items(self, url: str, data: ItemList, chunksize: Optional[int] = None) -> ItemList:
        """
        Generic method for dispatching PATCH requests for the given `url`
        strictly returning JSON of type: list of objects
        """
        _url: Optional[str] = url
        # dumb shit to keep mypy happy
        if _url is None:
            raise ValueError('url is None')

        headers = self.auth.get_auth_headers()

        items: ItemList = list()

        if chunksize is None:
            chunksize = len(data)

        for chunk in chunked(data, chunksize):
            # keep fetching while there are more records to be returned
            while True:
                response = requests.patch(_url, headers=headers, json=chunk)
                try:
                    response.raise_for_status()
                except Exception as e:
                    print(f'URL: {url}')
                    raise e

                json = response.json()
                if isinstance(json, dict):
                    json = [json]
                elif not isinstance(json, list):
                    json = list(json)

                items.extend(json)

                _url = get_next_page_url(response.headers)
                if _url is None:
                    # no more pages to process
                    break

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
            warnings.warn( # type: ignore
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
