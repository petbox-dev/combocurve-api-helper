from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200
POST_LIMIT = 500
PUT_LIMIT = 500


def _get_route(econ_model_type: str) -> Union[str, None]:
    for model in APIBase.ECON_MODELS:
        if model['econModelType'] == econ_model_type:
            return model['route']

    return None


class Models(APIBase):
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

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_econ_models_by_type_url(
            self, project_id: str, econ_model_type: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of econ models for a specific project id and model
        type. Allows `econModelType` passed as a parameter rather than calling
        a different function for each model type.
        """
        route = _get_route(econ_model_type)
        if route is None:
            raise ValueError(
                f'Invalid econ model type: {econ_model_type}\n'
                f'Valid types are: {", ".join(m["econModelType"] for m in APIBase.ECON_MODELS)}'
            )


        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/{route}'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
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

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_econ_model_assignments_by_type_by_id_url(
            self, project_id: str, econ_model_type: str, model_id: str,
            filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for assignments of a sepcific econ model for a
        specific project id and model type. Allows `econModelType` passed as a
        parameter rather than calling a different function for each model type.
        """
        base_url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        url = f'{base_url}/assignments'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_general_options_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of general options models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/general-options'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_general_options_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific general options model for a specific
        project id.
        """
        base_url = self.get_general_options_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_actual_forecast_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of actual-forecast models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/actual-forecast'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_actual_forecast_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific actual-forecast model for a specific
        project id.
        """
        base_url = self.get_actual_forecast_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_actual_forecast_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific actual-forecast model assignment for
        a specific project id.
        """
        base_url = self.get_actual_forecast_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_reserves_categories_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of reserves categories models for a specific
        project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/reserves-categories'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_reserves_categories_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific reserves categories model for a
        specific project id.
        """
        base_url = self.get_reserves_categories_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_reserves_categories_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific reserves categories model assignment
        for a specific project id.
        """
        base_url = self.get_reserves_categories_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_escalations_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of escalations models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/escalations'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_escalations_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific escalations model for a specific
        project id.
        """
        base_url = self.get_escalations_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_escalations_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific escalations model assignment for a
        specific project id.
        """
        base_url = self.get_escalations_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_differentials_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of differentials models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/differentials'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_differentials_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific differentials model for a specific
        project id.
        """
        base_url = self.get_differentials_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_differentials_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific differentials model assignment for a
        specific project id.
        """
        base_url = self.get_differentials_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_pricing_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of pricing models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/pricing'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_pricing_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific pricing model for a specific
        project id.
        """
        base_url = self.get_pricing_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_pricing_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific pricing model assignment for a
        specific project id.
        """
        base_url = self.get_pricing_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_ownership_reversions_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of ownership reversions models for a specific
        project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/ownership-reversions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_ownership_reversions_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific ownership reversions model for a
        specific project id.
        """
        base_url = self.get_ownership_reversions_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_ownership_reversions_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific ownership reversions model assignment
        for a specific project id.
        """
        base_url = self.get_ownership_reversions_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_production_taxes_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of production taxes models for a specific
        project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/production-taxes'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_production_taxes_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific production taxes model for a specific
        project id.
        """
        base_url = self.get_production_taxes_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_production_taxes_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific production taxes model assignment for
        a specific project id.
        """
        base_url = self.get_production_taxes_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_riskings_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of riskings models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/riskings'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_riskings_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific riskings model for a specific
        project id.
        """
        base_url = self.get_riskings_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_riskings_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific riskings model assignment for a
        specific project id.
        """
        base_url = self.get_riskings_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_stream_properties_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of stream properties models for a specific
        project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/stream-properties'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_stream_properties_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific stream properties model for a
        specific project id.
        """
        base_url = self.get_stream_properties_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_stream_properties_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific stream properties model assignment
        for a specific project id.
        """
        base_url = self.get_stream_properties_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_expenses_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of expenses models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/expenses'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_expenses_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific expenses model for a specific
        project id.
        """
        base_url = self.get_expenses_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_expenses_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific expenses model assignment for a
        specific project id.
        """
        base_url = self.get_expenses_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_emissions_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of emissions models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/emissions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_emissions_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific emissions model for a specific
        project id.
        """
        base_url = self.get_emissions_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_emissions_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific emissions model assignment for a
        specific project id.
        """
        base_url = self.get_emissions_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_fluid_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of fluid models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/fluid-models'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_fluid_models_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific fluid model for a specific
        project id.
        """
        base_url = self.get_fluid_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_fluid_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific fluid model assignment for a specific
        project id.
        """
        base_url = self.get_fluid_models_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_capex_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of capex models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/capex'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_capex_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific capex model for a specific
        project id.
        """
        base_url = self.get_capex_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_capex_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific capex model assignment for a specific
        project id.
        """
        base_url = self.get_capex_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_date_settings_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of date settings models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/date-settings'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_date_settings_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific date settings model for a specific
        project id.
        """
        base_url = self.get_date_settings_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_date_settings_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific date settings model assignment for a
        specific project id.
        """
        base_url = self.get_date_settings_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


    def get_depreciation_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of depreciation models for a specific project id.
        """
        base_url = self.get_econ_models_url(project_id)
        url = f'{base_url}/depreciation'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_depreciation_model_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific depreciation model for a specific
        project id.
        """
        base_url = self.get_depreciation_models_url(project_id)
        return f'{base_url}/{model_id}'


    def get_depreciation_assignments_by_id_url(self, project_id: str, model_id: str) -> str:
        """
        Returns the API url of a specific depreciation model assignment for a
        specific project id.
        """
        base_url = self.get_depreciation_model_by_id_url(project_id, model_id)
        return f'{base_url}/assignments'


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

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(econ_models, order)


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

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(econ_models, order)


    def get_econ_model_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str) -> Item:
        """
        Returns a specific econ model from its type and id. Allows
        `econModelType` passed as a parameter rather than calling a different
        function for each model type.
        """
        url = self.get_econ_model_by_type_by_id_url(project_id, econ_model_type, model_id)
        econ_models = self._get_items(url)

        return econ_models[0]


    def get_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str) -> Item:
        """
        Returns a specific econ model assignment from its type and id. Allows
        `econModelType` passed as a parameter rather than calling a different
        function for each model type.
        """
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        econ_models = self._get_items(url)

        return econ_models[0]


    def get_general_options_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of general options models.
        """
        url = self.get_general_options_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        general_options = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(general_options, order)


    def get_general_options_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific general options model from its id.
        """
        url = self.get_general_options_model_by_id_url(project_id, model_id)
        general_options = self._get_items(url)

        return general_options[0]


    def get_actual_forecast_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of actual-forecast models.
        """
        url = self.get_actual_forecast_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        actual_forecast = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(actual_forecast, order)


    def get_actual_forecast_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific actual-forecast model from its id.
        """
        url = self.get_actual_forecast_model_by_id_url(project_id, model_id)
        actual_forecast = self._get_items(url)

        return actual_forecast[0]


    def get_actual_forecast_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific actual-forecast model assignment from its id.
        """
        url = self.get_actual_forecast_assignments_by_id_url(project_id, model_id)
        actual_forecast = self._get_items(url)

        return actual_forecast[0]


    def get_reserves_categories_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of reserves categories models.
        """
        url = self.get_reserves_categories_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        reserves_categories = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(reserves_categories, order)


    def get_reserves_categories_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific reserves categories model from its id.
        """
        url = self.get_reserves_categories_model_by_id_url(project_id, model_id)
        reserves_categories = self._get_items(url)

        return reserves_categories[0]


    def get_reserves_categories_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific reserves categories model assignment from its id.
        """
        url = self.get_reserves_categories_assignments_by_id_url(project_id, model_id)
        reserves_categories = self._get_items(url)

        return reserves_categories[0]


    def get_escalation_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of escalations models.
        """
        url = self.get_escalations_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        escalations = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(escalations, order)


    def get_escalations_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific escalations model from its id.
        """
        url = self.get_escalations_model_by_id_url(project_id, model_id)
        escalations = self._get_items(url)

        return escalations[0]


    def get_escalations_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific escalations model assignment from its id.
        """
        url = self.get_escalations_assignments_by_id_url(project_id, model_id)
        escalations = self._get_items(url)

        return escalations[0]


    def get_differential_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of differentials models.
        """
        url = self.get_differentials_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        differentials = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(differentials, order)


    def get_differentials_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific differentials model from its id.
        """
        url = self.get_differentials_model_by_id_url(project_id, model_id)
        differentials = self._get_items(url)

        return differentials[0]


    def get_differentials_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific differentials model assignment from its id.
        """
        url = self.get_differentials_assignments_by_id_url(project_id, model_id)
        differentials = self._get_items(url)

        return differentials[0]


    def get_pricing_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of pricing models.
        """
        url = self.get_pricing_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        pricing = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(pricing, order)


    def get_pricing_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific pricing model from its id.
        """
        url = self.get_pricing_model_by_id_url(project_id, model_id)
        pricing = self._get_items(url)

        return pricing[0]


    def get_pricing_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific pricing model assignment from its id.
        """
        url = self.get_pricing_assignments_by_id_url(project_id, model_id)
        pricing = self._get_items(url)

        return pricing[0]


    def get_ownership_reversions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of ownership reversions models.
        """
        url = self.get_ownership_reversions_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        ownership_reversions = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(ownership_reversions, order)


    def get_ownership_reversions_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific ownership reversions model from its id.
        """
        url = self.get_ownership_reversions_model_by_id_url(project_id, model_id)
        ownership_reversions = self._get_items(url)

        return ownership_reversions[0]


    def get_ownership_reversions_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific ownership reversions model assignment from its id.
        """
        url = self.get_ownership_reversions_assignments_by_id_url(project_id, model_id)
        ownership_reversions = self._get_items(url)

        return ownership_reversions[0]


    def get_production_taxe_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of production taxes models.
        """
        url = self.get_production_taxes_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        production_taxes = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(production_taxes, order)


    def get_production_taxes_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific production taxes model from its id.
        """
        url = self.get_production_taxes_model_by_id_url(project_id, model_id)
        production_taxes = self._get_items(url)

        return production_taxes[0]


    def get_production_taxes_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific production taxes model assignment from its id.
        """
        url = self.get_production_taxes_assignments_by_id_url(project_id, model_id)
        production_taxes = self._get_items(url)

        return production_taxes[0]


    def get_risking_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of riskings models.
        """
        url = self.get_riskings_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        riskings = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(riskings, order)


    def get_riskings_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific riskings model from its id.
        """
        url = self.get_riskings_model_by_id_url(project_id, model_id)
        riskings = self._get_items(url)

        return riskings[0]


    def get_riskings_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific riskings model assignment from its id.
        """
        url = self.get_riskings_assignments_by_id_url(project_id, model_id)
        riskings = self._get_items(url)

        return riskings[0]


    def get_stream_propertie_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of stream properties models.
        """
        url = self.get_stream_properties_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        stream_properties = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(stream_properties, order)


    def get_stream_properties_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific stream properties model from its id.
        """
        url = self.get_stream_properties_model_by_id_url(project_id, model_id)
        stream_properties = self._get_items(url)

        return stream_properties[0]


    def get_stream_properties_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific stream properties model assignment from its id.
        """
        url = self.get_stream_properties_assignments_by_id_url(project_id, model_id)
        stream_properties = self._get_items(url)

        return stream_properties[0]


    def get_expense_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of expenses models.
        """
        url = self.get_expenses_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        expenses = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(expenses, order)


    def get_expenses_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific expenses model from its id.
        """
        url = self.get_expenses_model_by_id_url(project_id, model_id)
        expenses = self._get_items(url)

        return expenses[0]


    def get_expenses_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific expenses model assignment from its id.
        """
        url = self.get_expenses_assignments_by_id_url(project_id, model_id)
        expenses = self._get_items(url)

        return expenses[0]


    def get_emission_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of emissions models.
        """
        url = self.get_emissions_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        emissions = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(emissions, order)


    def get_emissions_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific emissions model from its id.
        """
        url = self.get_emissions_model_by_id_url(project_id, model_id)
        emissions = self._get_items(url)

        return emissions[0]


    def get_emissions_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific emissions model assignment from its id.
        """
        url = self.get_emissions_assignments_by_id_url(project_id, model_id)
        emissions = self._get_items(url)

        return emissions[0]


    def get_fluid_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of fluid models.
        """
        url = self.get_fluid_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        fluid_models = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(fluid_models, order)


    def get_fluid_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific fluid model from its id.
        """
        url = self.get_fluid_models_by_id_url(project_id, model_id)
        fluid_models = self._get_items(url)

        return fluid_models[0]


    def get_fluid_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific fluid model assignment from its id.
        """
        url = self.get_fluid_assignments_by_id_url(project_id, model_id)
        fluid_models = self._get_items(url)

        return fluid_models[0]


    def get_capex(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of capex models.
        """
        url = self.get_capex_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        capex = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(capex, order)


    def get_capex_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific capex model from its id.
        """
        url = self.get_capex_model_by_id_url(project_id, model_id)
        capex = self._get_items(url)

        return capex[0]


    def get_capex_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific capex model assignment from its id.
        """
        url = self.get_capex_assignments_by_id_url(project_id, model_id)
        capex = self._get_items(url)

        return capex[0]


    def get_date_settings(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of date settings models.
        """
        url = self.get_date_settings_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        date_settings = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(date_settings, order)


    def get_date_settings_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific date settings model from its id.
        """
        url = self.get_date_settings_model_by_id_url(project_id, model_id)
        date_settings = self._get_items(url)

        return date_settings[0]


    def get_date_settings_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific date settings model assignment from its id.
        """
        url = self.get_date_settings_assignments_by_id_url(project_id, model_id)
        date_settings = self._get_items(url)

        return date_settings[0]


    def get_depreciation(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of depreciation models.
        """
        url = self.get_depreciation_models_url(project_id, filters)
        params = {'take': GET_LIMIT}
        depreciation = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(depreciation, order)


    def get_depreciation_model_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific depreciation model from its id.
        """
        url = self.get_depreciation_model_by_id_url(project_id, model_id)
        depreciation = self._get_items(url)

        return depreciation[0]


    def get_depreciation_assignments_by_id(self, project_id: str, model_id: str) -> Item:
        """
        Returns a specific depreciation model assignment from its id.
        """
        url = self.get_depreciation_assignments_by_id_url(project_id, model_id)
        depreciation = self._get_items(url)

        return depreciation[0]
