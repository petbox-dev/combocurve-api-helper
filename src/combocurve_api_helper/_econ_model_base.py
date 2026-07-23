from typing import Dict, List, Optional, Sequence, Union, cast

from requests import Response

from .base import APIBase, Item, ItemList, WriteResponse


GET_LIMIT = 200

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
        self, project_id: str, econ_model_type: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
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
        self, project_id: str, econ_model_type: str, model_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
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
        self, project_id: str, econ_model_type: str, model_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for assignments of a sepcific econ model for a
        specific project id and model type. Allows `econModelType` passed as a
        parameter rather than calling a different function for each model type.
        """

        def _get_route_for_assignment(econ_model_type: str) -> Union[str, None]:
            # The assignment route's {econName} path segment is the KEBAB
            # `route` (e.g. `fluid-models`), NOT the PascalCase `econModelType`.
            # The server tolerates PascalCase for most types by coincidental
            # normalization, but REJECTS it for FluidModel
            # (`InvalidEconName: fluidmodel`); only the `route` resolves for all
            # types. Verified live 2026-07. See econModels.json name-form note.
            for model in APIBase.ECON_MODELS:
                if model['econModelType'].casefold() == econ_model_type.casefold():
                    return model['route']

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
        self, project_id: str, econ_model_type: str, filters: Optional[Dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of econ models by type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model
        type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type, filters)
        params = {'take': GET_LIMIT}
        econ_models = self._get_items(url, params)

        return self._keysort(econ_models, SORT_ORDER)

    def get_econ_model_by_type_by_id(self, project_id: str, econ_model_type: str, model_id: str) -> Union[Item, None]:
        """
        Returns a specific econ model from its type and id. Allows
        `econModelType` passed as a parameter rather than calling a different
        function for each model type.
        """
        url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        econ_model = self._get_items(url)

        return econ_model[0]

    def post_econ_models_by_type(self, project_id: str, econ_model_type: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates econ models of a specific type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type)
        return cast(List[WriteResponse], self._post_items(url, data))

    def put_econ_models_by_type(self, project_id: str, econ_model_type: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts econ models of a specific type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type)
        return cast(List[WriteResponse], self._put_items(url, data))

    def delete_econ_model_by_type_by_id(self, project_id: str, econ_model_type: str, model_id: str) -> List[Response]:
        """
        Deletes a specific econ model by type + id. Allows `econModelType`
        passed as a parameter rather than calling a different function for each
        model type.
        """
        url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._delete_responses(url, data=[])

    def get_econ_model_assignments_by_type_by_id(
        self, project_id: str, econ_model_type: str, model_id: str
    ) -> Union[ItemList, None]:
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
        self, project_id: str, econ_model_type: str, model_id: str, data: ItemList
    ) -> List[WriteResponse]:
        """Create assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return cast(List[WriteResponse], self._post_items(url, data))

    def put_econ_model_assignments_by_type_by_id(
        self, project_id: str, econ_model_type: str, model_id: str, data: ItemList
    ) -> List[WriteResponse]:
        """Upsert assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return cast(List[WriteResponse], self._put_items(url, data))

    def delete_econ_model_assignments_by_type_by_id(
        self,
        project_id: str,
        econ_model_type: str,
        model_id: str,
        scenario_id: str,
        qualifier_name: Optional[str] = None,
        wells: Union[str, Sequence[str], None] = None,
        all_wells: Optional[bool] = None,
    ) -> List[Response]:
        """Delete assignments for a specific econ model (by type + id).

        Unlike POST/PUT on the same route, DELETE takes query parameters, not
        a JSON body: `scenarioId` is required; `qualifierName`, `wells`, and
        `allWells` are optional filters narrowing which assignments are
        removed. Confirmed against the official ComboCurve Postman
        collection.

        `wells` accepts either a comma-separated string or a sequence of
        well-id strings -- POST/PUT assignment bodies carry `wells` as a
        list, so callers that reuse that value here (e.g. JSON-driven
        callers not protected by mypy) are normalized rather than silently
        producing a Python list-repr query param that matches nothing."""
        filters: Dict[str, str] = {'scenarioId': scenario_id}
        if qualifier_name is not None:
            filters['qualifierName'] = qualifier_name

        if wells is not None:
            filters['wells'] = wells if isinstance(wells, str) else ','.join(wells)

        if all_wells is not None:
            filters['allWells'] = str(all_wells).lower()

        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id, filters)
        return self._delete_responses(url, data=[])
