from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200
POST_LIMIT = 500
PUT_LIMIT = 500


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


    def get_actual_forecast_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of actual-forecast models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/actual-forecast'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_actual_forecast_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific actual-forecast model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/actual-forecast/{id}'


    def get_general_options_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of general options models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/general-options'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_general_options_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific general options model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/general-options/{id}'


    def get_reserves_categories_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of reserves categories models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/reserves-categories'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_reserves_categories_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific reserves categories model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/reserves-categories/{id}'


    def get_escalations_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of escalations models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/escalations'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_escalations_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific escalations model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/escalations/{id}'


    def get_differentials_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of differentials models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/differentials'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_differentials_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific differentials model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/differentials/{id}'


    def get_pricing_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of pricing models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/pricing'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_pricing_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific pricing model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/pricing/{id}'


    def get_ownership_reversions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of ownership reversions models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/ownership-reversions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_ownership_reversions_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific ownership reversions model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/ownership-reversions/{id}'


    def get_production_taxes_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of production taxes models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/production-taxes'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_production_taxes_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific production taxes model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/production-taxes/{id}'


    def get_riskings_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of riskings models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/riskings'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_riskings_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific riskings model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/riskings/{id}'


    def get_stream_properties_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of stream properties models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/stream-properties'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_stream_properties_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific stream properties model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/stream-properties/{id}'


    def get_expenses_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of expenses models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/expenses'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_expenses_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific expenses model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/expenses/{id}'


    def get_emissions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of emissions models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/emissions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_emissions_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific emissions model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/emissions/{id}'


    def get_fluid_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of fluid models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/fluid-models'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_fluid_models_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific fluid model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/fluid-models/{id}'


    def get_capex_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of capex models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/capex'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_capex_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific capex model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/capex/{id}'


    def get_date_settings_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of date settings models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/date-settings'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_date_settings_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific date settings model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/date-settings/{id}'


    def get_depreciation_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of depreciation models for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/econ-models/depreciation'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_depreciation_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url of a specific depreciation model for a specific project id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/econ-models/depreciation/{id}'


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


    def get_actual_forecast(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of actual-forecast models.
        """
        url = self.get_actual_forecast_url(project_id, filters)
        params = {'take': GET_LIMIT}
        actual_forecast = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(actual_forecast, order)


    def get_actual_forecast_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific actual-forecast model from its id.
        """
        url = self.get_actual_forecast_by_id_url(project_id, id)
        actual_forecast = self._get_items(url)

        return actual_forecast[0]


    def get_general_options(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of general options models.
        """
        url = self.get_general_options_url(project_id, filters)
        params = {'take': GET_LIMIT}
        general_options = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(general_options, order)


    def get_general_options_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific general options model from its id.
        """
        url = self.get_general_options_by_id_url(project_id, id)
        general_options = self._get_items(url)

        return general_options[0]


    def get_reserves_categories(self, project_id: str, filters: Optional[Dict[str, str]] = None
                                ) -> ItemList:
        """
        Returns a list of reserves categories models.
        """
        url = self.get_reserves_categories_url(project_id, filters)
        params = {'take': GET_LIMIT}
        reserves_categories = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(reserves_categories, order)


    def get_reserves_categories_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific reserves categories model from its id.
        """
        url = self.get_reserves_categories_by_id_url(project_id, id)
        reserves_categories = self._get_items(url)

        return reserves_categories[0]


    def get_escalations(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of escalations models.
        """
        url = self.get_escalations_url(project_id, filters)
        params = {'take': GET_LIMIT}
        escalations = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(escalations, order)


    def get_escalations_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific escalations model from its id.
        """
        url = self.get_escalations_by_id_url(project_id, id)
        escalations = self._get_items(url)

        return escalations[0]


    def get_differentials(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of differentials models.
        """
        url = self.get_differentials_url(project_id, filters)
        params = {'take': GET_LIMIT}
        differentials = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(differentials, order)


    def get_differentials_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific differentials model from its id.
        """
        url = self.get_differentials_by_id_url(project_id, id)
        differentials = self._get_items(url)

        return differentials[0]


    def get_pricing(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of pricing models.
        """
        url = self.get_pricing_url(project_id, filters)
        params = {'take': GET_LIMIT}
        pricing = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(pricing, order)


    def get_pricing_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific pricing model from its id.
        """
        url = self.get_pricing_by_id_url(project_id, id)
        pricing = self._get_items(url)

        return pricing[0]


    def get_ownership_reversions(self, project_id: str, filters: Optional[Dict[str, str]] = None
                                 ) -> ItemList:
        """
        Returns a list of ownership reversions models.
        """
        url = self.get_ownership_reversions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        ownership_reversions = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(ownership_reversions, order)


    def get_ownership_reversions_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific ownership reversions model from its id.
        """
        url = self.get_ownership_reversions_by_id_url(project_id, id)
        ownership_reversions = self._get_items(url)

        return ownership_reversions[0]


    def get_production_taxes(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of production taxes models.
        """
        url = self.get_production_taxes_url(project_id, filters)
        params = {'take': GET_LIMIT}
        production_taxes = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(production_taxes, order)


    def get_production_taxes_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific production taxes model from its id.
        """
        url = self.get_production_taxes_by_id_url(project_id, id)
        production_taxes = self._get_items(url)

        return production_taxes[0]


    def get_riskings(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of riskings models.
        """
        url = self.get_riskings_url(project_id, filters)
        params = {'take': GET_LIMIT}
        riskings = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(riskings, order)


    def get_riskings_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific riskings model from its id.
        """
        url = self.get_riskings_by_id_url(project_id, id)
        riskings = self._get_items(url)

        return riskings[0]


    def get_stream_properties(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of stream properties models.
        """
        url = self.get_stream_properties_url(project_id, filters)
        params = {'take': GET_LIMIT}
        stream_properties = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(stream_properties, order)


    def get_stream_properties_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific stream properties model from its id.
        """
        url = self.get_stream_properties_by_id_url(project_id, id)
        stream_properties = self._get_items(url)

        return stream_properties[0]


    def get_expenses(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of expenses models.
        """
        url = self.get_expenses_url(project_id, filters)
        params = {'take': GET_LIMIT}
        expenses = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(expenses, order)


    def get_expenses_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific expenses model from its id.
        """
        url = self.get_expenses_by_id_url(project_id, id)
        expenses = self._get_items(url)

        return expenses[0]


    def get_emissions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of emissions models.
        """
        url = self.get_emissions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        emissions = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(emissions, order)


    def get_emissions_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific emissions model from its id.
        """
        url = self.get_emissions_by_id_url(project_id, id)
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


    def get_fluid_models_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific fluid model from its id.
        """
        url = self.get_fluid_models_by_id_url(project_id, id)
        fluid_models = self._get_items(url)

        return fluid_models[0]


    def get_capex(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of capex models.
        """
        url = self.get_capex_url(project_id, filters)
        params = {'take': GET_LIMIT}
        capex = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(capex, order)


    def get_capex_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific capex model from its id.
        """
        url = self.get_capex_by_id_url(project_id, id)
        capex = self._get_items(url)

        return capex[0]


    def get_date_settings(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of date settings models.
        """
        url = self.get_date_settings_url(project_id, filters)
        params = {'take': GET_LIMIT}
        date_settings = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(date_settings, order)


    def get_date_settings_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific date settings model from its id.
        """
        url = self.get_date_settings_by_id_url(project_id, id)
        date_settings = self._get_items(url)

        return date_settings[0]


    def get_depreciation(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of depreciation models.
        """
        url = self.get_depreciation_url(project_id, filters)
        params = {'take': GET_LIMIT}
        depreciation = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1
        }
        return self._keysort(depreciation, order)


    def get_depreciation_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific depreciation model from its id.
        """
        url = self.get_depreciation_by_id_url(project_id, id)
        depreciation = self._get_items(url)

        return depreciation[0]
