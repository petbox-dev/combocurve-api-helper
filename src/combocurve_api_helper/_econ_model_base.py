from typing import Dict, Optional, Union

from .base import APIBase, Item, ItemList


GET_LIMIT = 200
POST_LIMIT = 500
PUT_LIMIT = 500

SORT_ORDER = {
    'name': 0,
    'id': 3,
    'createdAt': 2,
    'updatedAt': 1,
}


class _EconModelMethodsBase(APIBase):
    """
    Generic, type-parameterized econ-model delegates shared by every per-type
    method in `_GeneratedModelMethods`. These are the non-per-type endpoints:
    list all econ models, list/get/assignments by an explicit `econModelType`,
    and the assignment write generics (POST/PUT/DELETE). The generated per-type
    methods call these via `self.<generic>`, so they live on a shared base
    (rather than a Protocol) to type-check cleanly.
    """

    ######
    # URLs
    ######


    def get_econ_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of econ models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_econ_models_by_type_url(
            self, project_id: str, econ_model_type: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of econ models for a specific project id and model
        type. Allows `econModelType` passed as a parameter rather than calling
        a different function for each model type.
        """
        def _get_route_for_model(econ_model_type: str) -> Union[str, None]:
            for model in APIBase.ECON_MODELS:
                if model['econModelType'].casefold() == econ_model_type.casefold():
                    return model['route']

            return None

        route = _get_route_for_model(econ_model_type)
        assert route is not None, f'Invalid econ model type: {econ_model_type}'
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/{route}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_econ_model_by_type_by_id_url(
            self, project_id: str, econ_model_type: str, model_id: str,
            filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of a sepcific econ model for a specific project id
        and model type. Allows `econModelType` passed as a parameter rather
        than calling a different function for each model type.
        """
        base_url = self.get_econ_models_by_type_url(project_id, econ_model_type)
        url = f'{base_url}/{model_id}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_econ_model_assignments_by_type_by_id_url(
            self, project_id: str, econ_model_type: str, model_id: str,
            filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for assignments of a sepcific econ model for a
        specific project id and model type. Allows `econModelType` passed as a
        parameter rather than calling a different function for each model type.
        """
        def _get_route_for_assignment(econ_model_type: str) -> Union[str, None]:
            for model in APIBase.ECON_MODELS:
                if model['econModelType'].casefold() == econ_model_type.casefold():
                    return model['econModelType']

            return None

        route = _get_route_for_assignment(econ_model_type)
        assert route is not None, f'Invalid econ model type: {econ_model_type}'
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/{route}/{model_id}/assignments'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    ###########
    # API calls
    ###########


    def get_econ_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ models.
        """
        url = self.get_econ_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        econ_models = self._get_items(url, params)

        return self._keysort(econ_models, SORT_ORDER)


    def get_econ_models_by_type(
            self, project_id: str, econ_model_type: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ models by type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model
        type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type, filters)
        params = {'take': GET_LIMIT}
        econ_models = self._get_items(url, params)

        return self._keysort(econ_models, SORT_ORDER)


    def get_econ_model_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str) -> Union[Item, None]:
        """
        Returns a specific econ model from its type and id. Allows
        `econModelType` passed as a parameter rather than calling a different
        function for each model type.
        """
        url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        econ_model = self._get_items(url)

        return econ_model[0]


    def get_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str) -> Union[ItemList, None]:
        """
        Returns a specific econ model assignment from its type and id. Allows
        `econModelType` passed as a parameter rather than calling a different
        function for each model type.
        """
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        assignments = self._get_items(url)

        if len(assignments) == 0:
            return None

        return assignments


    def post_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList:
        """Create assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._post_items(url, data)

    def put_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList:
        """Upsert assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._put_items(url, data)

    def delete_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList:
        """Delete assignments for a specific econ model (by type + id).

        NOTE: the delete request body/filters for this route are UNVERIFIED and
        remain unconfirmed until a live dev test (Task 6) exercises them
        against the API; adjust here if the live response shows a different
        shape (e.g. query filters instead of a JSON body)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._delete_responses(url, data)  # type: ignore[return-value]
