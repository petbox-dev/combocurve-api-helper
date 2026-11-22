from collections.abc import Sequence
from typing import Optional, Union, cast

from requests import Response

from .base import LIST_SORT_ORDER, WELL_FILTER_LIMIT, APIBase, Item, ItemList, QueryFilters, WriteResponse

GET_LIMIT = 200


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

    def get_econ_models_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of econ models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_econ_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of one econ model of any type for a specific project id.
        """
        return f'{self.get_econ_models_url(project_id)}/{model_id}'

    def get_econ_models_by_type_url(
        self, project_id: str, econ_model_type: str, filters: Optional[dict[str, str]] = None
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
        self, project_id: str, econ_model_type: str, model_id: str, filters: Optional[dict[str, str]] = None
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
        self,
        project_id: str,
        econ_model_type: str,
        model_id: str,
        filters: Optional[QueryFilters] = None,
    ) -> str:
        """
        Returns the API url for assignments of a sepcific econ model for a
        specific project id and model type. Allows `econModelType` passed as a
        parameter rather than calling a different function for each model type.
        A sequence value in `filters` repeats its key (the DELETE `wells`).
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

    def get_econ_models(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ models.
        """
        url = self.get_econ_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        econ_models = self._get_items(url, params)

        return self._keysort(econ_models, LIST_SORT_ORDER)

    def count_econ_models(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of econ models of every type in a project matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-econ-models
        """
        return self._count_items(self.get_econ_models_url(project_id, filters))

    def get_econ_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns the HEADER of one econ model of any type from its id, without knowing its type:
        `id`, `name`, `unique`, `well`, `createdBy`, `lastUpdatedBy`, `createdAt`, `updatedAt` and
        `econModelType` -- NOT its assumption body (verified live 2026-09-29: a Capex model came back
        without `otherCapex`). Use it to learn `econModelType`, then read the full model with
        `get_econ_model_by_type_by_id`.

        https://docs.api.combocurve.com/api/get-econ-model-by-id
        """
        url = self.get_econ_model_by_id_url(project_id, model_id)
        econ_model = self._get_items(url)

        return econ_model[0]

    def get_econ_models_by_type(
        self, project_id: str, econ_model_type: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of econ models by type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model
        type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type, filters)
        params = {'take': GET_LIMIT}
        econ_models = self._get_items(url, params)

        return self._keysort(econ_models, LIST_SORT_ORDER)

    def count_econ_models_by_type(
        self, project_id: str, econ_model_type: str, filters: Optional[dict[str, str]] = None
    ) -> int:
        """
        Returns the number of econ models of `econ_model_type` in a project matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).
        """
        return self._count_items(self.get_econ_models_by_type_url(project_id, econ_model_type, filters))

    def get_econ_model_by_type_by_id(self, project_id: str, econ_model_type: str, model_id: str) -> Union[Item, None]:
        """
        Returns a specific econ model from its type and id. Allows
        `econModelType` passed as a parameter rather than calling a different
        function for each model type.
        """
        url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        econ_model = self._get_items(url)

        return econ_model[0]

    def post_econ_models_by_type(self, project_id: str, econ_model_type: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates econ models of a specific type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type)
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_econ_models_by_type(self, project_id: str, econ_model_type: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts econ models of a specific type. Allows `econModelType` passed as
        a parameter rather than calling a different function for each model type.
        """
        url = self.get_econ_models_by_type_url(project_id, econ_model_type)
        return cast('list[WriteResponse]', self._put_items(url, data))

    def delete_econ_model_by_type_by_id(self, project_id: str, econ_model_type: str, model_id: str) -> list[Response]:
        """
        Deletes a specific econ model by type + id. Allows `econModelType`
        passed as a parameter rather than calling a different function for each
        model type.
        """
        url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._delete_responses(url, data=[])

    def get_econ_model_assignments_by_type_by_id(
        self, project_id: str, econ_model_type: str, model_id: str, filters: Optional[QueryFilters] = None
    ) -> Union[ItemList, None]:
        """
        Returns the assignments of one econ model, from its type and id, or `None` when it has none.
        Allows `econModelType` passed as a parameter rather than calling a different function for
        each model type.

        `filters` take the query keys the route documents: `wells` and `scenarios` (the same keys as
        `count_econ_model_assignments_by_type_by_id`, so a filtered count has a matching list), plus
        `sort`, `skip` and `take`. A `take` in `filters` sets the page size; without it the API's
        default page size is used. The rows are returned in the order received.

        https://docs.api.combocurve.com/api/get-econ-models-assignments-read

        Example response:
        [
            {
                "qualifierName": "string",
                "scenario": "string",
                "wells": [
                    "string"
                ]
            }
        ]
        """
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id, filters)
        assignments = self._get_items(url)

        if len(assignments) == 0:
            return None

        return assignments

    def count_econ_model_assignments_by_type_by_id(
        self, project_id: str, econ_model_type: str, model_id: str, filters: Optional[QueryFilters] = None
    ) -> int:
        """
        Returns the number of assignments of one econ model (filters: `wells`, `scenarios`) matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-econ-models-assignments-count
        """
        return self._count_items(
            self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id, filters)
        )

    def post_econ_model_assignments_by_type_by_id(
        self, project_id: str, econ_model_type: str, model_id: str, data: ItemList
    ) -> list[WriteResponse]:
        """Create assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_econ_model_assignments_by_type_by_id(
        self, project_id: str, econ_model_type: str, model_id: str, data: ItemList
    ) -> list[WriteResponse]:
        """Upsert assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return cast('list[WriteResponse]', self._put_items(url, data))

    def delete_econ_model_assignments_by_type_by_id(
        self,
        project_id: str,
        econ_model_type: str,
        model_id: str,
        scenario_id: str,
        qualifier_name: Optional[str] = None,
        wells: Union[str, Sequence[str], None] = None,
        all_wells: Optional[bool] = None,
    ) -> list[Response]:
        """Delete assignments for a specific econ model (by type + id).

        Unlike POST/PUT on the same route, DELETE takes query parameters, not
        a JSON body: `scenarioId` is required; `qualifierName`, `wells`, and
        `allWells` are optional filters narrowing which assignments are
        removed. Confirmed against the official ComboCurve Postman
        collection.

        `wells` accepts either a sequence of well-id strings or a string of
        one id or several joined with `,` (kept for backward compatibility).
        Both are sent as one repeated `wells` key per id (`wells=a&wells=b`):
        the route refuses a comma-joined value with 400 `RequestStructureError`
        (`` `a,b` is not a valid ObjectId ``), and deletes both wells with the
        repeated keys (`X-Delete-Count: 2`); verified live 2026-11-21 (dev).
        The comma-joined form this method sent before was refused for two wells.

        A `wells` that names no well is refused with `ValueError` before
        anything is sent: an empty sequence, a sequence holding an empty id, an
        empty string, or a string with an empty element between commas (`','`,
        `'a,'`). Each would send a blank well id; the route answers a blank
        `wells=` with 400 `RequestStructureError` (`` `` is not a valid
        ObjectId ``) and deletes nothing (verified live 2026-11-21, dev). Leave
        `wells` as `None` to send no well filter. The whitespace around each
        id is stripped. A blank `scenario_id`, or a blank `qualifier_name`
        (leave it `None` for every qualifier), is refused the same way: the
        route may read it as absent and unassign more.

        At most 100 well ids per call: the route answers 101 with 400
        `RequestStructureError` (`` `[object Object]` is not a valid
        ObjectId ``) and 500 with 431 (verified live 2026-11-21, dev). A
        longer `wells` raises `ValueError` before anything is sent; it is not
        split, so a call never leaves part of the list unassigned. Call once
        per 100 ids. The per-type `delete_<type>_assignments_by_id` wrappers
        call this method, so the same limit applies to them.

        https://docs.api.combocurve.com/api/delete-econ-model-assignment-delete"""
        # A blank `scenarioId` or `qualifierName` the route may read as absent would widen the unassign.
        if not scenario_id.strip():
            raise ValueError('scenario_id must name a scenario; it is blank')
        filters: dict[str, Union[str, Sequence[str]]] = {'scenarioId': scenario_id}
        if qualifier_name is not None:
            if not qualifier_name.strip():
                raise ValueError('qualifier_name must name a qualifier, or be None for every qualifier; it is blank')
            filters['qualifierName'] = qualifier_name

        if wells is not None:
            well_ids = self._split_ids(wells, 'wells')
            self._require_at_most(len(well_ids), WELL_FILTER_LIMIT, 'wells', 'well ids')
            filters['wells'] = well_ids

        if all_wells is not None:
            filters['allWells'] = str(all_wells).lower()

        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id, filters)
        return self._delete_responses(url, data=[])
