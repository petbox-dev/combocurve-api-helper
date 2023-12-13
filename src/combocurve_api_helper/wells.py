from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


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

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_company_well_by_id_url(self, well_id: str) -> str:
        """
        Returns the API url for a specific company well from its well id.
        """
        return f'{self.API_BASE_URL}/wells/{id}'


    def get_project_company_wells_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for project company wells scoped from the
        project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/company-wells'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_company_well_by_id_url(self, project_id: str, well_id: str) -> str:
        """
        Returns the API url for a specific project company well from its
        well id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/company-wells/{id}'


    def get_project_wells_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for project wells scoped from the project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/wells'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_well_by_id_url(self, project_id: str, well_id: str) -> str:
        """
        Returns the API url for a specific project well from its well id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/wells/{id}'


    def get_well_comments_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for well comments.
        """
        url = f'{self.API_BASE_URL}/well-comments'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url

    ###########
    # API calls
    ###########


    # Company Wells


    def get_company_wells(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company wells.

        https://docs.api.combocurve.com/#f55ae267-2161-4025-a3a7-5df7d411a8e6
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


    def post_company_wells(self, data: ItemList) -> ItemList:
        """
        Creates a list of company wells.

        https://docs.api.combocurve.com/#3af96ea2-87a7-4fc2-9082-7b3191411f03
        """
        url = self.get_company_wells_url()
        wells = self._post_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def put_company_wells(self, data: ItemList) -> ItemList:
        """
        Upserts a list of company wells.

        https://docs.api.combocurve.com/#9aa285c2-8108-4589-92fd-3c7ee1a60c56
        """
        url = self.get_company_wells_url()
        wells = self._put_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def patch_company_wells(self, data: ItemList) -> ItemList:
        """
        Updates a list of company wells.

        https://docs.api.combocurve.com/#3d56ff9f-2c3d-4d28-8309-32ca79c61450
        """
        url = self.get_company_wells_url()
        wells = self._patch_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def delete_company_wells(
            self, project_id: str,
            chosen_id: Optional[str] = None, data_source: Optional[str] = None,
            well_id: Optional[str] = None) -> ItemList:
        """
        Deletes a list of company wells.

        https://docs.api.combocurve.com/#359b608e-05c2-41b4-a5ba-8070c34e5407

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

        https://docs.api.combocurve.com/#1e7560fb-4913-4bee-8ed5-7f691e5f6ec9
        """
        url = self.get_company_well_by_id_url(well_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]


    def put_company_well_by_id(self, well_id: str, data: Item) -> ItemList:
        """
        Upserts a specific company well from its well id.

        https://docs.api.combocurve.com/#9aa285c2-8108-4589-92fd-3c7ee1a60c56
        """
        url = self.get_company_well_by_id_url(well_id)
        wells = self._put_items(url, [data])

        return wells


    def patch_company_well_by_id(self, well_id: str, data: Item) -> ItemList:
        """
        Updates a specific company well from its well id.

        https://docs.api.combocurve.com/#dfed1eec-120f-4bc8-9ce8-8f8314e511b9
        """
        url = self.get_company_well_by_id_url(well_id)
        wells = self._patch_items(url, [data])

        return wells


    def delete_company_well_by_id(self, well_id: str) -> ItemList:
        """
        Deletes a specific company well from its well id.

        https://docs.api.combocurve.com/#359b608e-05c2-41b4-a5ba-8070c34e5407

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

        https://docs.api.combocurve.com/#15374dc9-94fe-4d85-b367-ae07c3881b5b
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


    def post_project_company_wells(self, project_id: str, data: ItemList) -> ItemList:
        """
        Creates a list of project company wells.

        https://docs.api.combocurve.com/#b9940884-cbd9-46cc-b8da-fa17246cced7
        """
        url = self.get_project_company_wells_url(project_id)
        wells = self._post_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def delete_project_company_wells(
            self, project_id: str,
            chosen_id: Optional[str] = None, data_source: Optional[str] = None,
            well_id: Optional[str] = None) -> ItemList:
        """
        Deletes a list of project company wells.

        https://docs.api.combocurve.com/#359b608e-05c2-41b4-a5ba-8070c34e5407

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

        https://docs.api.combocurve.com/#f3a836ab-93b0-4ec0-922a-a65d35d26b06
        """
        url = self.get_project_company_well_by_id_url(project_id, well_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]


    # Project Wells


    def get_project_wells(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/#2e1d512f-4996-49e8-b917-20bea90373ab
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


    def post_project_wells(self, project_id: str, data: ItemList) -> ItemList:
        """
        Creates a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/#55c7dcb1-b694-40ec-83bd-56e87f5853a6
        """
        url = self.get_project_wells_url(project_id)
        wells = self._post_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def put_project_wells(self, project_id: str, data: ItemList) -> ItemList:
        """
        Upserts a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/#731d6bb4-86af-4dff-8a34-3b63049e6c4b
        """
        url = self.get_project_wells_url(project_id)
        wells = self._put_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def patch_project_wells(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates a list of project wells scoped from the project's id.

        https://docs.api.combocurve.com/#80cb3f55-0444-41d3-9682-61e3d36e3b16
        """
        url = self.get_project_wells_url(project_id)
        wells = self._patch_items(url, data, POST_PATCH_PUT_LIMIT)

        return wells


    def delete_project_wells(
            self, project_id: str,
            chosen_id: Optional[str] = None, data_source: Optional[str] = None,
            well_id: Optional[str] = None) -> ItemList:
        """
        Deletes a list of project wells scoped from the project's id.
F
        https://docs.api.combocurve.com/#1b535f9f-2ace-4a90-bf95-791a23a90977

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

        https://docs.api.combocurve.com/#e44fe1d2-b292-4e34-bb79-224c63351ea3
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]


    def put_project_well_by_id(self, project_id: str, well_id: str, data: Item) -> ItemList:
        """
        Upserts a specific project well from its well id.

        https://docs.api.combocurve.com/#08036541-c470-4ee3-b4a6-be6626184071
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        wells = self._put_items(url, [data])

        return wells


    def patch_project_well_by_id(self, project_id: str, well_id: str, data: Item) -> ItemList:
        """
        Updates a specific project well from its well id.

        https://docs.api.combocurve.com/#29c1cd19-7e3c-4415-944d-0a2514e1823f
        """
        url = self.get_project_well_by_id_url(project_id, well_id)
        wells = self._patch_items(url, [data])

        return wells


    def delete_project_well_by_id(self, project_id: str, well_id: str) -> Item:
        """
        Deletes a specific project well from its well id.

        https://docs.api.combocurve.com/#18cd243f-187b-423d-98a7-a2b296ac7dee

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

        https://docs.api.combocurve.com/#0088082c-5909-47bd-b92e-d08db58bd8bb

        Example response:
        [
            {
                "commentedAt": "2020-07-27T17:52:28.791Z",
                "commentedBy": "5f51a46dd1986a0012058e01",
                "forecast": "60a6c4a13f40ab00125086a7",
                "project": "6064c19e2c3fc60012909a50",
                "text": "test",
                "well": "60e24fea5ea67a1bc4b857ae"
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
                "abstract": "31",
                "acreSpacing": 10,
                "allocationType": "MARCELLUS",
                "api10": "4247730985",
                "api12": "424773098500",
                "api14": "42477309850000",
                "ariesId": "D8GLPMRF8C",
                "azimuth": 14.52890449,
                "basin": "GULF COAST CENTRAL",
                "bg": 0.00368,
                "block": "7",
                "bo": 1.5,
                "bubblePointPress": 45,
                "casingId": 789,
                "chokeSize": 27,
                "chosenID": "42477309850000",
                "chosenKeyID": "API14",
                "completionDesign": "HYBRID",
                "completionEndDate": "2012-04-05T00:00:00Z",
                "completionStartDate": "2012-04-04T00:00:00Z",
                "copied": false,
                "copiedFrom": "5e272d39b78210dd2a1bd8fe",
                "country": "US",
                "county": "WASHINGTON (TX)",
                "createdAt": "2020-01-21T16:56:24.869Z",
                "cumBoe": 257.91616666666664,
                "cumBoePerPerforatedInterval": 54.11292022341659,
                "cumGas": 1547.401,
                "cumGasPerPerforatedInterval": 324.64527347454947,
                "cumGor": 96712562.5,
                "cumMmcfge": 1547.497,
                "cumMmcfgePerPerforatedInterval": 324.6775213404995,
                "cumOil": 0.016,
                "cumOilPerPerforatedInterval": 0.005374644325007904,
                "cumWater": 45.439,
                "cumWaterPerPerforatedInterval": 6.429339234903573,
                "currentOperator": "CRAWFORD HUGHES OPERATING CO.",
                "currentOperatorAlias": "CRAWFORD HUGHES OPERATING",
                "currentOperatorCode": "OP",
                "currentOperatorTicker": "MGY",
                "customBool0": true,
                "customBool1": false,
                "customBool2": true,
                "customBool3": false,
                "customBool4": false,
                "customDate0": "2020-01-21T16:56:24.869Z",
                "customDate1": "2020-01-22T16:56:24.869Z",
                "customDate2": "2020-01-21T16:56:24.849Z",
                "customDate3": "2012-01-21T16:56:24.869Z",
                "customDate4": "2014-02-21T16:56:24.869Z",
                "customDate5": "2020-01-21T16:52:24.869Z",
                "customDate6": "2004-03-12T17:23:17.256Z",
                "customDate7": "2020-01-21T16:12:24.869Z",
                "customDate8": "2015-03-17T16:56:24.869Z",
                "customDate9": "2022-05-04T00:00:00.000Z",
                "customNumber0": 4944,
                "customNumber1": 13278.72,
                "customNumber10": 12910,
                "customNumber11": -96.3070098,
                "customNumber12": 30.3248831,
                "customNumber13": 30.3355247,
                "customNumber14": 55.1,
                "customNumber15": 399,
                "customNumber16": 2868.92,
                "customNumber17": 428.47,
                "customNumber18": 0.73,
                "customNumber19": 376,
                "customNumber2": 2839,
                "customNumber3": 30.1097601,
                "customNumber4": -96.5976726,
                "customNumber5": 12626,
                "customNumber6": -5,
                "customNumber7": 0,
                "customNumber8": 184.427,
                "customNumber9": 311,
                "customString0": "internal",
                "customString1": "KB EST",
                "customString10": "D",
                "customString11": "TX",
                "customString12": "USA",
                "customString13": "GIDDINGS",
                "customString14": "INPT.VS3T8il8KF",
                "customString15": "9v7k0dcmbncd",
                "customString16": "OPERATING",
                "customString17": "Point",
                "customString18": "5f1b6511a5e1e208ccb34baa",
                "customString19": "ACTIVE",
                "customString2": "Y",
                "customString3": "1",
                "customString4": "NORMA",
                "customString5": "OIL",
                "customString6": "api",
                "customString7": "MAGNOLIA OIL & GAS",
                "customString8": "186",
                "customString9": "42477306120000",
                "dataPool": "internal",
                "dataSource": "internal",
                "dataSourceCustomName": "internal-id",
                "dateRigRelease": "2131-04-27T00:00:00Z",
                "dewPointPress": 12,
                "distanceFromBaseOfZone": 304.786,
                "distanceFromTopOfZone": 26.96,
                "district": "03",
                "drainageArea": 160,
                "drillEndDate": "2012-05-05T00:00:00Z",
                "drillStartDate": "2012-02-05T00:00:00Z",
                "drillinginfoId": "9E5F5CC579867509254700023",
                "elevation": 301.31,
                "elevationType": "KB EST",
                "field": "GIDDINGS",
                "first12Boe": 103.14016666666667,
                "first12BoePerPerforatedInterval": 54.11292022341659,
                "first12Gas": 618.841,
                "first12GasPerPerforatedInterval": 471.76666666666665,
                "first12Gor": 7072.235799694917,
                "first12Mmcfge": 618.841,
                "first12MmcfgePerPerforatedInterval": 137.525,
                "first12Oil": 0,
                "first12OilPerPerforatedInterval": 5.298140371925615,
                "first12Water": 6.43,
                "first12WaterPerPerforatedInterval": 14.47715736040609,
                "first6Boe": 81.80216666666668,
                "first6BoePerPerforatedInterval": 62.509399855386846,
                "first6Gas": 490.813,
                "first6GasPerPerforatedInterval": 937.1,
                "first6Gor": 21508.733624454148,
                "first6Mmcfge": 490.813,
                "first6MmcfgePerPerforatedInterval": 730.7922077922078,
                "first6Oil": 0,
                "first6OilPerPerforatedInterval": 103.68072289156626,
                "first6Water": 5.132,
                "first6WaterPerPerforatedInterval": 43.49841772151899,
                "firstAdditiveVolume": 130896,
                "firstClusterCount": 1,
                "firstFluidPerPerforatedInterval": 0.00004420703628660895,
                "firstFluidVolume": 682,
                "firstFracVendor": "UNIVERSAL PRESSURE PUMPING",
                "firstMaxInjectionPressure": 10820,
                "firstMaxInjectionRate": 87.17,
                "firstProdDate": "2012-04-07T00:00:00Z",
                "firstProdDateDailyCalc": "2012-04-07T00:00:00Z",
                "firstProdDateMonthlyCalc": "2012-05-15T00:00:00Z",
                "firstPropWeight": 357323,
                "firstProppantPerFluid": 0.633151794442117,
                "firstProppantPerPerforatedInterval": 906.8,
                "firstStageCount": 1,
                "firstTestFlowTbgPress": 1490,
                "firstTestGasVol": 2225,
                "firstTestGor": 1252,
                "firstTestOilVol": 1813,
                "firstTestWaterVol": 231,
                "firstTreatmentType": "SLICKWATER",
                "flowPath": "path",
                "fluidType": "99456",
                "footageInLandingZone": 2326.91,
                "formationThicknessMean": 331.746,
                "fractureConductivity": 12.5,
                "gasAnalysisDate": "2020-10-26T20:45:51.482Z",
                "gasC1": 2.135,
                "gasC2": 1.245,
                "gasC3": 0.85,
                "gasCo2": 1.23,
                "gasGatherer": "ENERGY TRANSFER COMPANY",
                "gasH2": 2.51,
                "gasH2o": 0.12,
                "gasH2s": 3.47,
                "gasHe": 2.45,
                "gasIc4": 1.23,
                "gasIc5": 2.1,
                "gasN2": 1.2,
                "gasNc10": 2.04,
                "gasNc4": 1.95,
                "gasNc5": 0.45,
                "gasNc6": 0.75,
                "gasNc7": 0.87,
                "gasNc8": 0.12,
                "gasNc9": 0.15,
                "gasO2": 2.56,
                "gasSpecificGravity": 0.71,
                "generic": true,
                "grossPerforatedInterval": 4268,
                "groundElevation": 278.31,
                "hasDaily": false,
                "hasMonthly": true,
                "heelLatitude": 30.1903838,
                "heelLongitude": -96.6974461,
                "holeDirection": "H",
                "horizontalSpacing": 1.21,
                "hzWellSpacingAnyZone": 677.7982338,
                "hzWellSpacingSameZone": 2001.308331,
                "id": "5e272d39b78910dd2a1bd8fe",
                "ihsId": "5489",
                "initialRespress": 5400,
                "initialRestemp": 220,
                "inptID": "INPT.ZB9xQAEFu5",
                "landingZone": "Austin Chalk",
                "landingZoneBase": 0.63,
                "landingZoneTop": 1,
                "last12Boe": 0.6311666666666667,
                "last12BoePerPerforatedInterval": 0.21630170316301703,
                "last12Gas": 3.787,
                "last12GasPerPerforatedInterval": 1.2291970802919707,
                "last12Gor": 3586.206896551724,
                "last12Mmcfge": 3.787,
                "last12MmcfgePerPerforatedInterval": 4.525384615384615,
                "last12Oil": 0,
                "last12OilPerPerforatedInterval": 0.08518296340731854,
                "last12Water": 0.6,
                "last12WaterPerPerforatedInterval": 0.44452554744525546,
                "lastMonthBoe": 0.017833333333333333,
                "lastMonthBoePerPerforatedInterval": 0.0004819940783584659,
                "lastMonthGas": 0.107,
                "lastMonthGasPerPerforatedInterval": 0.0028919644701507954,
                "lastMonthGor": 5142.857142857143,
                "lastMonthMmcfge": 0.107,
                "lastMonthMmcfgePerPerforatedInterval": 1.4784022294472827,
                "lastMonthOil": 0,
                "lastMonthOilPerPerforatedInterval": 0.001937984496124031,
                "lastMonthWater": 0.017,
                "lastMonthWaterPerPerforatedInterval": 0.9967130214917825,
                "lastProdDateDaily": "2015-10-04T00:00:00Z",
                "lastProdDateMonthly": "2015-10-15T00:00:00Z",
                "lateralLength": 777,
                "leaseName": "SCHAWE-WOLFF",
                "leaseNumber": "265263",
                "lowerPerforation": 15313,
                "matrixPermeability": 1.04,
                "measuredDepth": 15314,
                "monthsProduced": 42,
                "mostRecentImportDate": "2020-07-24T22:47:45.941Z",
                "mostRecentImportDesc": "External API Import - 03/01/2021 03:03:47 PM",
                "mostRecentImportType": "api",
                "nglGatherer": "ENTERPRISE LLC",
                "numTreatmentRecords": 26,
                "oilApiGravity": 52.5,
                "oilGatherer": "ENTERPRISE CRUDE OIL LLC",
                "oilSpecificGravity": 43.5,
                "padName": "33-023-01395",
                "parentChildAnyZone": "LIME ROCK",
                "parentChildSameZone": "5950",
                "percentInZone": 100,
                "perfLateralLength": 2,
                "permitDate": "2012-06-06T00:00:00Z",
                "phdwinId": "9E5F5CC579867509254700023",
                "play": "EAGLEBINE",
                "porosity": 9,
                "previousOperator": "EXXON MOBIL",
                "previousOperatorAlias": "XTO ENERGY",
                "previousOperatorCode": "XT",
                "previousOperatorTicker": "XOM",
                "primaryProduct": "GAS",
                "prmsReservesCategory": "Proved",
                "prmsReservesSubCategory": "Producing",
                "prmsResourcesClass": "Standard",
                "productionMethod": "PUMPING",
                "proppantMeshSize": "100M/4070/",
                "proppantType": "RSWhite/Brown/",
                "range": "26W",
                "recoveryMethod": "Regular",
                "refracAdditiveVolume": 1370,
                "refracClusterCount": 20,
                "refracDate": "2020-09-09T00:00:00Z",
                "refracFluidPerPerforatedInterval": 2.5248802064135645,
                "refracFluidVolume": 13700,
                "refracFracVendor": "BAKER HUGHES",
                "refracMaxInjectionPressure": 23,
                "refracMaxInjectionRate": 0.42,
                "refracPropWeight": 8,
                "refracProppantPerFluid": 4.957037815996877e-11,
                "refracProppantPerPerforatedInterval": 10,
                "refracStageCount": 2,
                "refracTreatmentType": "CROSSLINK HC",
                "rig": "RIG-1",
                "rs": 1,
                "rsegId": "421",
                "scope": "company",
                "section": "71",
                "sg": 0.595085877,
                "so": 40,
                "spudDate": "2012-01-06T00:00:00Z",
                "stageSpacing": 12,
                "state": "TX",
                "status": "INACTIVE",
                "subplay": "EAGLEVILLE",
                "surfaceLatitude": 30.3288694,
                "surfaceLongitude": -96.3641278,
                "survey": "COLES, J P",
                "sw": 30,
                "targetFormation": "AUSTIN CHALK, GAS",
                "tgsId": "147",
                "thickness": 70,
                "til": "2020-10-26T20:45:51.482Z",
                "toeInLandingZone": "Y",
                "toeLatitude": 30.3332851,
                "toeLongitude": -96.3631776,
                "toeUp": "02/01/2013",
                "totalAdditiveVolume": 400450,
                "totalClusterCount": 35,
                "totalFluidPerPerforatedInterval": 34.21673724091821,
                "totalFluidVolume": 425134,
                "totalPropWeight": 8840026,
                "totalProppantPerFluid": 1.225148340912877,
                "totalProppantPerPerforatedInterval": 1149.3987777922248,
                "totalStageCount": 31,
                "township": "001N",
                "trueVerticalDepth": 12691.52,
                "tubingDepth": 741006,
                "tubingId": 21,
                "typeCurveArea": "1000 GOR",
                "updatedAt": "2020-07-26T15:29:00.352Z",
                "upperPerforation": 12226,
                "verticalSpacing": 10,
                "vtWellSpacingAnyZone": 11,
                "vtWellSpacingSameZone": 10,
                "wellName": "SCHAWE-WOLFF",
                "wellNumber": "1H",
                "wellType": "GAS",
                "zi": 23
            }
        ]
"""

well_response = """
        Example response:
        {
            "abstract": "31",
            "acreSpacing": 10,
            "allocationType": "MARCELLUS",
            "api10": "4247730985",
            "api12": "424773098500",
            "api14": "42477309850000",
            "ariesId": "D8GLPMRF8C",
            "azimuth": 14.52890449,
            "basin": "GULF COAST CENTRAL",
            "bg": 0.00368,
            "block": "7",
            "bo": 1.5,
            "bubblePointPress": 45,
            "casingId": 789,
            "chokeSize": 27,
            "chosenID": "42477309850000",
            "chosenKeyID": "API14",
            "completionDesign": "HYBRID",
            "completionEndDate": "2012-04-05T00:00:00Z",
            "completionStartDate": "2012-04-04T00:00:00Z",
            "copied": false,
            "copiedFrom": "5e272d39b78210dd2a1bd8fe",
            "country": "US",
            "county": "WASHINGTON (TX)",
            "createdAt": "2020-01-21T16:56:24.869Z",
            "cumBoe": 257.91616666666664,
            "cumBoePerPerforatedInterval": 54.11292022341659,
            "cumGas": 1547.401,
            "cumGasPerPerforatedInterval": 324.64527347454947,
            "cumGor": 96712562.5,
            "cumMmcfge": 1547.497,
            "cumMmcfgePerPerforatedInterval": 324.6775213404995,
            "cumOil": 0.016,
            "cumOilPerPerforatedInterval": 0.005374644325007904,
            "cumWater": 45.439,
            "cumWaterPerPerforatedInterval": 6.429339234903573,
            "currentOperator": "CRAWFORD HUGHES OPERATING CO.",
            "currentOperatorAlias": "CRAWFORD HUGHES OPERATING",
            "currentOperatorCode": "OP",
            "currentOperatorTicker": "MGY",
            "customBool0": true,
            "customBool1": false,
            "customBool2": true,
            "customBool3": false,
            "customBool4": false,
            "customDate0": "2020-01-21T16:56:24.869Z",
            "customDate1": "2020-01-22T16:56:24.869Z",
            "customDate2": "2020-01-21T16:56:24.849Z",
            "customDate3": "2012-01-21T16:56:24.869Z",
            "customDate4": "2014-02-21T16:56:24.869Z",
            "customDate5": "2020-01-21T16:52:24.869Z",
            "customDate6": "2004-03-12T17:23:17.256Z",
            "customDate7": "2020-01-21T16:12:24.869Z",
            "customDate8": "2015-03-17T16:56:24.869Z",
            "customDate9": "2022-05-04T00:00:00.000Z",
            "customNumber0": 4944,
            "customNumber1": 13278.72,
            "customNumber10": 12910,
            "customNumber11": -96.3070098,
            "customNumber12": 30.3248831,
            "customNumber13": 30.3355247,
            "customNumber14": 55.1,
            "customNumber15": 399,
            "customNumber16": 2868.92,
            "customNumber17": 428.47,
            "customNumber18": 0.73,
            "customNumber19": 376,
            "customNumber2": 2839,
            "customNumber3": 30.1097601,
            "customNumber4": -96.5976726,
            "customNumber5": 12626,
            "customNumber6": -5,
            "customNumber7": 0,
            "customNumber8": 184.427,
            "customNumber9": 311,
            "customString0": "internal",
            "customString1": "KB EST",
            "customString10": "D",
            "customString11": "TX",
            "customString12": "USA",
            "customString13": "GIDDINGS",
            "customString14": "INPT.VS3T8il8KF",
            "customString15": "9v7k0dcmbncd",
            "customString16": "OPERATING",
            "customString17": "Point",
            "customString18": "5f1b6511a5e1e208ccb34baa",
            "customString19": "ACTIVE",
            "customString2": "Y",
            "customString3": "1",
            "customString4": "NORMA",
            "customString5": "OIL",
            "customString6": "api",
            "customString7": "MAGNOLIA OIL & GAS",
            "customString8": "186",
            "customString9": "42477306120000",
            "dataPool": "internal",
            "dataSource": "internal",
            "dataSourceCustomName": "internal-id",
            "dateRigRelease": "2131-04-27T00:00:00Z",
            "dewPointPress": 12,
            "distanceFromBaseOfZone": 304.786,
            "distanceFromTopOfZone": 26.96,
            "district": "03",
            "drainageArea": 160,
            "drillEndDate": "2012-05-05T00:00:00Z",
            "drillStartDate": "2012-02-05T00:00:00Z",
            "drillinginfoId": "9E5F5CC579867509254700023",
            "elevation": 301.31,
            "elevationType": "KB EST",
            "field": "GIDDINGS",
            "first12Boe": 103.14016666666667,
            "first12BoePerPerforatedInterval": 54.11292022341659,
            "first12Gas": 618.841,
            "first12GasPerPerforatedInterval": 471.76666666666665,
            "first12Gor": 7072.235799694917,
            "first12Mmcfge": 618.841,
            "first12MmcfgePerPerforatedInterval": 137.525,
            "first12Oil": 0,
            "first12OilPerPerforatedInterval": 5.298140371925615,
            "first12Water": 6.43,
            "first12WaterPerPerforatedInterval": 14.47715736040609,
            "first6Boe": 81.80216666666668,
            "first6BoePerPerforatedInterval": 62.509399855386846,
            "first6Gas": 490.813,
            "first6GasPerPerforatedInterval": 937.1,
            "first6Gor": 21508.733624454148,
            "first6Mmcfge": 490.813,
            "first6MmcfgePerPerforatedInterval": 730.7922077922078,
            "first6Oil": 0,
            "first6OilPerPerforatedInterval": 103.68072289156626,
            "first6Water": 5.132,
            "first6WaterPerPerforatedInterval": 43.49841772151899,
            "firstAdditiveVolume": 130896,
            "firstClusterCount": 1,
            "firstFluidPerPerforatedInterval": 0.00004420703628660895,
            "firstFluidVolume": 682,
            "firstFracVendor": "UNIVERSAL PRESSURE PUMPING",
            "firstMaxInjectionPressure": 10820,
            "firstMaxInjectionRate": 87.17,
            "firstProdDate": "2012-04-07T00:00:00Z",
            "firstProdDateDailyCalc": "2012-04-07T00:00:00Z",
            "firstProdDateMonthlyCalc": "2012-05-15T00:00:00Z",
            "firstPropWeight": 357323,
            "firstProppantPerFluid": 0.633151794442117,
            "firstProppantPerPerforatedInterval": 906.8,
            "firstStageCount": 1,
            "firstTestFlowTbgPress": 1490,
            "firstTestGasVol": 2225,
            "firstTestGor": 1252,
            "firstTestOilVol": 1813,
            "firstTestWaterVol": 231,
            "firstTreatmentType": "SLICKWATER",
            "flowPath": "path",
            "fluidType": "99456",
            "footageInLandingZone": 2326.91,
            "formationThicknessMean": 331.746,
            "fractureConductivity": 12.5,
            "gasAnalysisDate": "2020-10-26T20:45:51.482Z",
            "gasC1": 2.135,
            "gasC2": 1.245,
            "gasC3": 0.85,
            "gasCo2": 1.23,
            "gasGatherer": "ENERGY TRANSFER COMPANY",
            "gasH2": 2.51,
            "gasH2o": 0.12,
            "gasH2s": 3.47,
            "gasHe": 2.45,
            "gasIc4": 1.23,
            "gasIc5": 2.1,
            "gasN2": 1.2,
            "gasNc10": 2.04,
            "gasNc4": 1.95,
            "gasNc5": 0.45,
            "gasNc6": 0.75,
            "gasNc7": 0.87,
            "gasNc8": 0.12,
            "gasNc9": 0.15,
            "gasO2": 2.56,
            "gasSpecificGravity": 0.71,
            "generic": true,
            "grossPerforatedInterval": 4268,
            "groundElevation": 278.31,
            "hasDaily": false,
            "hasMonthly": true,
            "heelLatitude": 30.1903838,
            "heelLongitude": -96.6974461,
            "holeDirection": "H",
            "horizontalSpacing": 1.21,
            "hzWellSpacingAnyZone": 677.7982338,
            "hzWellSpacingSameZone": 2001.308331,
            "id": "5e272d39b78910dd2a1bd8fe",
            "ihsId": "5489",
            "initialRespress": 5400,
            "initialRestemp": 220,
            "inptID": "INPT.ZB9xQAEFu5",
            "landingZone": "Austin Chalk",
            "landingZoneBase": 0.63,
            "landingZoneTop": 1,
            "last12Boe": 0.6311666666666667,
            "last12BoePerPerforatedInterval": 0.21630170316301703,
            "last12Gas": 3.787,
            "last12GasPerPerforatedInterval": 1.2291970802919707,
            "last12Gor": 3586.206896551724,
            "last12Mmcfge": 3.787,
            "last12MmcfgePerPerforatedInterval": 4.525384615384615,
            "last12Oil": 0,
            "last12OilPerPerforatedInterval": 0.08518296340731854,
            "last12Water": 0.6,
            "last12WaterPerPerforatedInterval": 0.44452554744525546,
            "lastMonthBoe": 0.017833333333333333,
            "lastMonthBoePerPerforatedInterval": 0.0004819940783584659,
            "lastMonthGas": 0.107,
            "lastMonthGasPerPerforatedInterval": 0.0028919644701507954,
            "lastMonthGor": 5142.857142857143,
            "lastMonthMmcfge": 0.107,
            "lastMonthMmcfgePerPerforatedInterval": 1.4784022294472827,
            "lastMonthOil": 0,
            "lastMonthOilPerPerforatedInterval": 0.001937984496124031,
            "lastMonthWater": 0.017,
            "lastMonthWaterPerPerforatedInterval": 0.9967130214917825,
            "lastProdDateDaily": "2015-10-04T00:00:00Z",
            "lastProdDateMonthly": "2015-10-15T00:00:00Z",
            "lateralLength": 777,
            "leaseName": "SCHAWE-WOLFF",
            "leaseNumber": "265263",
            "lowerPerforation": 15313,
            "matrixPermeability": 1.04,
            "measuredDepth": 15314,
            "monthsProduced": 42,
            "mostRecentImportDate": "2020-07-24T22:47:45.941Z",
            "mostRecentImportDesc": "External API Import - 03/01/2021 03:03:47 PM",
            "mostRecentImportType": "api",
            "nglGatherer": "ENTERPRISE LLC",
            "numTreatmentRecords": 26,
            "oilApiGravity": 52.5,
            "oilGatherer": "ENTERPRISE CRUDE OIL LLC",
            "oilSpecificGravity": 43.5,
            "padName": "33-023-01395",
            "parentChildAnyZone": "LIME ROCK",
            "parentChildSameZone": "5950",
            "percentInZone": 100,
            "perfLateralLength": 2,
            "permitDate": "2012-06-06T00:00:00Z",
            "phdwinId": "9E5F5CC579867509254700023",
            "play": "EAGLEBINE",
            "porosity": 9,
            "previousOperator": "EXXON MOBIL",
            "previousOperatorAlias": "XTO ENERGY",
            "previousOperatorCode": "XT",
            "previousOperatorTicker": "XOM",
            "primaryProduct": "GAS",
            "prmsReservesCategory": "Proved",
            "prmsReservesSubCategory": "Producing",
            "prmsResourcesClass": "Standard",
            "productionMethod": "PUMPING",
            "proppantMeshSize": "100M/4070/",
            "proppantType": "RSWhite/Brown/",
            "range": "26W",
            "recoveryMethod": "Regular",
            "refracAdditiveVolume": 1370,
            "refracClusterCount": 20,
            "refracDate": "2020-09-09T00:00:00Z",
            "refracFluidPerPerforatedInterval": 2.5248802064135645,
            "refracFluidVolume": 13700,
            "refracFracVendor": "BAKER HUGHES",
            "refracMaxInjectionPressure": 23,
            "refracMaxInjectionRate": 0.42,
            "refracPropWeight": 8,
            "refracProppantPerFluid": 4.957037815996877e-11,
            "refracProppantPerPerforatedInterval": 10,
            "refracStageCount": 2,
            "refracTreatmentType": "CROSSLINK HC",
            "rig": "RIG-1",
            "rs": 1,
            "rsegId": "421",
            "scope": "company",
            "section": "71",
            "sg": 0.595085877,
            "so": 40,
            "spudDate": "2012-01-06T00:00:00Z",
            "stageSpacing": 12,
            "state": "TX",
            "status": "INACTIVE",
            "subplay": "EAGLEVILLE",
            "surfaceLatitude": 30.3288694,
            "surfaceLongitude": -96.3641278,
            "survey": "COLES, J P",
            "sw": 30,
            "targetFormation": "AUSTIN CHALK, GAS",
            "tgsId": "147",
            "thickness": 70,
            "til": "2020-10-26T20:45:51.482Z",
            "toeInLandingZone": "Y",
            "toeLatitude": 30.3332851,
            "toeLongitude": -96.3631776,
            "toeUp": "02/01/2013",
            "totalAdditiveVolume": 400450,
            "totalClusterCount": 35,
            "totalFluidPerPerforatedInterval": 34.21673724091821,
            "totalFluidVolume": 425134,
            "totalPropWeight": 8840026,
            "totalProppantPerFluid": 1.225148340912877,
            "totalProppantPerPerforatedInterval": 1149.3987777922248,
            "totalStageCount": 31,
            "township": "001N",
            "trueVerticalDepth": 12691.52,
            "tubingDepth": 741006,
            "tubingId": 21,
            "typeCurveArea": "1000 GOR",
            "updatedAt": "2020-07-26T15:29:00.352Z",
            "upperPerforation": 12226,
            "verticalSpacing": 10,
            "vtWellSpacingAnyZone": 11,
            "vtWellSpacingSameZone": 10,
            "wellName": "SCHAWE-WOLFF",
            "wellNumber": "1H",
            "wellType": "GAS",
            "zi": 23
        }
"""

post_patch_put_wells_response = """
        Example data:
        [
            {
                "dataSource": "<string>",
                "abstract": "<string>",
                "acreSpacing": "<number>",
                "allocationType": "<string>",
                "api10": "<string>",
                "api12": "<string>",
                "api14": "<string>",
                "ariesId": "<string>",
                "azimuth": "<number>",
                "basin": "<string>",
                "bg": "<number>",
                "block": "<string>",
                "bo": "<number>",
                "bubblePointPress": "<number>",
                "casingId": "<number>",
                "chokeSize": "<number>",
                "chosenID": "<string>",
                "chosenKeyID": "<string>",
                "completionDesign": "<string>",
                "completionEndDate": "<date>",
                "completionStartDate": "<date>",
                "country": "<string>",
                "county": "<string>",
                "currentOperator": "<string>",
                "currentOperatorAlias": "<string>",
                "currentOperatorCode": "<string>",
                "currentOperatorTicker": "<string>",
                "customBool0": "<boolean>",
                "customBool1": "<boolean>",
                "customBool2": "<boolean>",
                "customBool3": "<boolean>",
                "customBool4": "<boolean>",
                "customDate0": "<date>",
                "customDate1": "<date>",
                "customDate2": "<date>",
                "customDate3": "<date>",
                "customDate4": "<date>",
                "customDate5": "<date>",
                "customDate6": "<date>",
                "customDate7": "<date>",
                "customDate8": "<date>",
                "customDate9": "<date>",
                "customNumber0": "<number>",
                "customNumber1": "<number>",
                "customNumber10": "<number>",
                "customNumber11": "<number>",
                "customNumber12": "<number>",
                "customNumber13": "<number>",
                "customNumber14": "<number>",
                "customNumber15": "<number>",
                "customNumber16": "<number>",
                "customNumber17": "<number>",
                "customNumber18": "<number>",
                "customNumber19": "<number>",
                "customNumber2": "<number>",
                "customNumber3": "<number>",
                "customNumber4": "<number>",
                "customNumber5": "<number>",
                "customNumber6": "<number>",
                "customNumber7": "<number>",
                "customNumber8": "<number>",
                "customNumber9": "<number>",
                "customString0": "<string>",
                "customString1": "<string>",
                "customString10": "<string>",
                "customString11": "<string>",
                "customString12": "<string>",
                "customString13": "<string>",
                "customString14": "<string>",
                "customString15": "<string>",
                "customString16": "<string>",
                "customString17": "<string>",
                "customString18": "<string>",
                "customString19": "<string>",
                "customString2": "<string>",
                "customString3": "<string>",
                "customString4": "<string>",
                "customString5": "<string>",
                "customString6": "<string>",
                "customString7": "<string>",
                "customString8": "<string>",
                "customString9": "<string>",
                "dataSourceCustomName": "<string>",
                "dateRigRelease": "<date>",
                "dewPointPress": "<number>",
                "distanceFromBaseOfZone": "<number>",
                "distanceFromTopOfZone": "<number>",
                "district": "<string>",
                "drainageArea": "<number>",
                "drillEndDate": "<date>",
                "drillStartDate": "<date>",
                "drillinginfoId": "<string>",
                "elevation": "<number>",
                "elevationType": "<string>",
                "field": "<string>",
                "firstAdditiveVolume": "<number>",
                "firstClusterCount": "<number>",
                "firstFluidVolume": "<number>",
                "firstFracVendor": "<string>",
                "firstMaxInjectionPressure": "<number>",
                "firstMaxInjectionRate": "<number>",
                "firstProdDate": "<date>",
                "firstPropWeight": "<number>",
                "firstStageCount": "<number>",
                "firstTestFlowTbgPress": "<number>",
                "firstTestGasVol": "<number>",
                "firstTestGor": "<number>",
                "firstTestOilVol": "<number>",
                "firstTestWaterVol": "<number>",
                "firstTreatmentType": "<string>",
                "flowPath": "<string>",
                "fluidType": "<string>",
                "footageInLandingZone": "<number>",
                "formationThicknessMean": "<number>",
                "fractureConductivity": "<number>",
                "gasAnalysisDate": "<date>",
                "gasC1": "<number>",
                "gasC2": "<number>",
                "gasC3": "<number>",
                "gasCo2": "<number>",
                "gasGatherer": "<string>",
                "gasH2": "<number>",
                "gasH2o": "<number>",
                "gasH2s": "<number>",
                "gasHe": "<number>",
                "gasIc4": "<number>",
                "gasIc5": "<number>",
                "gasN2": "<number>",
                "gasNc10": "<number>",
                "gasNc4": "<number>",
                "gasNc5": "<number>",
                "gasNc6": "<number>",
                "gasNc7": "<number>",
                "gasNc8": "<number>",
                "gasNc9": "<number>",
                "gasO2": "<number>",
                "gasSpecificGravity": "<number>",
                "grossPerforatedInterval": "<number>",
                "groundElevation": "<number>",
                "heelLatitude": "<number>",
                "heelLongitude": "<number>",
                "holeDirection": "<string>",
                "horizontalSpacing": "<number>",
                "hzWellSpacingAnyZone": "<number>",
                "hzWellSpacingSameZone": "<number>",
                "id": "<string>",
                "ihsId": "<string>",
                "initialRespress": "<number>",
                "initialRestemp": "<number>",
                "landingZone": "<string>",
                "landingZoneBase": "<number>",
                "landingZoneTop": "<number>",
                "lateralLength": "<number>",
                "leaseName": "<string>",
                "leaseNumber": "<string>",
                "lowerPerforation": "<number>",
                "matrixPermeability": "<number>",
                "measuredDepth": "<number>",
                "nglGatherer": "<string>",
                "numTreatmentRecords": "<number>",
                "oilApiGravity": "<number>",
                "oilGatherer": "<string>",
                "oilSpecificGravity": "<number>",
                "padName": "<string>",
                "parentChildAnyZone": "<string>",
                "parentChildSameZone": "<string>",
                "percentInZone": "<number>",
                "perfLateralLength": "<number>",
                "permitDate": "<date>",
                "phdwinId": "<string>",
                "play": "<string>",
                "porosity": "<number>",
                "previousOperator": "<string>",
                "previousOperatorAlias": "<string>",
                "previousOperatorCode": "<string>",
                "previousOperatorTicker": "<string>",
                "primaryProduct": "<string>",
                "prmsReservesCategory": "<string>",
                "prmsReservesSubCategory": "<string>",
                "prmsResourcesClass": "<string>",
                "productionMethod": "<string>",
                "proppantMeshSize": "<string>",
                "proppantType": "<string>",
                "range": "<string>",
                "recoveryMethod": "<string>",
                "refracAdditiveVolume": "<number>",
                "refracClusterCount": "<number>",
                "refracDate": "<date>",
                "refracFluidVolume": "<number>",
                "refracFracVendor": "<string>",
                "refracMaxInjectionPressure": "<number>",
                "refracMaxInjectionRate": "<number>",
                "refracPropWeight": "<number>",
                "refracStageCount": "<number>",
                "refracTreatmentType": "<string>",
                "rig": "<string>",
                "rs": "<number>",
                "rsegId": "<string>",
                "section": "<string>",
                "sg": "<number>",
                "so": "<number>",
                "spudDate": "<date>",
                "stageSpacing": "<number>",
                "state": "<string>",
                "status": "<string>",
                "subplay": "<string>",
                "surfaceLatitude": "<number>",
                "surfaceLongitude": "<number>",
                "survey": "<string>",
                "sw": "<number>",
                "targetFormation": "<string>",
                "tgsId": "<string>",
                "thickness": "<number>",
                "til": "<date>",
                "toeInLandingZone": "<string>",
                "toeLatitude": "<number>",
                "toeLongitude": "<number>",
                "toeUp": "<string>",
                "township": "<string>",
                "trueVerticalDepth": "<number>",
                "tubingDepth": "<number>",
                "tubingId": "<number>",
                "typeCurveArea": "<string>",
                "upperPerforation": "<number>",
                "verticalSpacing": "<number>",
                "vtWellSpacingAnyZone": "<number>",
                "vtWellSpacingSameZone": "<number>",
                "wellName": "<string>",
                "wellNumber": "<string>",
                "wellType": "<string>",
                "zi": "<number>"
            },
            {
                "dataSource": "<string>",
                "abstract": "<string>",
                "acreSpacing": "<number>",
                "allocationType": "<string>",
                "api10": "<string>",
                "api12": "<string>",
                "api14": "<string>",
                "ariesId": "<string>",
                "azimuth": "<number>",
                "basin": "<string>",
                "bg": "<number>",
                "block": "<string>",
                "bo": "<number>",
                "bubblePointPress": "<number>",
                "casingId": "<number>",
                "chokeSize": "<number>",
                "chosenID": "<string>",
                "chosenKeyID": "<string>",
                "completionDesign": "<string>",
                "completionEndDate": "<date>",
                "completionStartDate": "<date>",
                "country": "<string>",
                "county": "<string>",
                "currentOperator": "<string>",
                "currentOperatorAlias": "<string>",
                "currentOperatorCode": "<string>",
                "currentOperatorTicker": "<string>",
                "customBool0": "<boolean>",
                "customBool1": "<boolean>",
                "customBool2": "<boolean>",
                "customBool3": "<boolean>",
                "customBool4": "<boolean>",
                "customDate0": "<date>",
                "customDate1": "<date>",
                "customDate2": "<date>",
                "customDate3": "<date>",
                "customDate4": "<date>",
                "customDate5": "<date>",
                "customDate6": "<date>",
                "customDate7": "<date>",
                "customDate8": "<date>",
                "customDate9": "<date>",
                "customNumber0": "<number>",
                "customNumber1": "<number>",
                "customNumber10": "<number>",
                "customNumber11": "<number>",
                "customNumber12": "<number>",
                "customNumber13": "<number>",
                "customNumber14": "<number>",
                "customNumber15": "<number>",
                "customNumber16": "<number>",
                "customNumber17": "<number>",
                "customNumber18": "<number>",
                "customNumber19": "<number>",
                "customNumber2": "<number>",
                "customNumber3": "<number>",
                "customNumber4": "<number>",
                "customNumber5": "<number>",
                "customNumber6": "<number>",
                "customNumber7": "<number>",
                "customNumber8": "<number>",
                "customNumber9": "<number>",
                "customString0": "<string>",
                "customString1": "<string>",
                "customString10": "<string>",
                "customString11": "<string>",
                "customString12": "<string>",
                "customString13": "<string>",
                "customString14": "<string>",
                "customString15": "<string>",
                "customString16": "<string>",
                "customString17": "<string>",
                "customString18": "<string>",
                "customString19": "<string>",
                "customString2": "<string>",
                "customString3": "<string>",
                "customString4": "<string>",
                "customString5": "<string>",
                "customString6": "<string>",
                "customString7": "<string>",
                "customString8": "<string>",
                "customString9": "<string>",
                "dataSourceCustomName": "<string>",
                "dateRigRelease": "<date>",
                "dewPointPress": "<number>",
                "distanceFromBaseOfZone": "<number>",
                "distanceFromTopOfZone": "<number>",
                "district": "<string>",
                "drainageArea": "<number>",
                "drillEndDate": "<date>",
                "drillStartDate": "<date>",
                "drillinginfoId": "<string>",
                "elevation": "<number>",
                "elevationType": "<string>",
                "field": "<string>",
                "firstAdditiveVolume": "<number>",
                "firstClusterCount": "<number>",
                "firstFluidVolume": "<number>",
                "firstFracVendor": "<string>",
                "firstMaxInjectionPressure": "<number>",
                "firstMaxInjectionRate": "<number>",
                "firstProdDate": "<date>",
                "firstPropWeight": "<number>",
                "firstStageCount": "<number>",
                "firstTestFlowTbgPress": "<number>",
                "firstTestGasVol": "<number>",
                "firstTestGor": "<number>",
                "firstTestOilVol": "<number>",
                "firstTestWaterVol": "<number>",
                "firstTreatmentType": "<string>",
                "flowPath": "<string>",
                "fluidType": "<string>",
                "footageInLandingZone": "<number>",
                "formationThicknessMean": "<number>",
                "fractureConductivity": "<number>",
                "gasAnalysisDate": "<date>",
                "gasC1": "<number>",
                "gasC2": "<number>",
                "gasC3": "<number>",
                "gasCo2": "<number>",
                "gasGatherer": "<string>",
                "gasH2": "<number>",
                "gasH2o": "<number>",
                "gasH2s": "<number>",
                "gasHe": "<number>",
                "gasIc4": "<number>",
                "gasIc5": "<number>",
                "gasN2": "<number>",
                "gasNc10": "<number>",
                "gasNc4": "<number>",
                "gasNc5": "<number>",
                "gasNc6": "<number>",
                "gasNc7": "<number>",
                "gasNc8": "<number>",
                "gasNc9": "<number>",
                "gasO2": "<number>",
                "gasSpecificGravity": "<number>",
                "grossPerforatedInterval": "<number>",
                "groundElevation": "<number>",
                "heelLatitude": "<number>",
                "heelLongitude": "<number>",
                "holeDirection": "<string>",
                "horizontalSpacing": "<number>",
                "hzWellSpacingAnyZone": "<number>",
                "hzWellSpacingSameZone": "<number>",
                "id": "<string>",
                "ihsId": "<string>",
                "initialRespress": "<number>",
                "initialRestemp": "<number>",
                "landingZone": "<string>",
                "landingZoneBase": "<number>",
                "landingZoneTop": "<number>",
                "lateralLength": "<number>",
                "leaseName": "<string>",
                "leaseNumber": "<string>",
                "lowerPerforation": "<number>",
                "matrixPermeability": "<number>",
                "measuredDepth": "<number>",
                "nglGatherer": "<string>",
                "numTreatmentRecords": "<number>",
                "oilApiGravity": "<number>",
                "oilGatherer": "<string>",
                "oilSpecificGravity": "<number>",
                "padName": "<string>",
                "parentChildAnyZone": "<string>",
                "parentChildSameZone": "<string>",
                "percentInZone": "<number>",
                "perfLateralLength": "<number>",
                "permitDate": "<date>",
                "phdwinId": "<string>",
                "play": "<string>",
                "porosity": "<number>",
                "previousOperator": "<string>",
                "previousOperatorAlias": "<string>",
                "previousOperatorCode": "<string>",
                "previousOperatorTicker": "<string>",
                "primaryProduct": "<string>",
                "prmsReservesCategory": "<string>",
                "prmsReservesSubCategory": "<string>",
                "prmsResourcesClass": "<string>",
                "productionMethod": "<string>",
                "proppantMeshSize": "<string>",
                "proppantType": "<string>",
                "range": "<string>",
                "recoveryMethod": "<string>",
                "refracAdditiveVolume": "<number>",
                "refracClusterCount": "<number>",
                "refracDate": "<date>",
                "refracFluidVolume": "<number>",
                "refracFracVendor": "<string>",
                "refracMaxInjectionPressure": "<number>",
                "refracMaxInjectionRate": "<number>",
                "refracPropWeight": "<number>",
                "refracStageCount": "<number>",
                "refracTreatmentType": "<string>",
                "rig": "<string>",
                "rs": "<number>",
                "rsegId": "<string>",
                "section": "<string>",
                "sg": "<number>",
                "so": "<number>",
                "spudDate": "<date>",
                "stageSpacing": "<number>",
                "state": "<string>",
                "status": "<string>",
                "subplay": "<string>",
                "surfaceLatitude": "<number>",
                "surfaceLongitude": "<number>",
                "survey": "<string>",
                "sw": "<number>",
                "targetFormation": "<string>",
                "tgsId": "<string>",
                "thickness": "<number>",
                "til": "<date>",
                "toeInLandingZone": "<string>",
                "toeLatitude": "<number>",
                "toeLongitude": "<number>",
                "toeUp": "<string>",
                "township": "<string>",
                "trueVerticalDepth": "<number>",
                "tubingDepth": "<number>",
                "tubingId": "<number>",
                "typeCurveArea": "<string>",
                "upperPerforation": "<number>",
                "verticalSpacing": "<number>",
                "vtWellSpacingAnyZone": "<number>",
                "vtWellSpacingSameZone": "<number>",
                "wellName": "<string>",
                "wellNumber": "<string>",
                "wellType": "<string>",
                "zi": "<number>"
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "ValidationError",
                    "message": "The field 'id' is required.",
                    "location": "In body of request at position [0]"
                },
                {
                    "name": "ValidationError",
                    "message": "The field 'dataSource' is required.",
                    "location": "In body of request at position [2]"
                }
            ],
            "results": [
                {
                    "status": "Success",
                    "code": 200,
                    "id": "62b1c13e2750169012ee4515",
                    "chosenID": "abc1234567890",
                    "dataSource": "di",
                    "createdAt": "2023-01-01T00:00:00.000Z",
                    "updatedAt": "2023-01-01T00:00:00.000Z"
                },
                {
                    "status": "Success",
                    "code": 200,
                    "id": "62b1c13e4857169000ee4613",
                    "chosenID": 1234567891,
                    "dataSource": "internal",
                    "createdAt": "2023-01-01T00:00:00.000Z",
                    "updatedAt": "2023-01-01T00:00:00.000Z"
                }
            ],
            "failedCount": 2,
            "successCount": 2
        }
"""

patch_put_well_response = """
        Example data:
                {
            "dataSource": "<string>",
            "abstract": "<string>",
            "acreSpacing": "<number>",
            "allocationType": "<string>",
            "api10": "<string>",
            "api12": "<string>",
            "api14": "<string>",
            "ariesId": "<string>",
            "azimuth": "<number>",
            "basin": "<string>",
            "bg": "<number>",
            "block": "<string>",
            "bo": "<number>",
            "bubblePointPress": "<number>",
            "casingId": "<number>",
            "chokeSize": "<number>",
            "chosenID": "<string>",
            "chosenKeyID": "<string>",
            "completionDesign": "<string>",
            "completionEndDate": "<date>",
            "completionStartDate": "<date>",
            "country": "<string>",
            "county": "<string>",
            "currentOperator": "<string>",
            "currentOperatorAlias": "<string>",
            "currentOperatorCode": "<string>",
            "currentOperatorTicker": "<string>",
            "customBool0": "<boolean>",
            "customBool1": "<boolean>",
            "customBool2": "<boolean>",
            "customBool3": "<boolean>",
            "customBool4": "<boolean>",
            "customDate0": "<date>",
            "customDate1": "<date>",
            "customDate2": "<date>",
            "customDate3": "<date>",
            "customDate4": "<date>",
            "customDate5": "<date>",
            "customDate6": "<date>",
            "customDate7": "<date>",
            "customDate8": "<date>",
            "customDate9": "<date>",
            "customNumber0": "<number>",
            "customNumber1": "<number>",
            "customNumber10": "<number>",
            "customNumber11": "<number>",
            "customNumber12": "<number>",
            "customNumber13": "<number>",
            "customNumber14": "<number>",
            "customNumber15": "<number>",
            "customNumber16": "<number>",
            "customNumber17": "<number>",
            "customNumber18": "<number>",
            "customNumber19": "<number>",
            "customNumber2": "<number>",
            "customNumber3": "<number>",
            "customNumber4": "<number>",
            "customNumber5": "<number>",
            "customNumber6": "<number>",
            "customNumber7": "<number>",
            "customNumber8": "<number>",
            "customNumber9": "<number>",
            "customString0": "<string>",
            "customString1": "<string>",
            "customString10": "<string>",
            "customString11": "<string>",
            "customString12": "<string>",
            "customString13": "<string>",
            "customString14": "<string>",
            "customString15": "<string>",
            "customString16": "<string>",
            "customString17": "<string>",
            "customString18": "<string>",
            "customString19": "<string>",
            "customString2": "<string>",
            "customString3": "<string>",
            "customString4": "<string>",
            "customString5": "<string>",
            "customString6": "<string>",
            "customString7": "<string>",
            "customString8": "<string>",
            "customString9": "<string>",
            "dataSourceCustomName": "<string>",
            "dateRigRelease": "<date>",
            "dewPointPress": "<number>",
            "distanceFromBaseOfZone": "<number>",
            "distanceFromTopOfZone": "<number>",
            "district": "<string>",
            "drainageArea": "<number>",
            "drillEndDate": "<date>",
            "drillStartDate": "<date>",
            "drillinginfoId": "<string>",
            "elevation": "<number>",
            "elevationType": "<string>",
            "field": "<string>",
            "firstAdditiveVolume": "<number>",
            "firstClusterCount": "<number>",
            "firstFluidVolume": "<number>",
            "firstFracVendor": "<string>",
            "firstMaxInjectionPressure": "<number>",
            "firstMaxInjectionRate": "<number>",
            "firstProdDate": "<date>",
            "firstPropWeight": "<number>",
            "firstStageCount": "<number>",
            "firstTestFlowTbgPress": "<number>",
            "firstTestGasVol": "<number>",
            "firstTestGor": "<number>",
            "firstTestOilVol": "<number>",
            "firstTestWaterVol": "<number>",
            "firstTreatmentType": "<string>",
            "flowPath": "<string>",
            "fluidType": "<string>",
            "footageInLandingZone": "<number>",
            "formationThicknessMean": "<number>",
            "fractureConductivity": "<number>",
            "gasAnalysisDate": "<date>",
            "gasC1": "<number>",
            "gasC2": "<number>",
            "gasC3": "<number>",
            "gasCo2": "<number>",
            "gasGatherer": "<string>",
            "gasH2": "<number>",
            "gasH2o": "<number>",
            "gasH2s": "<number>",
            "gasHe": "<number>",
            "gasIc4": "<number>",
            "gasIc5": "<number>",
            "gasN2": "<number>",
            "gasNc10": "<number>",
            "gasNc4": "<number>",
            "gasNc5": "<number>",
            "gasNc6": "<number>",
            "gasNc7": "<number>",
            "gasNc8": "<number>",
            "gasNc9": "<number>",
            "gasO2": "<number>",
            "gasSpecificGravity": "<number>",
            "grossPerforatedInterval": "<number>",
            "groundElevation": "<number>",
            "heelLatitude": "<number>",
            "heelLongitude": "<number>",
            "holeDirection": "<string>",
            "horizontalSpacing": "<number>",
            "hzWellSpacingAnyZone": "<number>",
            "hzWellSpacingSameZone": "<number>",
            "id": "<string>",
            "ihsId": "<string>",
            "initialRespress": "<number>",
            "initialRestemp": "<number>",
            "landingZone": "<string>",
            "landingZoneBase": "<number>",
            "landingZoneTop": "<number>",
            "lateralLength": "<number>",
            "leaseName": "<string>",
            "leaseNumber": "<string>",
            "lowerPerforation": "<number>",
            "matrixPermeability": "<number>",
            "measuredDepth": "<number>",
            "nglGatherer": "<string>",
            "numTreatmentRecords": "<number>",
            "oilApiGravity": "<number>",
            "oilGatherer": "<string>",
            "oilSpecificGravity": "<number>",
            "padName": "<string>",
            "parentChildAnyZone": "<string>",
            "parentChildSameZone": "<string>",
            "percentInZone": "<number>",
            "perfLateralLength": "<number>",
            "permitDate": "<date>",
            "phdwinId": "<string>",
            "play": "<string>",
            "porosity": "<number>",
            "previousOperator": "<string>",
            "previousOperatorAlias": "<string>",
            "previousOperatorCode": "<string>",
            "previousOperatorTicker": "<string>",
            "primaryProduct": "<string>",
            "prmsReservesCategory": "<string>",
            "prmsReservesSubCategory": "<string>",
            "prmsResourcesClass": "<string>",
            "productionMethod": "<string>",
            "proppantMeshSize": "<string>",
            "proppantType": "<string>",
            "range": "<string>",
            "recoveryMethod": "<string>",
            "refracAdditiveVolume": "<number>",
            "refracClusterCount": "<number>",
            "refracDate": "<date>",
            "refracFluidVolume": "<number>",
            "refracFracVendor": "<string>",
            "refracMaxInjectionPressure": "<number>",
            "refracMaxInjectionRate": "<number>",
            "refracPropWeight": "<number>",
            "refracStageCount": "<number>",
            "refracTreatmentType": "<string>",
            "rig": "<string>",
            "rs": "<number>",
            "rsegId": "<string>",
            "section": "<string>",
            "sg": "<number>",
            "so": "<number>",
            "spudDate": "<date>",
            "stageSpacing": "<number>",
            "state": "<string>",
            "status": "<string>",
            "subplay": "<string>",
            "surfaceLatitude": "<number>",
            "surfaceLongitude": "<number>",
            "survey": "<string>",
            "sw": "<number>",
            "targetFormation": "<string>",
            "tgsId": "<string>",
            "thickness": "<number>",
            "til": "<date>",
            "toeInLandingZone": "<string>",
            "toeLatitude": "<number>",
            "toeLongitude": "<number>",
            "toeUp": "<string>",
            "township": "<string>",
            "trueVerticalDepth": "<number>",
            "tubingDepth": "<number>",
            "tubingId": "<number>",
            "typeCurveArea": "<string>",
            "upperPerforation": "<number>",
            "verticalSpacing": "<number>",
            "vtWellSpacingAnyZone": "<number>",
            "vtWellSpacingSameZone": "<number>",
            "wellName": "<string>",
            "wellNumber": "<string>",
            "wellType": "<string>",
            "zi": "<number>"
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
