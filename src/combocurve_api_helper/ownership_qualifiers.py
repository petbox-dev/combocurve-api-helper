from typing import Dict, Optional

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class OwnershipQualifiers(APIBase):
    ######
    # URLs
    ######

    def get_ownership_qualifiers_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for ownership qualifiers.
        """
        url = f'{self.API_BASE_URL}/ownership-qualifiers'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_ownership_qualifier_by_id_url(self, ownership_qualifier_id: str) -> str:
        """
        Returns the API url for a specific ownership qualifier from its id.
        """
        base_url = self.get_ownership_qualifiers_url()
        return f'{base_url}/{ownership_qualifier_id}'

    ###########
    # API calls
    ###########

    def get_ownership_qualifiers(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of ownership qualifiers. Distinct from scenario
        qualifiers (see the scenarios methods).

        https://docs.api.combocurve.com/api/get-ownership-qualifiers
        """
        url = self.get_ownership_qualifiers_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_ownership_qualifier_by_id(self, ownership_qualifier_id: str) -> Item:
        """
        Returns a specific ownership qualifier from its id.

        https://docs.api.combocurve.com/api/get-ownership-qualifier-by-id
        """
        url = self.get_ownership_qualifier_by_id_url(ownership_qualifier_id)
        return self._get_items(url)[0]

    def post_ownership_qualifiers(self, data: ItemList) -> ItemList:
        """
        Creates one or more ownership qualifiers.

        https://docs.api.combocurve.com/api/post-ownership-qualifiers
        """
        url = self.get_ownership_qualifiers_url()
        return self._post_items(url, data)

    def put_ownership_qualifiers(self, data: ItemList) -> ItemList:
        """
        Upserts one or more ownership qualifiers.

        https://docs.api.combocurve.com/api/put-ownership-qualifiers
        """
        url = self.get_ownership_qualifiers_url()
        return self._put_items(url, data)
