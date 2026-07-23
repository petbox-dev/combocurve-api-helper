from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from requests.structures import CaseInsensitiveDict

from .base import APIBase, Item, ItemList, WriteResponse


GET_LIMIT = 1000
POST_PATCH_PUT_LIMIT = 1000


class Wells(APIBase):
    ######
    # URLs
    ######

    def get_company_wells_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for company wells.
        """
        url = f'{self.API_BASE_URL}/wells'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_company_well_by_id_url(self, well_id: str) -> str:
        """
        Returns the API url for a specific company well from its well id.
        """
        return f'{self.API_BASE_URL}/wells/{well_id}'

    def get_project_company_wells_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for project company wells scoped from the
        project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/company-wells'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_project_company_well_by_id_url(self, project_id: str, well_id: str) -> str:
        """
        Returns the API url for a specific project company well from its
        well id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/company-wells/{well_id}'

    def get_project_wells_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for project wells scoped from the project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/wells'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_project_well_by_id_url(self, project_id: str, well_id: str) -> str:
        """
        Returns the API url for a specific project well from its well id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/wells/{well_id}'

    def get_well_comments_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for well comments.
        """
        url = f'{self.API_BASE_URL}/well-comments'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    ###########
    # API calls
    ###########

    # Company Wells

    def get_company_wells(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company wells.

        https://docs.api.combocurve.com/api/get-wells
        """
        url = self.get_company_wells_url(filters)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(wells, order)

    def post_company_wells(self, data: ItemList) -> List[WriteResponse]:
        """
        Creates a list of company wells.

        https://docs.api.combocurve.com/api/post-wells
        """
        url = self.get_company_wells_url()
        wells = cast(List[WriteResponse], self._post_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def put_company_wells(self, data: ItemList) -> List[WriteResponse]:
        """
        Upserts a list of company wells.

        https://docs.api.combocurve.com/api/put-wells
        """
        url = self.get_company_wells_url()
        wells = cast(List[WriteResponse], self._put_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def patch_company_wells(self, data: ItemList) -> List[WriteResponse]:
        """
        Updates a list of company wells.

        https://docs.api.combocurve.com/api/patch-wells
        """
        url = self.get_company_wells_url()
        wells = cast(List[WriteResponse], self._patch_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def delete_company_wells(
        self,
        project_id: str,
        chosen_id: Optional[str] = None,
        data_source: Optional[str] = None,
        well_id: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes a list of company wells.

        https://docs.api.combocurve.com/api/delete-wells

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        if (chosen_id or data_source or well_id) is None:
            raise ValueError('Must provide at least one of chosen_id, data_source, or well_id')

        filters: Dict[str, str] = {}
        if chosen_id is not None:
            filters['chosenID'] = chosen_id

        if data_source is not None:
            filters['dataSource'] = data_source

        if well_id is not None:
            filters['id'] = well_id

        url = self.get_company_wells_url(filters)
        wells = self._delete_responses(url, data=[])

        headers = wells[0].headers

        return headers

    def get_company_well_by_id(self, well_id: str) -> Item:
        """
        Returns a specific company well from its well id.

        https://docs.api.combocurve.com/api/get-well-by-id
        """
        url = self.get_company_well_by_id_url(well_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]

    def put_company_well_by_id(self, well_id: str, data: Item) -> List[WriteResponse]:
        """
        Upserts a specific company well from its well id.

        https://docs.api.combocurve.com/api/put-well-by-id
        """
        url = self.get_company_well_by_id_url(well_id)
        wells = cast(List[WriteResponse], self._put_items(url, [data]))

        return wells

    def patch_company_well_by_id(self, well_id: str, data: Item) -> List[WriteResponse]:
        """
        Updates a specific company well from its well id.

        https://docs.api.combocurve.com/api/patch-well-by-id
        """
        url = self.get_company_well_by_id_url(well_id)
        wells = cast(List[WriteResponse], self._patch_items(url, [data]))

        return wells

    def delete_company_well_by_id(self, well_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific company well from its well id.

        https://docs.api.combocurve.com/api/delete-well-by-id

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        url = self.get_company_well_by_id_url(well_id)
        wells = self._delete_responses(url, data=[])

        headers = wells[0].headers

        return headers

    # Project Company Wells

    def get_project_company_wells(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of project company wells scoped from the project's id.

        https://docs.api.combocurve.com/api/get-project-company-wells
        """
        url = self.get_project_company_wells_url(project_id, filters)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(wells, order)

    def post_project_company_wells(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates a list of project company wells.

        https://docs.api.combocurve.com/api/post-project-company-wells
        """
        url = self.get_project_company_wells_url(project_id)
        wells = cast(List[WriteResponse], self._post_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def delete_project_company_wells(
        self,
        project_id: str,
        chosen_id: Optional[str] = None,
        data_source: Optional[str] = None,
        well_id: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes a list of project company wells.

        https://docs.api.combocurve.com/api/delete-project-company-wells

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        if (chosen_id or data_source or well_id) is None:
            raise ValueError('Must provide at least one of chosen_id, data_source, or well_id')

        filters: Dict[str, str] = {}
        if chosen_id is not None:
            filters['chosenID'] = chosen_id

        if data_source is not None:
            filters['dataSource'] = data_source

        if well_id is not None:
            filters['id'] = well_id

        url = self.get_project_company_wells_url(project_id, filters)
        wells = self._delete_responses(url, data=[])

        headers = wells[0].headers

        return headers

    def get_project_company_well_by_id(self, project_id: str, well_id: str) -> Item:
        """
        Returns a specific project company well from its well id.

        https://docs.api.combocurve.com/api/get-project-company-well-by-id
        """
        url = self.get_project_company_well_by_id_url(project_id, well_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]

    # Project Wells

    def get_project_wells(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/api/get-project-wells
        """
        url = self.get_project_wells_url(project_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(wells, order)

    def post_project_wells(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/api/post-projects-wells
        """
        url = self.get_project_wells_url(project_id)
        wells = cast(List[WriteResponse], self._post_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def put_project_wells(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/api/put-projects-wells
        """
        url = self.get_project_wells_url(project_id)
        wells = cast(List[WriteResponse], self._put_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def patch_project_wells(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Updates a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/api/patch-project-wells
        """
        url = self.get_project_wells_url(project_id)
        wells = cast(List[WriteResponse], self._patch_items(url, data, POST_PATCH_PUT_LIMIT))

        return wells

    def delete_project_wells(
        self,
        project_id: str,
        chosen_id: Optional[str] = None,
        data_source: Optional[str] = None,
        well_id: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
                Deletes a list of project wells scoped from the project's id.
        F
                https://docs.api.combocurve.com/api/delete-project-wells

                Returns the headers from the delete response where 'X-Delete-Count' is
                the number of wells deleted.
        """
        if (chosen_id or data_source or well_id) is None:
            raise ValueError('Must provide at least one of chosen_id, data_source, or well_id')

        filters: Dict[str, str] = {}
        if chosen_id is not None:
            filters['chosenID'] = chosen_id

        if data_source is not None:
            filters['dataSource'] = data_source

        if well_id is not None:
            filters['id'] = well_id

        url = self.get_project_wells_url(project_id, filters)
        wells = self._delete_responses(url, data=[])

        headers = wells[0].headers

        return headers

    def get_project_well_by_id(self, project_id: str, well_id: str) -> Item:
        """
        Returns a specific project well from its well id.

        https://docs.api.combocurve.com/api/get-project-well-by-id
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]

    def put_project_well_by_id(self, project_id: str, well_id: str, data: Item) -> List[WriteResponse]:
        """
        Upserts a specific project well from its well id.

        https://docs.api.combocurve.com/api/put-projects-wells-by-id
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        wells = cast(List[WriteResponse], self._put_items(url, [data]))

        return wells

    def patch_project_well_by_id(self, project_id: str, well_id: str, data: Item) -> List[WriteResponse]:
        """
        Updates a specific project well from its well id.

        https://docs.api.combocurve.com/api/patch-project-well-by-id
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        wells = cast(List[WriteResponse], self._patch_items(url, [data]))

        return wells

    def delete_project_well_by_id(self, project_id: str, well_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific project well from its well id.

        https://docs.api.combocurve.com/api/delete-project-well-by-id

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        wells = self._delete_responses(url, data=[])

        headers = wells[0].headers

        return headers

    def get_well_comments(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of well comments.

        https://docs.api.combocurve.com/api/get-well-comments

        Example response:
        [
            {
                "commentedAt": "2020-01-01",
                "commentedBy": "string",
                "forecast": "string",
                "project": "string",
                "text": "string",
                "well": "string"
            }
        ]
        """
        url = self.get_well_comments_url(filters)
        params = {'take': GET_LIMIT}
        well_comments = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(well_comments, order)


wells_response = """
        Example response:
        [
            {
                "dataSource": "string",
                "abstract": "string",
                "acreSpacing": 123.45,
                "allocationType": "string",
                "api10": "string",
                "api12": "string",
                "api14": "string",
                "ariesId": "5e272d38b78910dd2a1bd691",
                "azimuth": 123.45,
                "basin": "string",
                "bg": 123.45,
                "block": "string",
                "bo": 123.45,
                "bubblePointPress": 123.45,
                "casingId": 123.45,
                "chokeSize": 123.45,
                "chosenID": "string",
                "chosenKeyID": "string",
                "completionDesign": "string",
                "completionEndDate": "2020-01-01",
                "completionStartDate": "2020-01-01",
                "copied": true,
                "copiedFrom": "string",
                "country": "string",
                "county": "string",
                "createdAt": "2020-01-01",
                "cumBoe": 123.45,
                "cumBoePerPerforatedInterval": 123.45,
                "cumGas": 123.45,
                "cumGasPerPerforatedInterval": 123.45,
                "cumGor": 123.45,
                "cumMmcfge": 123.45,
                "cumMmcfgePerPerforatedInterval": 123.45,
                "cumOil": 123.45,
                "cumOilPerPerforatedInterval": 123.45,
                "cumWater": 123.45,
                "cumWaterPerPerforatedInterval": 123.45,
                "currentOperator": "string",
                "currentOperatorAlias": "string",
                "currentOperatorCode": "string",
                "currentOperatorTicker": "string",
                "customBool0": true,
                "customBool1": true,
                "customBool2": true,
                "customBool3": true,
                "customBool4": true,
                "customDate0": "2020-01-01",
                "customDate1": "2020-01-01",
                "customDate2": "2020-01-01",
                "customDate3": "2020-01-01",
                "customDate4": "2020-01-01",
                "customDate5": "2020-01-01",
                "customDate6": "2020-01-01",
                "customDate7": "2020-01-01",
                "customDate8": "2020-01-01",
                "customDate9": "2020-01-01",
                "customDate10": "2020-01-01",
                "customDate11": "2020-01-01",
                "customDate12": "2020-01-01",
                "customDate13": "2020-01-01",
                "customDate14": "2020-01-01",
                "customDate15": "2020-01-01",
                "customDate16": "2020-01-01",
                "customDate17": "2020-01-01",
                "customDate18": "2020-01-01",
                "customDate19": "2020-01-01",
                "customNumber0": 123.45,
                "customNumber1": 123.45,
                "customNumber10": 123.45,
                "customNumber11": 123.45,
                "customNumber12": 123.45,
                "customNumber13": 123.45,
                "customNumber14": 123.45,
                "customNumber15": 123.45,
                "customNumber16": 123.45,
                "customNumber17": 123.45,
                "customNumber18": 123.45,
                "customNumber19": 123.45,
                "customNumber2": 123.45,
                "customNumber3": 123.45,
                "customNumber4": 123.45,
                "customNumber5": 123.45,
                "customNumber6": 123.45,
                "customNumber7": 123.45,
                "customNumber8": 123.45,
                "customNumber9": 123.45,
                "customString0": "string",
                "customString1": "string",
                "customString10": "string",
                "customString11": "string",
                "customString12": "string",
                "customString13": "string",
                "customString14": "string",
                "customString15": "string",
                "customString16": "string",
                "customString17": "string",
                "customString18": "string",
                "customString19": "string",
                "customString20": "string",
                "customString21": "string",
                "customString22": "string",
                "customString23": "string",
                "customString24": "string",
                "customString25": "string",
                "customString26": "string",
                "customString27": "string",
                "customString28": "string",
                "customString29": "string",
                "customString30": "string",
                "customString31": "string",
                "customString32": "string",
                "customString33": "string",
                "customString34": "string",
                "customString2": "string",
                "customString3": "string",
                "customString4": "string",
                "customString5": "string",
                "customString6": "string",
                "customString7": "string",
                "customString8": "string",
                "customString9": "string",
                "dataPool": "string",
                "dataSourceCustomName": "string",
                "dateRigRelease": "2020-01-01",
                "dewPointPress": 123.45,
                "distanceFromBaseOfZone": 123.45,
                "distanceFromTopOfZone": 123.45,
                "district": "string",
                "drainageArea": 123.45,
                "drillEndDate": "2020-01-01",
                "drillStartDate": "2020-01-01",
                "drillinginfoId": "5e272d38b78910dd2a1bd691",
                "elevation": 123.45,
                "elevationType": "string",
                "field": "string",
                "first12Boe": 123.45,
                "first12BoePerPerforatedInterval": 123.45,
                "first12Gas": 123.45,
                "first12GasPerPerforatedInterval": 123.45,
                "first12Gor": 123.45,
                "first12Mmcfge": 123.45,
                "first12MmcfgePerPerforatedInterval": 123.45,
                "first12Oil": 123.45,
                "first12OilPerPerforatedInterval": 123.45,
                "first12Water": 123.45,
                "first12WaterPerPerforatedInterval": 123.45,
                "first6Boe": 123.45,
                "first6BoePerPerforatedInterval": 123.45,
                "first6Gas": 123.45,
                "first6GasPerPerforatedInterval": 123.45,
                "first6Gor": 123.45,
                "first6Mmcfge": 123.45,
                "first6MmcfgePerPerforatedInterval": 123.45,
                "first6Oil": 123.45,
                "first6OilPerPerforatedInterval": 123.45,
                "first6Water": 123.45,
                "first6WaterPerPerforatedInterval": 123.45,
                "firstAdditiveVolume": 123.45,
                "firstClusterCount": 123.45,
                "firstFluidPerPerforatedInterval": 123.45,
                "firstFluidVolume": 123.45,
                "firstFracVendor": "string",
                "firstMaxInjectionPressure": 123.45,
                "firstMaxInjectionRate": 123.45,
                "firstProdDate": "2020-01-01",
                "firstProdDateDailyCalc": "2020-01-01",
                "firstProdDateMonthlyCalc": "2020-01-01",
                "firstPropWeight": 123.45,
                "firstProppantPerFluid": 123.45,
                "firstProppantPerPerforatedInterval": 123.45,
                "firstStageCount": 123.45,
                "firstTestFlowTbgPress": 123.45,
                "firstTestGasVol": 123.45,
                "firstTestGor": 123.45,
                "firstTestOilVol": 123.45,
                "firstTestWaterVol": 123.45,
                "firstTreatmentType": "string",
                "flowPath": "string",
                "fluidType": "string",
                "footageInLandingZone": 123.45,
                "formationThicknessMean": 123.45,
                "fractureConductivity": 123.45,
                "gasAnalysisDate": "2020-01-01",
                "gasC1": 123.45,
                "gasC2": 123.45,
                "gasC3": 123.45,
                "gasCo2": 123.45,
                "gasGatherer": "string",
                "gasH2": 123.45,
                "gasH2o": 123.45,
                "gasH2s": 123.45,
                "gasHe": 123.45,
                "gasIc4": 123.45,
                "gasIc5": 123.45,
                "gasN2": 123.45,
                "gasNc10": 123.45,
                "gasNc4": 123.45,
                "gasNc5": 123.45,
                "gasNc6": 123.45,
                "gasNc7": 123.45,
                "gasNc8": 123.45,
                "gasNc9": 123.45,
                "gasO2": 123.45,
                "gasSpecificGravity": 123.45,
                "generic": true,
                "grossPerforatedInterval": 123.45,
                "groundElevation": 123.45,
                "hasDaily": true,
                "hasMonthly": true,
                "heelLatitude": 123.45,
                "heelLongitude": 123.45,
                "holeDirection": "string",
                "horizontalSpacing": 123.45,
                "hzWellSpacingAnyZone": 123.45,
                "hzWellSpacingSameZone": 123.45,
                "id": "5e272d38b78910dd2a1bd691",
                "ihsId": "5e272d38b78910dd2a1bd691",
                "initialRespress": 123.45,
                "initialRestemp": 123.45,
                "inptID": "string",
                "landingZone": "string",
                "landingZoneBase": 123.45,
                "landingZoneTop": 123.45,
                "last12Boe": 123.45,
                "last12BoePerPerforatedInterval": 123.45,
                "last12Gas": 123.45,
                "last12GasPerPerforatedInterval": 123.45,
                "last12Gor": 123.45,
                "last12Mmcfge": 123.45,
                "last12MmcfgePerPerforatedInterval": 123.45,
                "last12Oil": 123.45,
                "last12OilPerPerforatedInterval": 123.45,
                "last12Water": 123.45,
                "last12WaterPerPerforatedInterval": 123.45,
                "lastMonthBoe": 123.45,
                "lastMonthBoePerPerforatedInterval": 123.45,
                "lastMonthGas": 123.45,
                "lastMonthGasPerPerforatedInterval": 123.45,
                "lastMonthGor": 123.45,
                "lastMonthMmcfge": 123.45,
                "lastMonthMmcfgePerPerforatedInterval": 123.45,
                "lastMonthOil": 123.45,
                "lastMonthOilPerPerforatedInterval": 123.45,
                "lastMonthWater": 123.45,
                "lastMonthWaterPerPerforatedInterval": 123.45,
                "lastProdDateDaily": "2020-01-01",
                "lastProdDateMonthly": "2020-01-01",
                "lateralLength": 123.45,
                "leaseName": "string",
                "leaseNumber": "string",
                "lowerPerforation": 123.45,
                "matrixPermeability": 123.45,
                "measuredDepth": 123.45,
                "monthsProduced": 123.45,
                "mostRecentImportDate": "2020-01-01",
                "mostRecentImportDesc": "string",
                "mostRecentImportType": "string",
                "nglGatherer": "string",
                "numTreatmentRecords": 123.45,
                "oilApiGravity": 123.45,
                "oilGatherer": "string",
                "oilSpecificGravity": 123.45,
                "padName": "string",
                "parentChildAnyZone": "string",
                "parentChildSameZone": "string",
                "percentInZone": 123.45,
                "perfLateralLength": 123.45,
                "permitDate": "2020-01-01",
                "phdwinId": "5e272d38b78910dd2a1bd691",
                "play": "string",
                "porosity": 123.45,
                "previousOperator": "string",
                "previousOperatorAlias": "string",
                "previousOperatorCode": "string",
                "previousOperatorTicker": "string",
                "primaryProduct": "string",
                "prmsReservesCategory": "string",
                "prmsReservesSubCategory": "string",
                "prmsResourcesClass": "string",
                "productionMethod": "string",
                "proppantMeshSize": "string",
                "proppantType": "string",
                "range": "string",
                "recoveryMethod": "string",
                "refracAdditiveVolume": 123.45,
                "refracClusterCount": 123.45,
                "refracDate": "2020-01-01",
                "refracFluidPerPerforatedInterval": 123.45,
                "refracFluidVolume": 123.45,
                "refracFracVendor": "string",
                "refracMaxInjectionPressure": 123.45,
                "refracMaxInjectionRate": 123.45,
                "refracPropWeight": 123.45,
                "refracProppantPerFluid": 123.45,
                "refracProppantPerPerforatedInterval": 123.45,
                "refracStageCount": 123.45,
                "refracTreatmentType": "string",
                "rig": "string",
                "rs": 123.45,
                "rsegId": "5e272d38b78910dd2a1bd691",
                "scope": "string",
                "section": "string",
                "sg": 123.45,
                "so": 123.45,
                "spudDate": "2020-01-01",
                "stageSpacing": 123.45,
                "state": "string",
                "status": "string",
                "subplay": "string",
                "surfaceLatitude": 123.45,
                "surfaceLongitude": 123.45,
                "survey": "string",
                "sw": 123.45,
                "targetFormation": "string",
                "tgsId": "5e272d38b78910dd2a1bd691",
                "spgciId": "5e272d38b78910dd2a1bd691",
                "thickness": 123.45,
                "til": "2020-01-01",
                "toeInLandingZone": "string",
                "toeLatitude": 123.45,
                "toeLongitude": 123.45,
                "toeUp": "string",
                "totalAdditiveVolume": 123.45,
                "totalClusterCount": 123.45,
                "totalFluidPerPerforatedInterval": 123.45,
                "totalFluidVolume": 123.45,
                "totalPropWeight": 123.45,
                "totalProppantPerFluid": 123.45,
                "totalProppantPerPerforatedInterval": 123.45,
                "totalStageCount": 123.45,
                "township": "string",
                "trueVerticalDepth": 123.45,
                "tubingDepth": 123.45,
                "tubingId": 123.45,
                "typeCurveArea": "string",
                "updatedAt": "2020-01-01",
                "upperPerforation": 123.45,
                "verticalSpacing": 123.45,
                "vtWellSpacingAnyZone": 123.45,
                "vtWellSpacingSameZone": 123.45,
                "wellName": "string",
                "wellNumber": "string",
                "wellType": "string",
                "zi": 123.45,
                "beforeIncomeTaxCashFlow": 123.45,
                "econFirstProductionDate": "2020-01-01",
                "econRunDate": "2020-01-01",
                "gasBreakeven": 123.45,
                "gasShrunkEur": 123.45,
                "gasShrunkEurOverPll": 123.45,
                "hasDirectionalSurvey": true,
                "first_discount_cash_flow": 123.45,
                "irr": 123.45,
                "nglShrunkEur": 123.45,
                "nglShrunkEurOverPll": 123.45,
                "nriOil": 123.45,
                "oilBreakeven": 123.45,
                "oilShrunkEur": 123.45,
                "oilShrunkEurOverPll": 123.45,
                "payoutDuration": 123.45,
                "undiscountedRoi": 123.45,
                "wiOil": 123.45
            }
        ]
"""

well_response = """
        Example response:
        {
            "dataSource": "string",
            "abstract": "string",
            "acreSpacing": 123.45,
            "allocationType": "string",
            "api10": "string",
            "api12": "string",
            "api14": "string",
            "ariesId": "5e272d38b78910dd2a1bd691",
            "azimuth": 123.45,
            "basin": "string",
            "bg": 123.45,
            "block": "string",
            "bo": 123.45,
            "bubblePointPress": 123.45,
            "casingId": 123.45,
            "chokeSize": 123.45,
            "chosenID": "string",
            "chosenKeyID": "string",
            "completionDesign": "string",
            "completionEndDate": "2020-01-01",
            "completionStartDate": "2020-01-01",
            "copied": true,
            "copiedFrom": "string",
            "country": "string",
            "county": "string",
            "createdAt": "2020-01-01",
            "cumBoe": 123.45,
            "cumBoePerPerforatedInterval": 123.45,
            "cumGas": 123.45,
            "cumGasPerPerforatedInterval": 123.45,
            "cumGor": 123.45,
            "cumMmcfge": 123.45,
            "cumMmcfgePerPerforatedInterval": 123.45,
            "cumOil": 123.45,
            "cumOilPerPerforatedInterval": 123.45,
            "cumWater": 123.45,
            "cumWaterPerPerforatedInterval": 123.45,
            "currentOperator": "string",
            "currentOperatorAlias": "string",
            "currentOperatorCode": "string",
            "currentOperatorTicker": "string",
            "customBool0": true,
            "customBool1": true,
            "customBool2": true,
            "customBool3": true,
            "customBool4": true,
            "customDate0": "2020-01-01",
            "customDate1": "2020-01-01",
            "customDate2": "2020-01-01",
            "customDate3": "2020-01-01",
            "customDate4": "2020-01-01",
            "customDate5": "2020-01-01",
            "customDate6": "2020-01-01",
            "customDate7": "2020-01-01",
            "customDate8": "2020-01-01",
            "customDate9": "2020-01-01",
            "customDate10": "2020-01-01",
            "customDate11": "2020-01-01",
            "customDate12": "2020-01-01",
            "customDate13": "2020-01-01",
            "customDate14": "2020-01-01",
            "customDate15": "2020-01-01",
            "customDate16": "2020-01-01",
            "customDate17": "2020-01-01",
            "customDate18": "2020-01-01",
            "customDate19": "2020-01-01",
            "customNumber0": 123.45,
            "customNumber1": 123.45,
            "customNumber10": 123.45,
            "customNumber11": 123.45,
            "customNumber12": 123.45,
            "customNumber13": 123.45,
            "customNumber14": 123.45,
            "customNumber15": 123.45,
            "customNumber16": 123.45,
            "customNumber17": 123.45,
            "customNumber18": 123.45,
            "customNumber19": 123.45,
            "customNumber2": 123.45,
            "customNumber3": 123.45,
            "customNumber4": 123.45,
            "customNumber5": 123.45,
            "customNumber6": 123.45,
            "customNumber7": 123.45,
            "customNumber8": 123.45,
            "customNumber9": 123.45,
            "customString0": "string",
            "customString1": "string",
            "customString10": "string",
            "customString11": "string",
            "customString12": "string",
            "customString13": "string",
            "customString14": "string",
            "customString15": "string",
            "customString16": "string",
            "customString17": "string",
            "customString18": "string",
            "customString19": "string",
            "customString20": "string",
            "customString21": "string",
            "customString22": "string",
            "customString23": "string",
            "customString24": "string",
            "customString25": "string",
            "customString26": "string",
            "customString27": "string",
            "customString28": "string",
            "customString29": "string",
            "customString30": "string",
            "customString31": "string",
            "customString32": "string",
            "customString33": "string",
            "customString34": "string",
            "customString2": "string",
            "customString3": "string",
            "customString4": "string",
            "customString5": "string",
            "customString6": "string",
            "customString7": "string",
            "customString8": "string",
            "customString9": "string",
            "dataPool": "string",
            "dataSourceCustomName": "string",
            "dateRigRelease": "2020-01-01",
            "dewPointPress": 123.45,
            "distanceFromBaseOfZone": 123.45,
            "distanceFromTopOfZone": 123.45,
            "district": "string",
            "drainageArea": 123.45,
            "drillEndDate": "2020-01-01",
            "drillStartDate": "2020-01-01",
            "drillinginfoId": "5e272d38b78910dd2a1bd691",
            "elevation": 123.45,
            "elevationType": "string",
            "field": "string",
            "first12Boe": 123.45,
            "first12BoePerPerforatedInterval": 123.45,
            "first12Gas": 123.45,
            "first12GasPerPerforatedInterval": 123.45,
            "first12Gor": 123.45,
            "first12Mmcfge": 123.45,
            "first12MmcfgePerPerforatedInterval": 123.45,
            "first12Oil": 123.45,
            "first12OilPerPerforatedInterval": 123.45,
            "first12Water": 123.45,
            "first12WaterPerPerforatedInterval": 123.45,
            "first6Boe": 123.45,
            "first6BoePerPerforatedInterval": 123.45,
            "first6Gas": 123.45,
            "first6GasPerPerforatedInterval": 123.45,
            "first6Gor": 123.45,
            "first6Mmcfge": 123.45,
            "first6MmcfgePerPerforatedInterval": 123.45,
            "first6Oil": 123.45,
            "first6OilPerPerforatedInterval": 123.45,
            "first6Water": 123.45,
            "first6WaterPerPerforatedInterval": 123.45,
            "firstAdditiveVolume": 123.45,
            "firstClusterCount": 123.45,
            "firstFluidPerPerforatedInterval": 123.45,
            "firstFluidVolume": 123.45,
            "firstFracVendor": "string",
            "firstMaxInjectionPressure": 123.45,
            "firstMaxInjectionRate": 123.45,
            "firstProdDate": "2020-01-01",
            "firstProdDateDailyCalc": "2020-01-01",
            "firstProdDateMonthlyCalc": "2020-01-01",
            "firstPropWeight": 123.45,
            "firstProppantPerFluid": 123.45,
            "firstProppantPerPerforatedInterval": 123.45,
            "firstStageCount": 123.45,
            "firstTestFlowTbgPress": 123.45,
            "firstTestGasVol": 123.45,
            "firstTestGor": 123.45,
            "firstTestOilVol": 123.45,
            "firstTestWaterVol": 123.45,
            "firstTreatmentType": "string",
            "flowPath": "string",
            "fluidType": "string",
            "footageInLandingZone": 123.45,
            "formationThicknessMean": 123.45,
            "fractureConductivity": 123.45,
            "gasAnalysisDate": "2020-01-01",
            "gasC1": 123.45,
            "gasC2": 123.45,
            "gasC3": 123.45,
            "gasCo2": 123.45,
            "gasGatherer": "string",
            "gasH2": 123.45,
            "gasH2o": 123.45,
            "gasH2s": 123.45,
            "gasHe": 123.45,
            "gasIc4": 123.45,
            "gasIc5": 123.45,
            "gasN2": 123.45,
            "gasNc10": 123.45,
            "gasNc4": 123.45,
            "gasNc5": 123.45,
            "gasNc6": 123.45,
            "gasNc7": 123.45,
            "gasNc8": 123.45,
            "gasNc9": 123.45,
            "gasO2": 123.45,
            "gasSpecificGravity": 123.45,
            "generic": true,
            "grossPerforatedInterval": 123.45,
            "groundElevation": 123.45,
            "hasDaily": true,
            "hasMonthly": true,
            "heelLatitude": 123.45,
            "heelLongitude": 123.45,
            "holeDirection": "string",
            "horizontalSpacing": 123.45,
            "hzWellSpacingAnyZone": 123.45,
            "hzWellSpacingSameZone": 123.45,
            "id": "5e272d38b78910dd2a1bd691",
            "ihsId": "5e272d38b78910dd2a1bd691",
            "initialRespress": 123.45,
            "initialRestemp": 123.45,
            "inptID": "string",
            "landingZone": "string",
            "landingZoneBase": 123.45,
            "landingZoneTop": 123.45,
            "last12Boe": 123.45,
            "last12BoePerPerforatedInterval": 123.45,
            "last12Gas": 123.45,
            "last12GasPerPerforatedInterval": 123.45,
            "last12Gor": 123.45,
            "last12Mmcfge": 123.45,
            "last12MmcfgePerPerforatedInterval": 123.45,
            "last12Oil": 123.45,
            "last12OilPerPerforatedInterval": 123.45,
            "last12Water": 123.45,
            "last12WaterPerPerforatedInterval": 123.45,
            "lastMonthBoe": 123.45,
            "lastMonthBoePerPerforatedInterval": 123.45,
            "lastMonthGas": 123.45,
            "lastMonthGasPerPerforatedInterval": 123.45,
            "lastMonthGor": 123.45,
            "lastMonthMmcfge": 123.45,
            "lastMonthMmcfgePerPerforatedInterval": 123.45,
            "lastMonthOil": 123.45,
            "lastMonthOilPerPerforatedInterval": 123.45,
            "lastMonthWater": 123.45,
            "lastMonthWaterPerPerforatedInterval": 123.45,
            "lastProdDateDaily": "2020-01-01",
            "lastProdDateMonthly": "2020-01-01",
            "lateralLength": 123.45,
            "leaseName": "string",
            "leaseNumber": "string",
            "lowerPerforation": 123.45,
            "matrixPermeability": 123.45,
            "measuredDepth": 123.45,
            "monthsProduced": 123.45,
            "mostRecentImportDate": "2020-01-01",
            "mostRecentImportDesc": "string",
            "mostRecentImportType": "string",
            "nglGatherer": "string",
            "numTreatmentRecords": 123.45,
            "oilApiGravity": 123.45,
            "oilGatherer": "string",
            "oilSpecificGravity": 123.45,
            "padName": "string",
            "parentChildAnyZone": "string",
            "parentChildSameZone": "string",
            "percentInZone": 123.45,
            "perfLateralLength": 123.45,
            "permitDate": "2020-01-01",
            "phdwinId": "5e272d38b78910dd2a1bd691",
            "play": "string",
            "porosity": 123.45,
            "previousOperator": "string",
            "previousOperatorAlias": "string",
            "previousOperatorCode": "string",
            "previousOperatorTicker": "string",
            "primaryProduct": "string",
            "prmsReservesCategory": "string",
            "prmsReservesSubCategory": "string",
            "prmsResourcesClass": "string",
            "productionMethod": "string",
            "proppantMeshSize": "string",
            "proppantType": "string",
            "range": "string",
            "recoveryMethod": "string",
            "refracAdditiveVolume": 123.45,
            "refracClusterCount": 123.45,
            "refracDate": "2020-01-01",
            "refracFluidPerPerforatedInterval": 123.45,
            "refracFluidVolume": 123.45,
            "refracFracVendor": "string",
            "refracMaxInjectionPressure": 123.45,
            "refracMaxInjectionRate": 123.45,
            "refracPropWeight": 123.45,
            "refracProppantPerFluid": 123.45,
            "refracProppantPerPerforatedInterval": 123.45,
            "refracStageCount": 123.45,
            "refracTreatmentType": "string",
            "rig": "string",
            "rs": 123.45,
            "rsegId": "5e272d38b78910dd2a1bd691",
            "scope": "string",
            "section": "string",
            "sg": 123.45,
            "so": 123.45,
            "spudDate": "2020-01-01",
            "stageSpacing": 123.45,
            "state": "string",
            "status": "string",
            "subplay": "string",
            "surfaceLatitude": 123.45,
            "surfaceLongitude": 123.45,
            "survey": "string",
            "sw": 123.45,
            "targetFormation": "string",
            "tgsId": "5e272d38b78910dd2a1bd691",
            "spgciId": "5e272d38b78910dd2a1bd691",
            "thickness": 123.45,
            "til": "2020-01-01",
            "toeInLandingZone": "string",
            "toeLatitude": 123.45,
            "toeLongitude": 123.45,
            "toeUp": "string",
            "totalAdditiveVolume": 123.45,
            "totalClusterCount": 123.45,
            "totalFluidPerPerforatedInterval": 123.45,
            "totalFluidVolume": 123.45,
            "totalPropWeight": 123.45,
            "totalProppantPerFluid": 123.45,
            "totalProppantPerPerforatedInterval": 123.45,
            "totalStageCount": 123.45,
            "township": "string",
            "trueVerticalDepth": 123.45,
            "tubingDepth": 123.45,
            "tubingId": 123.45,
            "typeCurveArea": "string",
            "updatedAt": "2020-01-01",
            "upperPerforation": 123.45,
            "verticalSpacing": 123.45,
            "vtWellSpacingAnyZone": 123.45,
            "vtWellSpacingSameZone": 123.45,
            "wellName": "string",
            "wellNumber": "string",
            "wellType": "string",
            "zi": 123.45,
            "beforeIncomeTaxCashFlow": 123.45,
            "econFirstProductionDate": "2020-01-01",
            "econRunDate": "2020-01-01",
            "gasBreakeven": 123.45,
            "gasShrunkEur": 123.45,
            "gasShrunkEurOverPll": 123.45,
            "hasDirectionalSurvey": true,
            "first_discount_cash_flow": 123.45,
            "irr": 123.45,
            "nglShrunkEur": 123.45,
            "nglShrunkEurOverPll": 123.45,
            "nriOil": 123.45,
            "oilBreakeven": 123.45,
            "oilShrunkEur": 123.45,
            "oilShrunkEurOverPll": 123.45,
            "payoutDuration": 123.45,
            "undiscountedRoi": 123.45,
            "wiOil": 123.45
        }
"""

post_patch_put_wells_response = """
        Example data:
        [
            {
                "dataSource": "string",
                "abstract": "string",
                "acreSpacing": 123.45,
                "allocationType": "string",
                "api10": "string",
                "api12": "string",
                "api14": "string",
                "ariesId": "5e272d38b78910dd2a1bd691",
                "azimuth": 123.45,
                "basin": "string",
                "bg": 123.45,
                "block": "string",
                "bo": 123.45,
                "bubblePointPress": 123.45,
                "casingId": 123.45,
                "chokeSize": 123.45,
                "chosenID": "string",
                "chosenKeyID": "string",
                "completionDesign": "string",
                "completionEndDate": "2020-01-01",
                "completionStartDate": "2020-01-01",
                "country": "string",
                "county": "string",
                "currentOperator": "string",
                "currentOperatorAlias": "string",
                "currentOperatorCode": "string",
                "currentOperatorTicker": "string",
                "customBool0": true,
                "customBool1": true,
                "customBool2": true,
                "customBool3": true,
                "customBool4": true,
                "customDate0": "2020-01-01",
                "customDate1": "2020-01-01",
                "customDate2": "2020-01-01",
                "customDate3": "2020-01-01",
                "customDate4": "2020-01-01",
                "customDate5": "2020-01-01",
                "customDate6": "2020-01-01",
                "customDate7": "2020-01-01",
                "customDate8": "2020-01-01",
                "customDate9": "2020-01-01",
                "customDate10": "2020-01-01",
                "customDate11": "2020-01-01",
                "customDate12": "2020-01-01",
                "customDate13": "2020-01-01",
                "customDate14": "2020-01-01",
                "customDate15": "2020-01-01",
                "customDate16": "2020-01-01",
                "customDate17": "2020-01-01",
                "customDate18": "2020-01-01",
                "customDate19": "2020-01-01",
                "customNumber0": 123.45,
                "customNumber1": 123.45,
                "customNumber10": 123.45,
                "customNumber11": 123.45,
                "customNumber12": 123.45,
                "customNumber13": 123.45,
                "customNumber14": 123.45,
                "customNumber15": 123.45,
                "customNumber16": 123.45,
                "customNumber17": 123.45,
                "customNumber18": 123.45,
                "customNumber19": 123.45,
                "customNumber2": 123.45,
                "customNumber3": 123.45,
                "customNumber4": 123.45,
                "customNumber5": 123.45,
                "customNumber6": 123.45,
                "customNumber7": 123.45,
                "customNumber8": 123.45,
                "customNumber9": 123.45,
                "customString0": "string",
                "customString1": "string",
                "customString10": "string",
                "customString11": "string",
                "customString12": "string",
                "customString13": "string",
                "customString14": "string",
                "customString15": "string",
                "customString16": "string",
                "customString17": "string",
                "customString18": "string",
                "customString19": "string",
                "customString20": "string",
                "customString21": "string",
                "customString22": "string",
                "customString23": "string",
                "customString24": "string",
                "customString25": "string",
                "customString26": "string",
                "customString27": "string",
                "customString28": "string",
                "customString29": "string",
                "customString30": "string",
                "customString31": "string",
                "customString32": "string",
                "customString33": "string",
                "customString34": "string",
                "customString2": "string",
                "customString3": "string",
                "customString4": "string",
                "customString5": "string",
                "customString6": "string",
                "customString7": "string",
                "customString8": "string",
                "customString9": "string",
                "dataSourceCustomName": "string",
                "dateRigRelease": "2020-01-01",
                "dewPointPress": 123.45,
                "distanceFromBaseOfZone": 123.45,
                "distanceFromTopOfZone": 123.45,
                "district": "string",
                "drainageArea": 123.45,
                "drillEndDate": "2020-01-01",
                "drillStartDate": "2020-01-01",
                "drillinginfoId": "5e272d38b78910dd2a1bd691",
                "elevation": 123.45,
                "elevationType": "string",
                "field": "string",
                "firstAdditiveVolume": 123.45,
                "firstClusterCount": 123.45,
                "firstFluidVolume": 123.45,
                "firstFracVendor": "string",
                "firstMaxInjectionPressure": 123.45,
                "firstMaxInjectionRate": 123.45,
                "firstProdDate": "2020-01-01",
                "firstPropWeight": 123.45,
                "firstStageCount": 123.45,
                "firstTestFlowTbgPress": 123.45,
                "firstTestGasVol": 123.45,
                "firstTestGor": 123.45,
                "firstTestOilVol": 123.45,
                "firstTestWaterVol": 123.45,
                "firstTreatmentType": "string",
                "flowPath": "string",
                "fluidType": "string",
                "footageInLandingZone": 123.45,
                "formationThicknessMean": 123.45,
                "fractureConductivity": 123.45,
                "gasAnalysisDate": "2020-01-01",
                "gasC1": 123.45,
                "gasC2": 123.45,
                "gasC3": 123.45,
                "gasCo2": 123.45,
                "gasGatherer": "string",
                "gasH2": 123.45,
                "gasH2o": 123.45,
                "gasH2s": 123.45,
                "gasHe": 123.45,
                "gasIc4": 123.45,
                "gasIc5": 123.45,
                "gasN2": 123.45,
                "gasNc10": 123.45,
                "gasNc4": 123.45,
                "gasNc5": 123.45,
                "gasNc6": 123.45,
                "gasNc7": 123.45,
                "gasNc8": 123.45,
                "gasNc9": 123.45,
                "gasO2": 123.45,
                "gasSpecificGravity": 123.45,
                "grossPerforatedInterval": 123.45,
                "groundElevation": 123.45,
                "heelLatitude": 123.45,
                "heelLongitude": 123.45,
                "holeDirection": "string",
                "horizontalSpacing": 123.45,
                "hzWellSpacingAnyZone": 123.45,
                "hzWellSpacingSameZone": 123.45,
                "id": "5e272d38b78910dd2a1bd691",
                "ihsId": "5e272d38b78910dd2a1bd691",
                "initialRespress": 123.45,
                "initialRestemp": 123.45,
                "landingZone": "string",
                "landingZoneBase": 123.45,
                "landingZoneTop": 123.45,
                "lateralLength": 123.45,
                "leaseName": "string",
                "leaseNumber": "string",
                "lowerPerforation": 123.45,
                "matrixPermeability": 123.45,
                "measuredDepth": 123.45,
                "nglGatherer": "string",
                "numTreatmentRecords": 123.45,
                "oilApiGravity": 123.45,
                "oilGatherer": "string",
                "oilSpecificGravity": 123.45,
                "padName": "string",
                "parentChildAnyZone": "string",
                "parentChildSameZone": "string",
                "percentInZone": 123.45,
                "perfLateralLength": 123.45,
                "permitDate": "2020-01-01",
                "phdwinId": "5e272d38b78910dd2a1bd691",
                "play": "string",
                "porosity": 123.45,
                "previousOperator": "string",
                "previousOperatorAlias": "string",
                "previousOperatorCode": "string",
                "previousOperatorTicker": "string",
                "primaryProduct": "string",
                "prmsReservesCategory": "string",
                "prmsReservesSubCategory": "string",
                "prmsResourcesClass": "string",
                "productionMethod": "string",
                "proppantMeshSize": "string",
                "proppantType": "string",
                "range": "string",
                "recoveryMethod": "string",
                "refracAdditiveVolume": 123.45,
                "refracClusterCount": 123.45,
                "refracDate": "2020-01-01",
                "refracFluidVolume": 123.45,
                "refracFracVendor": "string",
                "refracMaxInjectionPressure": 123.45,
                "refracMaxInjectionRate": 123.45,
                "refracPropWeight": 123.45,
                "refracStageCount": 123.45,
                "refracTreatmentType": "string",
                "rig": "string",
                "rs": 123.45,
                "rsegId": "5e272d38b78910dd2a1bd691",
                "section": "string",
                "sg": 123.45,
                "so": 123.45,
                "spudDate": "2020-01-01",
                "stageSpacing": 123.45,
                "state": "string",
                "status": "string",
                "subplay": "string",
                "surfaceLatitude": 123.45,
                "surfaceLongitude": 123.45,
                "survey": "string",
                "sw": 123.45,
                "targetFormation": "string",
                "tgsId": "5e272d38b78910dd2a1bd691",
                "spgciId": "5e272d38b78910dd2a1bd691",
                "thickness": 123.45,
                "til": "2020-01-01",
                "toeInLandingZone": "string",
                "toeLatitude": 123.45,
                "toeLongitude": 123.45,
                "toeUp": "string",
                "township": "string",
                "trueVerticalDepth": 123.45,
                "tubingDepth": 123.45,
                "tubingId": 123.45,
                "typeCurveArea": "string",
                "upperPerforation": 123.45,
                "verticalSpacing": 123.45,
                "vtWellSpacingAnyZone": 123.45,
                "vtWellSpacingSameZone": 123.45,
                "wellName": "string",
                "wellNumber": "string",
                "wellType": "string",
                "zi": 123.45
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "id": "5e272d38b78910dd2a1bd691",
                    "chosenID": "string",
                    "dataSource": "string",
                    "createdAt": "2020-01-01",
                    "updatedAt": "2020-01-01",
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
"""

patch_put_well_response = """
        Example data:
        {
            "dataSource": "string",
            "abstract": "string",
            "acreSpacing": 123.45,
            "allocationType": "string",
            "api10": "string",
            "api12": "string",
            "api14": "string",
            "ariesId": "5e272d38b78910dd2a1bd691",
            "azimuth": 123.45,
            "basin": "string",
            "bg": 123.45,
            "block": "string",
            "bo": 123.45,
            "bubblePointPress": 123.45,
            "casingId": 123.45,
            "chokeSize": 123.45,
            "chosenID": "string",
            "chosenKeyID": "string",
            "completionDesign": "string",
            "completionEndDate": "2020-01-01",
            "completionStartDate": "2020-01-01",
            "country": "string",
            "county": "string",
            "currentOperator": "string",
            "currentOperatorAlias": "string",
            "currentOperatorCode": "string",
            "currentOperatorTicker": "string",
            "customBool0": true,
            "customBool1": true,
            "customBool2": true,
            "customBool3": true,
            "customBool4": true,
            "customDate0": "2020-01-01",
            "customDate1": "2020-01-01",
            "customDate2": "2020-01-01",
            "customDate3": "2020-01-01",
            "customDate4": "2020-01-01",
            "customDate5": "2020-01-01",
            "customDate6": "2020-01-01",
            "customDate7": "2020-01-01",
            "customDate8": "2020-01-01",
            "customDate9": "2020-01-01",
            "customDate10": "2020-01-01",
            "customDate11": "2020-01-01",
            "customDate12": "2020-01-01",
            "customDate13": "2020-01-01",
            "customDate14": "2020-01-01",
            "customDate15": "2020-01-01",
            "customDate16": "2020-01-01",
            "customDate17": "2020-01-01",
            "customDate18": "2020-01-01",
            "customDate19": "2020-01-01",
            "customNumber0": 123.45,
            "customNumber1": 123.45,
            "customNumber10": 123.45,
            "customNumber11": 123.45,
            "customNumber12": 123.45,
            "customNumber13": 123.45,
            "customNumber14": 123.45,
            "customNumber15": 123.45,
            "customNumber16": 123.45,
            "customNumber17": 123.45,
            "customNumber18": 123.45,
            "customNumber19": 123.45,
            "customNumber2": 123.45,
            "customNumber3": 123.45,
            "customNumber4": 123.45,
            "customNumber5": 123.45,
            "customNumber6": 123.45,
            "customNumber7": 123.45,
            "customNumber8": 123.45,
            "customNumber9": 123.45,
            "customString0": "string",
            "customString1": "string",
            "customString10": "string",
            "customString11": "string",
            "customString12": "string",
            "customString13": "string",
            "customString14": "string",
            "customString15": "string",
            "customString16": "string",
            "customString17": "string",
            "customString18": "string",
            "customString19": "string",
            "customString20": "string",
            "customString21": "string",
            "customString22": "string",
            "customString23": "string",
            "customString24": "string",
            "customString25": "string",
            "customString26": "string",
            "customString27": "string",
            "customString28": "string",
            "customString29": "string",
            "customString30": "string",
            "customString31": "string",
            "customString32": "string",
            "customString33": "string",
            "customString34": "string",
            "customString2": "string",
            "customString3": "string",
            "customString4": "string",
            "customString5": "string",
            "customString6": "string",
            "customString7": "string",
            "customString8": "string",
            "customString9": "string",
            "dataSourceCustomName": "string",
            "dateRigRelease": "2020-01-01",
            "dewPointPress": 123.45,
            "distanceFromBaseOfZone": 123.45,
            "distanceFromTopOfZone": 123.45,
            "district": "string",
            "drainageArea": 123.45,
            "drillEndDate": "2020-01-01",
            "drillStartDate": "2020-01-01",
            "drillinginfoId": "5e272d38b78910dd2a1bd691",
            "elevation": 123.45,
            "elevationType": "string",
            "field": "string",
            "firstAdditiveVolume": 123.45,
            "firstClusterCount": 123.45,
            "firstFluidVolume": 123.45,
            "firstFracVendor": "string",
            "firstMaxInjectionPressure": 123.45,
            "firstMaxInjectionRate": 123.45,
            "firstProdDate": "2020-01-01",
            "firstPropWeight": 123.45,
            "firstStageCount": 123.45,
            "firstTestFlowTbgPress": 123.45,
            "firstTestGasVol": 123.45,
            "firstTestGor": 123.45,
            "firstTestOilVol": 123.45,
            "firstTestWaterVol": 123.45,
            "firstTreatmentType": "string",
            "flowPath": "string",
            "fluidType": "string",
            "footageInLandingZone": 123.45,
            "formationThicknessMean": 123.45,
            "fractureConductivity": 123.45,
            "gasAnalysisDate": "2020-01-01",
            "gasC1": 123.45,
            "gasC2": 123.45,
            "gasC3": 123.45,
            "gasCo2": 123.45,
            "gasGatherer": "string",
            "gasH2": 123.45,
            "gasH2o": 123.45,
            "gasH2s": 123.45,
            "gasHe": 123.45,
            "gasIc4": 123.45,
            "gasIc5": 123.45,
            "gasN2": 123.45,
            "gasNc10": 123.45,
            "gasNc4": 123.45,
            "gasNc5": 123.45,
            "gasNc6": 123.45,
            "gasNc7": 123.45,
            "gasNc8": 123.45,
            "gasNc9": 123.45,
            "gasO2": 123.45,
            "gasSpecificGravity": 123.45,
            "grossPerforatedInterval": 123.45,
            "groundElevation": 123.45,
            "heelLatitude": 123.45,
            "heelLongitude": 123.45,
            "holeDirection": "string",
            "horizontalSpacing": 123.45,
            "hzWellSpacingAnyZone": 123.45,
            "hzWellSpacingSameZone": 123.45,
            "id": "5e272d38b78910dd2a1bd691",
            "ihsId": "5e272d38b78910dd2a1bd691",
            "initialRespress": 123.45,
            "initialRestemp": 123.45,
            "landingZone": "string",
            "landingZoneBase": 123.45,
            "landingZoneTop": 123.45,
            "lateralLength": 123.45,
            "leaseName": "string",
            "leaseNumber": "string",
            "lowerPerforation": 123.45,
            "matrixPermeability": 123.45,
            "measuredDepth": 123.45,
            "nglGatherer": "string",
            "numTreatmentRecords": 123.45,
            "oilApiGravity": 123.45,
            "oilGatherer": "string",
            "oilSpecificGravity": 123.45,
            "padName": "string",
            "parentChildAnyZone": "string",
            "parentChildSameZone": "string",
            "percentInZone": 123.45,
            "perfLateralLength": 123.45,
            "permitDate": "2020-01-01",
            "phdwinId": "5e272d38b78910dd2a1bd691",
            "play": "string",
            "porosity": 123.45,
            "previousOperator": "string",
            "previousOperatorAlias": "string",
            "previousOperatorCode": "string",
            "previousOperatorTicker": "string",
            "primaryProduct": "string",
            "prmsReservesCategory": "string",
            "prmsReservesSubCategory": "string",
            "prmsResourcesClass": "string",
            "productionMethod": "string",
            "proppantMeshSize": "string",
            "proppantType": "string",
            "range": "string",
            "recoveryMethod": "string",
            "refracAdditiveVolume": 123.45,
            "refracClusterCount": 123.45,
            "refracDate": "2020-01-01",
            "refracFluidVolume": 123.45,
            "refracFracVendor": "string",
            "refracMaxInjectionPressure": 123.45,
            "refracMaxInjectionRate": 123.45,
            "refracPropWeight": 123.45,
            "refracStageCount": 123.45,
            "refracTreatmentType": "string",
            "rig": "string",
            "rs": 123.45,
            "rsegId": "5e272d38b78910dd2a1bd691",
            "section": "string",
            "sg": 123.45,
            "so": 123.45,
            "spudDate": "2020-01-01",
            "stageSpacing": 123.45,
            "state": "string",
            "status": "string",
            "subplay": "string",
            "surfaceLatitude": 123.45,
            "surfaceLongitude": 123.45,
            "survey": "string",
            "sw": 123.45,
            "targetFormation": "string",
            "tgsId": "5e272d38b78910dd2a1bd691",
            "spgciId": "5e272d38b78910dd2a1bd691",
            "thickness": 123.45,
            "til": "2020-01-01",
            "toeInLandingZone": "string",
            "toeLatitude": 123.45,
            "toeLongitude": 123.45,
            "toeUp": "string",
            "township": "string",
            "trueVerticalDepth": 123.45,
            "tubingDepth": 123.45,
            "tubingId": 123.45,
            "typeCurveArea": "string",
            "upperPerforation": 123.45,
            "verticalSpacing": 123.45,
            "vtWellSpacingAnyZone": 123.45,
            "vtWellSpacingSameZone": 123.45,
            "wellName": "string",
            "wellNumber": "string",
            "wellType": "string",
            "zi": 123.45
        }
"""

Wells.get_company_wells.__doc__ += wells_response  # type: ignore [operator]
Wells.get_project_company_wells.__doc__ += wells_response  # type: ignore [operator]
Wells.get_project_wells.__doc__ += wells_response  # type: ignore [operator]

Wells.get_company_well_by_id.__doc__ += well_response  # type: ignore [operator]
Wells.get_project_company_well_by_id_url.__doc__ += well_response  # type: ignore [operator]
Wells.get_project_well_by_id_url.__doc__ += well_response  # type: ignore [operator]

Wells.post_company_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]
Wells.post_project_company_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]
Wells.post_project_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]

Wells.put_company_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]
Wells.put_project_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]

Wells.put_company_well_by_id.__doc__ += patch_put_well_response  # type: ignore [operator]
Wells.put_project_well_by_id.__doc__ += patch_put_well_response  # type: ignore [operator]

Wells.patch_company_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]
Wells.patch_project_wells.__doc__ += post_patch_put_wells_response  # type: ignore [operator]

Wells.patch_company_well_by_id.__doc__ += patch_put_well_response  # type: ignore [operator]
Wells.patch_project_well_by_id.__doc__ += patch_put_well_response  # type: ignore [operator]
