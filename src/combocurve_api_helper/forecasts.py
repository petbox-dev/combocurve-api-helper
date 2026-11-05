import warnings
from collections.abc import Mapping
from types import MappingProxyType
from typing import Callable, Optional, cast

from more_itertools import chunked

from ._batch import BatchChunk, BatchWriteResult
from .base import LIST_SORT_ORDER, WELL_LIST_SORT_ORDER, APIBase, Item, ItemList, WriteResponse

GET_LIMIT = 200
GET_LIMIT_OUTPUTS_ARIES = 1000


# Forecast volume rows are keyed by well only.
_VOLUME_SORT_ORDER: Mapping[str, int] = MappingProxyType({'well': 0})


class Forecasts(APIBase):
    ######
    # URLs
    ######

    def get_forecasts_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of forecasts for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_by_id_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url for a specific forecast from its forecast id.
        """
        base_url = self.get_forecasts_url(project_id)
        return f'{base_url}/{forecast_id}'

    def get_forecast_wells_url(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a specific forecast's wells from its forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/wells'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_aries_url(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a specific forecast's ARIES parameters from its forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/aries'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_outputs_url(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a specific forecast outputs from its forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/outputs'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_output_by_id_url(self, project_id: str, forecast_id: str, output_id: str) -> str:
        """
        Returns the API url for a specific forecast output from its forecast id and output id.
        """
        base_url = self.get_forecast_outputs_url(project_id, forecast_id)
        return f'{base_url}/{output_id}'

    def get_forecast_daily_volumes_url(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for daily volumes for a specific project id and forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/daily-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_monthly_volumes_url(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for monthly volumes for a specific project id and forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/monthly-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_segment_parameters_url(
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str
    ) -> str:
        """
        Returns the API url for a specific forecast segment parameters from its
        forecast id, well id, phase, and series.
        """

        VALID_PHASES = ['oil', 'gas', 'water']
        VALID_SERIES = ['best', 'p10', 'p50', 'p90']

        if phase.lower() not in VALID_PHASES:
            warnings.warn(f"`phase` '{phase}' is not in list of valid names:\n{VALID_PHASES}", stacklevel=2)

        if series.lower() not in VALID_SERIES:
            warnings.warn(f"`series` '{series}' is not in list of valid names:\n{VALID_SERIES}", stacklevel=2)

        phase = phase.lower()
        series = series.lower()

        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/parameters/{well_id}/{phase}/{series}'

        return url

    ###########
    # API calls
    ###########

    def get_forecasts(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of forecasts for a specific project id.

        https://docs.api.combocurve.com/api/get-forecasts

        Example response:
        [
            {
                "createdAt": "2020-01-01",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "runDate": "2020-01-01",
                "running": true,
                "tags": [
                    {
                        "createdAt": "2020-01-01",
                        "description": "string",
                        "name": "Example",
                        "updatedAt": "2020-01-01"
                    }
                ],
                "type": "string",
                "updatedAt": "2020-01-01"
            }
        ]
        """
        url = self.get_forecasts_url(project_id, filters)
        params = {'take': GET_LIMIT}
        forecasts = self._get_items(url, params)

        return self._keysort(forecasts, LIST_SORT_ORDER)

    def count_forecasts(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of forecasts in a project matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-forecasts
        """
        return self._count_items(self.get_forecasts_url(project_id, filters))

    def post_forecasts(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates new forecasts for a specific project id.

        https://docs.api.combocurve.com/api/post-forecasts

        Example data:
        [
            {
                "name": "Example",
                "type": "string"
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
                    "forecastId": "5e272d38b78910dd2a1bd691",
                    "name": "Example",
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
        url = self.get_forecasts_url(project_id)
        forecasts = cast('list[WriteResponse]', self._post_items(url, data))

        return forecasts

    def post_forecast_wells(
        self,
        project_id: str,
        forecast_id: str,
        well_ids: list[str],
        *,
        chunksize: int = 100,
    ) -> ItemList:
        """
        Scope a list of well id's to a specific forecast, for a given project.

        Optionally, specify the `chunksize` to control how many wells are posted
        per request to avoid HTTP 413 Content Too Large or 504 Gateway Timeout errors
        when making requests to the ComboCurve API.

        https://docs.api.combocurve.com/api/post-wells-to-forecast
        """
        # NOTE: we can't use `self._post_items` since it expects the base data to be a list
        # whereas this particular endpoint receives an object

        url = self.get_forecast_wells_url(project_id, forecast_id)

        items: ItemList = []
        for well_ids_chunk in chunked(well_ids, chunksize):
            data = {'wellIds': well_ids_chunk}
            response = self._request_with_retry('post', url, json_body=data)
            response.raise_for_status()

            items.extend(self._extract_json(response))

        return items

    def get_forecast_wells(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns the wells scoped to a specific forecast, as full project well objects.

        https://docs.api.combocurve.com/api/get-forecast-wells

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
                "projectCustomHeader": "string",
                "projectCustomHeader1": "string",
                "projectCustomHeader2": "string",
                "projectCustomHeader3": "string",
                "projectCustomHeader4": "string",
                "projectCustomHeader5": "string",
                "projectCustomHeader6": "string",
                "projectCustomHeader7": "string",
                "projectCustomHeader8": "string",
                "projectCustomHeader9": "string",
                "projectCustomHeader10": "string",
                "projectCustomHeader11": "string",
                "projectCustomHeader12": "string",
                "projectCustomHeader13": "string",
                "projectCustomHeader14": "string",
                "projectCustomHeader15": "string",
                "projectCustomHeader16": "string",
                "projectCustomHeader17": "string",
                "projectCustomHeader18": "string",
                "projectCustomHeader19": "string",
                "projectCustomHeader20": "string",
                "projectCustomHeader21": "string",
                "projectCustomHeader22": "string",
                "projectCustomHeader23": "string",
                "projectCustomHeader24": "string",
                "projectCustomHeader25": "string",
                "projectCustomHeader26": "string",
                "projectCustomHeader27": "string",
                "projectCustomHeader28": "string",
                "projectCustomHeader29": "string",
                "projectCustomHeader30": "string",
                "projectCustomHeader31": "string",
                "projectCustomHeader32": "string",
                "projectCustomHeader33": "string",
                "projectCustomHeader34": "string",
                "projectCustomHeader35": "string",
                "projectCustomHeader36": "string",
                "projectCustomHeader37": "string",
                "projectCustomHeader38": "string",
                "projectCustomHeader39": "string",
                "projectCustomHeader40": "string",
                "projectCustomHeader41": "string",
                "projectCustomHeader42": "string",
                "projectCustomHeader43": "string",
                "projectCustomHeader44": "string",
                "projectCustomHeader45": "string",
                "projectCustomHeader46": "string",
                "projectCustomHeader47": "string",
                "projectCustomHeader48": "string",
                "projectCustomHeader49": "string",
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
                "heelTrueVerticalDepth": 123.45,
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
                "midpointLatitude": 123.45,
                "midpointLongitude": 123.45,
                "midpointTrueVerticalDepth": 123.45,
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
                "toeTrueVerticalDepth": 123.45,
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
                "firstDiscountCashFlow": 123.45,
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
        url = self.get_forecast_wells_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params=params)

        return self._keysort(wells, WELL_LIST_SORT_ORDER)

    def count_forecast_wells(self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of wells scoped to a specific forecast that match the filters.

        https://docs.api.combocurve.com/api/head-forecast-wells
        """
        return self._count_items(self.get_forecast_wells_url(project_id, forecast_id, filters))

    def get_forecast_by_id(self, project_id: str, forecast_id: str) -> Item:
        """
        Returns a specific forecast from its forecast id.

        https://docs.api.combocurve.com/api/get-forecast-by-id

        Example response:
        {
            "createdAt": "2020-01-01",
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "runDate": "2020-01-01",
            "running": true,
            "tags": [
                {
                    "createdAt": "2020-01-01",
                    "description": "string",
                    "name": "Example",
                    "updatedAt": "2020-01-01"
                }
            ],
            "type": "string",
            "updatedAt": "2020-01-01"
        }
        """
        url = self.get_forecast_by_id_url(project_id, forecast_id)
        params = {'take': GET_LIMIT}
        forecasts = self._get_items(url, params)

        return forecasts[0]

    def delete_forecast_by_id(self, project_id: str, forecast_id: str) -> ItemList:
        """
        Deletes a specific forecast from its project id and forecast id.

        https://docs.api.combocurve.com/api/delete-forecast-by-id
        """
        url = self.get_forecast_by_id_url(project_id, forecast_id)
        return self._delete_items(url, data=[])

    def patch_forecast_by_id(self, project_id: str, forecast_id: str, data: Item) -> Item:
        """
        Partially updates a specific forecast (e.g. its `name`) from its project
        id and forecast id.

        https://docs.api.combocurve.com/api/patch-forecast

        Example data:
        {
            "name": "Example"
        }

        Example response:
        {
            "status": "string",
            "code": 123,
            "forecastId": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "errors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ]
        }
        """
        # The by-id PATCH endpoint receives a single object body (e.g. {'name': ...}),
        # not a list, so `self._patch_items` (which chunks a list) does not apply.
        url = self.get_forecast_by_id_url(project_id, forecast_id)

        response = self._request_with_retry('patch', url, json_body=data)
        response.raise_for_status()

        return self._extract_json(response)[0]

    def get_forecast_aries(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of ARIES parameters for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-aries-forecast

        Example response:
        [
            {
                "forecast": [
                    {
                        "PROPNUM": "string",
                        "WELL NAME": "string",
                        "WELL NUMBER": "string",
                        "INPT ID": "string",
                        "API10": "string",
                        "API12": "string",
                        "API14": "string",
                        "CHOSEN ID": "string",
                        "ARIES ID": "string",
                        "PHDWIN ID": "string",
                        "SECTION": 123,
                        "SEQUENCE": 123,
                        "QUALIFIER": "string",
                        "KEYWORD": "string",
                        "EXPRESSION": "string"
                    }
                ],
                "well": "string"
            }
        ]
        """
        url = self.get_forecast_aries_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)

    def count_forecast_aries(self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of ARIES forecast documents matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-aries-forecast
        """
        return self._count_items(self.get_forecast_aries_url(project_id, forecast_id, filters))

    def get_forecast_outputs(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of outputs for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-forecast-outputs

        Example response:
        [
            {
                "best": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45,
                            "slopeValue": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "createdAt": "2020-01-01",
                "forecasted": true,
                "forecastedAt": "2020-01-01",
                "forecastedBy": "string",
                "id": "5e272d38b78910dd2a1bd691",
                "forecast": "string",
                "forecastType": "string",
                "forecastSubType": "string",
                "p10": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45,
                            "slopeValue": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "p50": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45,
                            "slopeValue": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "p90": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45,
                            "slopeValue": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "phase": "string",
                "ratio": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45,
                            "slopeValue": 123.45
                        }
                    ],
                    "basePhase": "string",
                    "eur": 123.45
                },
                "reviewedAt": "2020-01-01",
                "reviewedBy": "string",
                "runDate": "2020-01-01",
                "status": "string",
                "typeCurve": "string",
                "typeCurveApplySettings": {
                    "applyNormalization": true,
                    "fpdSource": "string",
                    "riskFactor": 123.45
                },
                "typeCurveData": {
                    "name": "Example",
                    "type": "string"
                },
                "updatedAt": "2020-01-01",
                "well": "string",
                "data_freq": "string"
            }
        ]
        """
        url = self.get_forecast_outputs_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)

    def count_forecast_outputs(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> int:
        """
        Returns the number of forecast outputs matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-forecast-outputs
        """
        return self._count_items(self.get_forecast_outputs_url(project_id, forecast_id, filters))

    def get_forecast_output_by_id(self, project_id: str, forecast_id: str, output_id: str) -> Item:
        """
        Returns a specific forecast output from its forecast id and output id.

        https://docs.api.combocurve.com/api/get-forecast-output-by-id

        Example response:
        {
            "best": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45,
                        "slopeValue": 123.45
                    }
                ],
                "eur": 123.45
            },
            "createdAt": "2020-01-01",
            "forecasted": true,
            "forecastedAt": "2020-01-01",
            "forecastedBy": "string",
            "id": "5e272d38b78910dd2a1bd691",
            "forecast": "string",
            "forecastType": "string",
            "forecastSubType": "string",
            "p10": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45,
                        "slopeValue": 123.45
                    }
                ],
                "eur": 123.45
            },
            "p50": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45,
                        "slopeValue": 123.45
                    }
                ],
                "eur": 123.45
            },
            "p90": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45,
                        "slopeValue": 123.45
                    }
                ],
                "eur": 123.45
            },
            "phase": "string",
            "ratio": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45,
                        "slopeValue": 123.45
                    }
                ],
                "basePhase": "string",
                "eur": 123.45
            },
            "reviewedAt": "2020-01-01",
            "reviewedBy": "string",
            "runDate": "2020-01-01",
            "status": "string",
            "typeCurve": "string",
            "typeCurveApplySettings": {
                "applyNormalization": true,
                "fpdSource": "string",
                "riskFactor": 123.45
            },
            "typeCurveData": {
                "name": "Example",
                "type": "string"
            },
            "updatedAt": "2020-01-01",
            "well": "string",
            "data_freq": "string"
        }
        """
        url = self.get_forecast_output_by_id_url(project_id, forecast_id, output_id)
        params = {'take': GET_LIMIT}
        outputs = self._get_items(url, params)

        return outputs[0]

    def get_forecast_daily_volumes(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of daily volumes for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-forecast-daily-volumes

        Example response:
        [
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "probabilistic",
                "well": "string",
                "resolution": "monthly",
                "phases": [
                    {
                        "phase": "customNumber3",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P50",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "water",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    }
                ]
            }
        ]
        """
        url = self.get_forecast_daily_volumes_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        daily_volumes = self._get_items(url, params)

        return self._keysort(daily_volumes, _VOLUME_SORT_ORDER)

    def count_forecast_daily_volumes(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> int:
        """
        Returns the number of forecast daily-volume documents matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-forecast-daily-volumes
        """
        return self._count_items(self.get_forecast_daily_volumes_url(project_id, forecast_id, filters))

    def get_forecast_monthly_volumes(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of monthly volumes for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-forecast-monthly-volumes

        Example response:
        [
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "probabilistic",
                "well": "string",
                "resolution": "monthly",
                "phases": [
                    {
                        "phase": "customNumber3",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P50",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "water",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    }
                ]
            }
        ]
        """
        url = self.get_forecast_monthly_volumes_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        monthly_volumes = self._get_items(url, params)

        return self._keysort(monthly_volumes, _VOLUME_SORT_ORDER)

    def count_forecast_monthly_volumes(
        self, project_id: str, forecast_id: str, filters: Optional[dict[str, str]] = None
    ) -> int:
        """
        Returns the number of forecast monthly-volume documents matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-forecast-monthly-volumes
        """
        return self._count_items(self.get_forecast_monthly_volumes_url(project_id, forecast_id, filters))

    def post_forecast_segment_parameters(
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str, data: ItemList
    ) -> list[WriteResponse]:
        """
        Inserts a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/api/post-projects-forecast-segment-parameters

        Example data:
        [
            {
                "segmentType": "string",
                "startDate": "string",
                "endDate": "string",
                "qStart": 123.45,
                "qEnd": 123.45,
                "diEffSec": 123.45,
                "b": 123.45,
                "targetDSwEffSec": 123.45,
                "flatValue": 123.45,
                "slope": 123.45,
                "realizedDEffSw": 123.45,
                "d": 123.45,
                "dEff": 123.45,
                "calculatedField": "string"
            }
        ]

        Example response:
        {
            "status": "string",
            "segmentCount": 123,
            "id": "5e272d38b78910dd2a1bd691"
        }
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = cast('list[WriteResponse]', self._post_items(url, data))

        return segments

    def put_forecast_segment_parameters(
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str, data: ItemList
    ) -> list[WriteResponse]:
        """
        Updates a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/api/put-projects-forecast-segment-parameters

        Example data:
        [
            {
                "segmentType": "string",
                "startDate": "string",
                "endDate": "string",
                "qStart": 123.45,
                "qEnd": 123.45,
                "diEffSec": 123.45,
                "b": 123.45,
                "targetDSwEffSec": 123.45,
                "flatValue": 123.45,
                "slope": 123.45,
                "realizedDEffSw": 123.45,
                "d": 123.45,
                "dEff": 123.45,
                "calculatedField": "string"
            }
        ]

        Example response:
        {
            "status": "string",
            "segmentCount": 123,
            "id": "5e272d38b78910dd2a1bd691"
        }
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = cast('list[WriteResponse]', self._put_items(url, data))

        return segments

    def delete_forecast_segment_parameters(
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str
    ) -> ItemList:
        """
        Deletes a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/api/delete-projects-forecast-segment-parameters
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._delete_items(url, data=[])

        return segments

    # Bulk forecast parameters (whole-forecast PUT) and forecast run (async job)

    def get_forecast_parameters_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url for a forecast's parameters (bulk, whole-forecast).
        Route: /v1/projects/{projectId}/forecasts/{forecastId}/parameters
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        return f'{base_url}/parameters'

    def put_forecast_parameters(
        self, project_id: str, forecast_id: str, data: ItemList, *, chunksize: int = 25
    ) -> list[WriteResponse]:
        """
        Upserts forecast parameters in bulk for a specific forecast. Each item in
        `data` is one well x phase record ({well, phase, series, forecastType,
        segments, ...}); see `put_forecast_segment_parameters` for the
        single-well variant.

        The endpoint accepts at most 25 well x phase records per PUT, so `data`
        is chunked into groups of `chunksize` (default 25) and each chunk is sent
        as a separate request. A record is one well x phase (not one decline
        segment), so 25 records is e.g. ~8 wells across oil/gas/water; there is
        no separate per-segment limit.
        """
        url = self.get_forecast_parameters_url(project_id, forecast_id)
        return cast('list[WriteResponse]', self._put_items(url, data, chunksize))

    def put_forecast_parameters_batched(
        self,
        project_id: str,
        forecast_id: str,
        data: ItemList,
        *,
        chunksize: int = 25,
        max_workers: int = 10,
        on_progress: Optional[Callable[[BatchChunk], None]] = None,
    ) -> BatchWriteResult:
        """Upsert forecast parameters in parallel chunks, returning the 207 envelope.

        Like `put_forecast_parameters`, but sends the (max 25 well x phase
        record) chunks concurrently and returns a `BatchWriteResult` instead of a
        flattened `ItemList`. The endpoint replies 207 Multi-Status, so
        ``result.results[i]`` corresponds to ``data[i]`` and per-record failures
        are preserved (``result.failed_count`` / ``result.ok``) rather than
        silently dropped. Prefer this when you need to detect partial failures or
        want parallel throughput; `on_progress` is called once per completed
        chunk (from the calling thread) for progress reporting.

        A failed chunk with `may_have_applied=True` (a gateway status, or a connection
        lost after the chunk was sent) is counted in `failed_count`, but the server may
        have applied it: check the server before sending it again.
        """
        url = self.get_forecast_parameters_url(project_id, forecast_id)
        return self._request_batched(
            'put', url, data, chunksize=chunksize, max_workers=max_workers, on_progress=on_progress
        )

    def get_forecast_run_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url to run a specific forecast.
        Route: /v1/projects/{projectId}/forecasts/{forecastId}/run
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        return f'{base_url}/run'

    def get_forecast_run_by_job_id_url(self, project_id: str, forecast_id: str, job_id: str) -> str:
        """
        Returns the API url for the status of a specific forecast run job.
        Route: /v1/projects/{projectId}/forecasts/{forecastId}/run/{jobId}
        """
        base_url = self.get_forecast_run_url(project_id, forecast_id)
        return f'{base_url}/{job_id}'

    def post_forecast_run(self, project_id: str, forecast_id: str, configuration_id: Optional[str] = None) -> ItemList:
        """
        Starts an (async) run of a specific forecast, optionally using a named
        forecast configuration. Returns the run job (carrying its `jobId`); poll
        `get_forecast_run_by_job_id` for status.
        """
        # The run endpoint receives a single object body ({configurationId}), not
        # a list, so `self._post_items` (which chunks a list) does not apply.
        url = self.get_forecast_run_url(project_id, forecast_id)

        data: dict[str, str] = {}
        if configuration_id is not None:
            data['configurationId'] = configuration_id

        response = self._request_with_retry('post', url, json_body=data)
        response.raise_for_status()

        return self._extract_json(response)

    def get_forecast_run_by_job_id(self, project_id: str, forecast_id: str, job_id: str) -> Item:
        """
        Returns the status of a specific forecast run job from its job id.
        """
        url = self.get_forecast_run_by_job_id_url(project_id, forecast_id, job_id)
        jobs = self._get_items(url)

        return jobs[0]
