import requests
import warnings

from combocurve_api_v1.pagination import get_next_page_url

from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList


GET_LIMIT = 200
GET_LIMIT_MONTHLY_EXPORTS = 100
CONCURRENCY_MONTHLY_EXPORTS = 10


def flatten_outputs(result: Item) -> Optional[Item]:
    if 'output' not in result:
        return None

    output = result.pop('output')

    # this happens is a well has no economic output, i.e. no forecast or
    # ownership model. In this case some basic header information exists,
    # but the 'output' key is None. We return only the header data.
    if output is None:
        return {**result}  # type: ignore[unreachable]

    if not isinstance(output, dict):
        raise TypeError(f'Expected output to be a dict, got {type(output)}')

    out = {k: v for k, v in output.items()}
    return {**result, **out}


class EconRuns(APIBase):
    ######
    # URLs
    ######

    def get_econ_runs_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url of econ runs for a specific project id and
        scenario id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/scenarios/{scenario_id}/econ-runs'

    def get_econ_run_by_id_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for a specific econ run from its econ run id.
        """
        base_url = self.get_econ_runs_url(project_id, scenario_id)
        return f'{base_url}/{econ_run_id}'

    def get_econ_run_onelines_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for onelines for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/one-liners'

    def get_econ_run_combo_names_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for onelines for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_econ_run_onelines_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/combo-names'

    def get_econ_run_monthly_export_id_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for monthly exports for a specific project id,
        scenario id, and econ run id.
        """
        base_url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/monthly-exports'

    def get_econ_run_monthly_export_url(
        self, project_id: str, scenario_id: str, econ_run_id: str, monthly_export_id: str
    ) -> str:
        """
        Returns the API url for monthly exports for a specific project id,
        scenario id, econ run id,
        and monthly export id.
        """
        base_url = self.get_econ_run_monthly_export_id_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/{monthly_export_id}'

    def get_econ_run_oneline_by_id_url(
        self, project_id: str, scenario_id: str, econ_run_id: str, oneline_id: str
    ) -> str:
        """
        Returns the API url for a specific oneline from its oneline id.
        """
        base_url = self.get_econ_run_onelines_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/{oneline_id}'

    def get_econ_run_monthly_econ_result_by_id_url(
        self, project_id: str, scenario_id: str, econ_run_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for monthly econ results for a specific project id,
        scenario id, and econ run id.
        """
        base_url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        url = f'{base_url}/monthly-econ-results'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    ###########
    # API calls
    ###########

    def get_econ_runs(self, project_id: str, scenario_id: str, add_combo_names: bool = True) -> ItemList:
        """
        Returns a list of econ runs for a specific project id and scenario id.

        `add_combo_names` will add the list of combo names to each econ run.
        """
        url = self.get_econ_runs_url(project_id, scenario_id)
        params = {'take': GET_LIMIT}
        econruns = self._get_items(url, params)

        if add_combo_names:
            self.update_econ_run_combo_names(econruns, project_id, scenario_id)

        order = {
            'id': 2,
            'status': 1,
            'runDate': 0,
        }
        return self._keysort(econruns, order, reverse=True)

    def get_econ_run_by_id(
        self, project_id: str, scenario_id: str, econ_run_id: str, add_combo_names: bool = True
    ) -> Item:
        """
        Returns a specific econ run from its econ run id.

        `add_combo_names` will add the list of combo names to the econ run.
        """
        url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        econruns = self._get_items(url)

        if add_combo_names:
            self.update_econ_run_combo_names(econruns, project_id, scenario_id)

        order = {
            'id': 2,
            'status': 1,
            'runDate': 0,
        }
        return self._keysort(econruns, order, reverse=True)[0]

    def get_econ_run_combo_names(self, project_id: str, scenario_id: str, econ_run_id: str) -> List[str]:
        """
        Returns a list of combo names for a specific project id, scenario id,
        and econ run id.
        """
        url = self.get_econ_run_combo_names_url(project_id, scenario_id, econ_run_id)
        params = {'take': GET_LIMIT}
        data = self._get_items(url, params)

        return cast(List[str], sorted(set(data)))

    def get_econ_run_onelines(self, project_id: str, scenario_id: str, econ_run_id: str) -> ItemList:
        """
        Returns a list of onelines for a specific project id, scenario id,
        and econ run id.
        """
        url = self.get_econ_run_onelines_url(project_id, scenario_id, econ_run_id)

        # in this specific case we do some post-processing to "flatten" the results
        # into the expected type of: ItemList
        params = {'take': GET_LIMIT}
        items = self._get_items(url, params)

        onelines = [
            item
            for item in (flatten_outputs(item) for item in items)
            # if item is not None
        ]

        return onelines  # type: ignore[return-value]

    def get_econ_run_oneline_by_id(
        self, project_id: str, scenario_id: str, econ_run_id: str, oneline_id: str
    ) -> Item:
        """
        Returns a specific oneline from its project id, scenario id, econ run id,
        and oneline id.

        https://docs.api.combocurve.com/api/get-one-liner-by-id

        Example response:
        {
            "comboName": "string",
            "econGroup": "string",
            "econPRMSResourcesClass": "string",
            "econPRMSReservesCategory": "string",
            "econPRMSReservesSubCategory": "string",
            "id": "5e272d38b78910dd2a1bd691",
            "chosenID": "string",
            "scenarioId": "5e272d38b78910dd2a1bd691",
            "scenarioName": "string",
            "output": {
                "abandonmentDate": "string",
                "adValoremTax": 123.45,
                "afitDiscountTableCashFlow_1": 123.45,
                "afitDiscountTableCashFlow_10": 123.45,
                "afitDiscountTableCashFlow_11": 123.45,
                "afitDiscountTableCashFlow_12": 123.45,
                "afitDiscountTableCashFlow_13": 123.45,
                "afitDiscountTableCashFlow_14": 123.45,
                "afitDiscountTableCashFlow_15": 123.45,
                "afitDiscountTableCashFlow_16": 123.45,
                "afitDiscountTableCashFlow_2": 123.45,
                "afitDiscountTableCashFlow_3": 123.45,
                "afitDiscountTableCashFlow_4": 123.45,
                "afitDiscountTableCashFlow_5": 123.45,
                "afitDiscountTableCashFlow_6": 123.45,
                "afitDiscountTableCashFlow_7": 123.45,
                "afitDiscountTableCashFlow_8": 123.45,
                "afitDiscountTableCashFlow_9": 123.45,
                "afitFirstDiscountCashFlow": 123.45,
                "afitFirstDiscountRoi": 123.45,
                "afitFirstDiscountPvr": 123.45,
                "afitSecondDiscountCashFlow": 123.45,
                "afitSecondDiscountRoi": 123.45,
                "afitUndiscountedPvr": 123.45,
                "afitIrr": 123.45,
                "afterIncomeTaxCashFlow": 123.45,
                "applyNormalization": "string",
                "asOfDate": "string",
                "beforeIncomeTaxCashFlow": 123.45,
                "consecutiveNegativeCashFlowMonthCount": 123.45,
                "consecutiveNegativeCashFlowMonths": "string",
                "depreciation": 123.45,
                "discountDate": "string",
                "discountTableCashFlow_1": 123.45,
                "discountTableCashFlow_10": 123.45,
                "discountTableCashFlow_11": 123.45,
                "discountTableCashFlow_12": 123.45,
                "discountTableCashFlow_13": 123.45,
                "discountTableCashFlow_14": 123.45,
                "discountTableCashFlow_15": 123.45,
                "discountTableCashFlow_16": 123.45,
                "discountTableCashFlow_2": 123.45,
                "discountTableCashFlow_3": 123.45,
                "discountTableCashFlow_4": 123.45,
                "discountTableCashFlow_5": 123.45,
                "discountTableCashFlow_6": 123.45,
                "discountTableCashFlow_7": 123.45,
                "discountTableCashFlow_8": 123.45,
                "discountTableCashFlow_9": 123.45,
                "dripCondensateGatheringExpense": 123.45,
                "dripCondensateMarketingExpense": 123.45,
                "dripCondensateOtherExpense": 123.45,
                "dripCondensatePrice": 123.45,
                "dripCondensateProcessingExpense": 123.45,
                "dripCondensateRevenue": 123.45,
                "dripCondensateSeveranceTax": 123.45,
                "dripCondensateShrunkEur": 123.45,
                "dripCondensateTransportationExpense": 123.45,
                "dripCondensateYield": 123.45,
                "dripCondensateBoeConversion": 123.45,
                "dripCondensateDifferentials1": 123.45,
                "dripCondensateDifferentials2": 123.45,
                "dripCondensateRisk": 123.45,
                "dripCondensateShrunkEurOverPll": 123.45,
                "dryGasBoeConversion": 123.45,
                "econFirstProdDate": "string",
                "federalIncomeTax": 123.45,
                "firstConsecutiveNegativeCashFlowMonth": "string",
                "firstDiscountCashFlow": 123.45,
                "firstDiscountRoi": 123.45,
                "firstDiscountPvr": 123.45,
                "firstDiscountNetIncome": 123.45,
                "firstDiscountPayout": "string",
                "firstDiscountPayoutDuration": 123.45,
                "firstDiscountRoiUndiscountedCapex": 123.45,
                "firstDiscountedCapex": 123.45,
                "fiveYearGrossBoeSalesVolume": 123.45,
                "fiveYearGrossBoeWellHeadVolume": 123.45,
                "fiveYearGrossDripCondensateSalesVolume": 123.45,
                "fiveYearGrossGasSalesVolume": 123.45,
                "fiveYearGrossGasWellHeadVolume": 123.45,
                "fiveYearGrossNglSalesVolume": 123.45,
                "fiveYearGrossOilSalesVolume": 123.45,
                "fiveYearGrossOilWellHeadVolume": 123.45,
                "fiveYearGrossWaterWellHeadVolume": 123.45,
                "fiveYearNetBoeSalesVolume": 123.45,
                "fiveYearNetDripCondensateSalesVolume": 123.45,
                "fiveYearNetGasSalesVolume": 123.45,
                "fiveYearNetNglSalesVolume": 123.45,
                "fiveYearNetOilSalesVolume": 123.45,
                "fiveYearWiBoeSalesVolume": 123.45,
                "fiveYearWiDripCondensateSalesVolume": 123.45,
                "fiveYearWiGasSalesVolume": 123.45,
                "fiveYearWiNglSalesVolume": 123.45,
                "fiveYearWiOilSalesVolume": 123.45,
                "forecastName": "string",
                "gasAssignedPSeriesFirstSegmentB": 123.45,
                "gasAssignedPSeriesFirstSegmentD1Nominal": 123.45,
                "gasAssignedPSeriesFirstSegmentDiEffSec": 123.45,
                "gasAssignedPSeriesFirstSegmentEndDate": "string",
                "gasAssignedPSeriesFirstSegmentQEnd": 123.45,
                "gasAssignedPSeriesFirstSegmentQStart": 123.45,
                "gasAssignedPSeriesFirstSegmentRealizedDSwEffSec": 123.45,
                "gasAssignedPSeriesFirstSegmentSegmentType": "string",
                "gasAssignedPSeriesFirstSegmentStartDate": "string",
                "gasAssignedPSeriesFirstSegmentSwDate": "string",
                "gasAssignedPSeriesLastSegmentB": 123.45,
                "gasAssignedPSeriesLastSegmentD1Nominal": 123.45,
                "gasAssignedPSeriesLastSegmentDiEffSec": 123.45,
                "gasAssignedPSeriesLastSegmentEndDate": "string",
                "gasAssignedPSeriesLastSegmentQEnd": 123.45,
                "gasAssignedPSeriesLastSegmentQStart": 123.45,
                "gasAssignedPSeriesLastSegmentRealizedDSwEffSec": 123.45,
                "gasAssignedPSeriesLastSegmentSegmentType": "string",
                "gasAssignedPSeriesLastSegmentStartDate": "string",
                "gasAssignedPSeriesLastSegmentSwDate": "string",
                "gasBestFitFirstSegmentB": 123.45,
                "gasBestFitFirstSegmentD1Nominal": 123.45,
                "gasBestFitFirstSegmentDiEffSec": 123.45,
                "gasBestFitFirstSegmentEndDate": "string",
                "gasBestFitFirstSegmentQEnd": 123.45,
                "gasBestFitFirstSegmentQStart": 123.45,
                "gasBestFitFirstSegmentRealizedDSwEffSec": 123.45,
                "gasBestFitFirstSegmentSegmentType": "string",
                "gasBestFitFirstSegmentStartDate": "string",
                "gasBestFitFirstSegmentSwDate": "string",
                "gasBestFitLastSegmentB": 123.45,
                "gasBestFitLastSegmentD1Nominal": 123.45,
                "gasBestFitLastSegmentDiEffSec": 123.45,
                "gasBestFitLastSegmentEndDate": "string",
                "gasBestFitLastSegmentQEnd": 123.45,
                "gasBestFitLastSegmentQStart": 123.45,
                "gasBestFitLastSegmentRealizedDSwEffSec": 123.45,
                "gasBestFitLastSegmentSegmentType": "string",
                "gasBestFitLastSegmentStartDate": "string",
                "gasBestFitLastSegmentSwDate": "string",
                "gasBreakeven": 123.45,
                "gasFlare": 123.45,
                "gasGatheringExpense": 123.45,
                "gasLoss": 123.45,
                "gasMarketingExpense": 123.45,
                "gasOtherExpense": 123.45,
                "gasP10FirstSegmentB": 123.45,
                "gasP10FirstSegmentD1Nominal": 123.45,
                "gasP10FirstSegmentDiEffSec": 123.45,
                "gasP10FirstSegmentEndDate": "string",
                "gasP10FirstSegmentQEnd": 123.45,
                "gasP10FirstSegmentQStart": 123.45,
                "gasP10FirstSegmentRealizedDSwEffSec": 123.45,
                "gasP10FirstSegmentSegmentType": "string",
                "gasP10FirstSegmentStartDate": "string",
                "gasP10FirstSegmentSwDate": "string",
                "gasP10LastSegmentB": 123.45,
                "gasP10LastSegmentD1Nominal": 123.45,
                "gasP10LastSegmentDiEffSec": 123.45,
                "gasP10LastSegmentEndDate": "string",
                "gasP10LastSegmentQEnd": 123.45,
                "gasP10LastSegmentQStart": 123.45,
                "gasP10LastSegmentRealizedDSwEffSec": 123.45,
                "gasP10LastSegmentSegmentType": "string",
                "gasP10LastSegmentStartDate": "string",
                "gasP10LastSegmentSwDate": "string",
                "gasP50FirstSegmentB": 123.45,
                "gasP50FirstSegmentD1Nominal": 123.45,
                "gasP50FirstSegmentDiEffSec": 123.45,
                "gasP50FirstSegmentEndDate": "string",
                "gasP50FirstSegmentQEnd": 123.45,
                "gasP50FirstSegmentQStart": 123.45,
                "gasP50FirstSegmentRealizedDSwEffSec": 123.45,
                "gasP50FirstSegmentSegmentType": "string",
                "gasP50FirstSegmentStartDate": "string",
                "gasP50FirstSegmentSwDate": "string",
                "gasP50LastSegmentB": 123.45,
                "gasP50LastSegmentD1Nominal": 123.45,
                "gasP50LastSegmentDiEffSec": 123.45,
                "gasP50LastSegmentEndDate": "string",
                "gasP50LastSegmentQEnd": 123.45,
                "gasP50LastSegmentQStart": 123.45,
                "gasP50LastSegmentRealizedDSwEffSec": 123.45,
                "gasP50LastSegmentSegmentType": "string",
                "gasP50LastSegmentStartDate": "string",
                "gasP50LastSegmentSwDate": "string",
                "gasP90FirstSegmentB": 123.45,
                "gasP90FirstSegmentD1Nominal": 123.45,
                "gasP90FirstSegmentDiEffSec": 123.45,
                "gasP90FirstSegmentEndDate": "string",
                "gasP90FirstSegmentQEnd": 123.45,
                "gasP90FirstSegmentQStart": 123.45,
                "gasP90FirstSegmentRealizedDSwEffSec": 123.45,
                "gasP90FirstSegmentSegmentType": "string",
                "gasP90FirstSegmentStartDate": "string",
                "gasP90FirstSegmentSwDate": "string",
                "gasP90LastSegmentB": 123.45,
                "gasP90LastSegmentD1Nominal": 123.45,
                "gasP90LastSegmentDiEffSec": 123.45,
                "gasP90LastSegmentEndDate": "string",
                "gasP90LastSegmentQEnd": 123.45,
                "gasP90LastSegmentQStart": 123.45,
                "gasP90LastSegmentRealizedDSwEffSec": 123.45,
                "gasP90LastSegmentSegmentType": "string",
                "gasP90LastSegmentStartDate": "string",
                "gasP90LastSegmentSwDate": "string",
                "gasPrice": 123.45,
                "gasProcessingExpense": 123.45,
                "gasRevenue": 123.45,
                "gasSeveranceTax": 123.45,
                "gasShrinkage": 123.45,
                "gasShrunkEur": 123.45,
                "gasTransportationExpense": 123.45,
                "gasWellHeadEur": 123.45,
                "gasDifferentials1": 123.45,
                "gasDifferentials2": 123.45,
                "gasProductionAsOfDate": 123.45,
                "gasRisk": 123.45,
                "gasShrunkEurOverPll": 123.45,
                "gasTcRisk": 123.45,
                "gasWellHeadEurOverPll": 123.45,
                "grossBoeSalesVolume": 123.45,
                "grossBoeWellHeadVolume": 123.45,
                "grossDripCondensateSalesVolume": 123.45,
                "grossGasSalesVolume": 123.45,
                "grossGasWellHeadVolume": 123.45,
                "grossNglSalesVolume": 123.45,
                "grossOilSalesVolume": 123.45,
                "grossOilWellHeadVolume": 123.45,
                "grossWaterWellHeadVolume": 123.45,
                "grossMcfeSalesVolume": 123.45,
                "grossMcfeWellHeadVolume": 123.45,
                "inputDripCondensatePrice": 123.45,
                "inputGasPrice": 123.45,
                "inputNglPrice": 123.45,
                "inputOilPrice": 123.45,
                "intangibleAbandonment": 123.45,
                "intangibleAppraisal": 123.45,
                "intangibleArtificialLift": 123.45,
                "intangibleCompletion": 123.45,
                "intangibleDevelopment": 123.45,
                "intangibleDrilling": 123.45,
                "intangibleExploration": 123.45,
                "intangibleFacilities": 123.45,
                "intangibleLeasehold": 123.45,
                "intangibleLegal": 123.45,
                "intangibleOtherInvestment": 123.45,
                "intangiblePad": 123.45,
                "intangiblePipelines": 123.45,
                "intangibleSalvage": 123.45,
                "intangibleWaterline": 123.45,
                "intangibleWorkover": 123.45,
                "irr": 123.45,
                "lastConsecutiveNegativeCashFlowMonth": "string",
                "lastOneMonthBoeAverage": 123.45,
                "lastOneMonthGasAverage": 123.45,
                "lastOneMonthMcfeAverage": 123.45,
                "lastOneMonthOilAverage": 123.45,
                "lastOneMonthWaterAverage": 123.45,
                "lastThreeMonthBoeAverage": 123.45,
                "lastThreeMonthGasAverage": 123.45,
                "lastThreeMonthMcfeAverage": 123.45,
                "lastThreeMonthOilAverage": 123.45,
                "lastThreeMonthWaterAverage": 123.45,
                "leaseNri": 123.45,
                "monthlyWellCost": 123.45,
                "netBoeSalesVolume": 123.45,
                "netDripCondensateSalesVolume": 123.45,
                "netGasSalesVolume": 123.45,
                "netNglSalesVolume": 123.45,
                "netOilSalesVolume": 123.45,
                "netProfit": 123.45,
                "netIncome": 123.45,
                "netMcfeSalesVolume": 123.45,
                "nglGatheringExpense": 123.45,
                "nglMarketingExpense": 123.45,
                "nglOtherExpense": 123.45,
                "nglPrice": 123.45,
                "nglProcessingExpense": 123.45,
                "nglRevenue": 123.45,
                "nglSeveranceTax": 123.45,
                "nglShrunkEur": 123.45,
                "nglTransportationExpense": 123.45,
                "nglYield": 123.45,
                "nglBoeConversion": 123.45,
                "nglDifferentials1": 123.45,
                "nglDifferentials2": 123.45,
                "nglRisk": 123.45,
                "nglShrunkEurOverPll": 123.45,
                "nriDripCondensate": 123.45,
                "nriGas": 123.45,
                "nriNgl": 123.45,
                "nriOil": 123.45,
                "oilAssignedPSeriesFirstSegmentB": 123.45,
                "oilAssignedPSeriesFirstSegmentD1Nominal": 123.45,
                "oilAssignedPSeriesFirstSegmentDiEffSec": 123.45,
                "oilAssignedPSeriesFirstSegmentEndDate": "string",
                "oilAssignedPSeriesFirstSegmentQEnd": 123.45,
                "oilAssignedPSeriesFirstSegmentQStart": 123.45,
                "oilAssignedPSeriesFirstSegmentRealizedDSwEffSec": 123.45,
                "oilAssignedPSeriesFirstSegmentSegmentType": "string",
                "oilAssignedPSeriesFirstSegmentStartDate": "string",
                "oilAssignedPSeriesFirstSegmentSwDate": "string",
                "oilAssignedPSeriesLastSegmentB": 123.45,
                "oilAssignedPSeriesLastSegmentD1Nominal": 123.45,
                "oilAssignedPSeriesLastSegmentDiEffSec": 123.45,
                "oilAssignedPSeriesLastSegmentEndDate": "string",
                "oilAssignedPSeriesLastSegmentQEnd": 123.45,
                "oilAssignedPSeriesLastSegmentQStart": 123.45,
                "oilAssignedPSeriesLastSegmentRealizedDSwEffSec": 123.45,
                "oilAssignedPSeriesLastSegmentSegmentType": "string",
                "oilAssignedPSeriesLastSegmentStartDate": "string",
                "oilAssignedPSeriesLastSegmentSwDate": "string",
                "oilBestFitFirstSegmentB": 123.45,
                "oilBestFitFirstSegmentD1Nominal": 123.45,
                "oilBestFitFirstSegmentDiEffSec": 123.45,
                "oilBestFitFirstSegmentEndDate": "string",
                "oilBestFitFirstSegmentQEnd": 123.45,
                "oilBestFitFirstSegmentQStart": 123.45,
                "oilBestFitFirstSegmentRealizedDSwEffSec": 123.45,
                "oilBestFitFirstSegmentSegmentType": "string",
                "oilBestFitFirstSegmentStartDate": "string",
                "oilBestFitFirstSegmentSwDate": "string",
                "oilBestFitLastSegmentB": 123.45,
                "oilBestFitLastSegmentD1Nominal": 123.45,
                "oilBestFitLastSegmentDiEffSec": 123.45,
                "oilBestFitLastSegmentEndDate": "string",
                "oilBestFitLastSegmentQEnd": 123.45,
                "oilBestFitLastSegmentQStart": 123.45,
                "oilBestFitLastSegmentRealizedDSwEffSec": 123.45,
                "oilBestFitLastSegmentSegmentType": "string",
                "oilBestFitLastSegmentStartDate": "string",
                "oilBestFitLastSegmentSwDate": "string",
                "oilBreakeven": 123.45,
                "oilGatheringExpense": 123.45,
                "oilLoss": 123.45,
                "oilMarketingExpense": 123.45,
                "oilOtherExpense": 123.45,
                "oilP10FirstSegmentB": 123.45,
                "oilP10FirstSegmentD1Nominal": 123.45,
                "oilP10FirstSegmentDiEffSec": 123.45,
                "oilP10FirstSegmentEndDate": "string",
                "oilP10FirstSegmentQEnd": 123.45,
                "oilP10FirstSegmentQStart": 123.45,
                "oilP10FirstSegmentRealizedDSwEffSec": 123.45,
                "oilP10FirstSegmentSegmentType": "string",
                "oilP10FirstSegmentStartDate": "string",
                "oilP10FirstSegmentSwDate": "string",
                "oilP10LastSegmentB": 123.45,
                "oilP10LastSegmentD1Nominal": 123.45,
                "oilP10LastSegmentDiEffSec": 123.45,
                "oilP10LastSegmentEndDate": "string",
                "oilP10LastSegmentQEnd": 123.45,
                "oilP10LastSegmentQStart": 123.45,
                "oilP10LastSegmentRealizedDSwEffSec": 123.45,
                "oilP10LastSegmentSegmentType": "string",
                "oilP10LastSegmentStartDate": "string",
                "oilP10LastSegmentSwDate": "string",
                "oilP50FirstSegmentB": 123.45,
                "oilP50FirstSegmentD1Nominal": 123.45,
                "oilP50FirstSegmentDiEffSec": 123.45,
                "oilP50FirstSegmentEndDate": "string",
                "oilP50FirstSegmentQEnd": 123.45,
                "oilP50FirstSegmentQStart": 123.45,
                "oilP50FirstSegmentRealizedDSwEffSec": 123.45,
                "oilP50FirstSegmentSegmentType": "string",
                "oilP50FirstSegmentStartDate": "string",
                "oilP50FirstSegmentSwDate": "string",
                "oilP50LastSegmentB": 123.45,
                "oilP50LastSegmentD1Nominal": 123.45,
                "oilP50LastSegmentDiEffSec": 123.45,
                "oilP50LastSegmentEndDate": "string",
                "oilP50LastSegmentQEnd": 123.45,
                "oilP50LastSegmentQStart": 123.45,
                "oilP50LastSegmentRealizedDSwEffSec": 123.45,
                "oilP50LastSegmentSegmentType": "string",
                "oilP50LastSegmentStartDate": "string",
                "oilP50LastSegmentSwDate": "string",
                "oilP90FirstSegmentB": 123.45,
                "oilP90FirstSegmentD1Nominal": 123.45,
                "oilP90FirstSegmentDiEffSec": 123.45,
                "oilP90FirstSegmentEndDate": "string",
                "oilP90FirstSegmentQEnd": 123.45,
                "oilP90FirstSegmentQStart": 123.45,
                "oilP90FirstSegmentRealizedDSwEffSec": 123.45,
                "oilP90FirstSegmentSegmentType": "string",
                "oilP90FirstSegmentStartDate": "string",
                "oilP90FirstSegmentSwDate": "string",
                "oilP90LastSegmentB": 123.45,
                "oilP90LastSegmentD1Nominal": 123.45,
                "oilP90LastSegmentDiEffSec": 123.45,
                "oilP90LastSegmentEndDate": "string",
                "oilP90LastSegmentQEnd": 123.45,
                "oilP90LastSegmentQStart": 123.45,
                "oilP90LastSegmentRealizedDSwEffSec": 123.45,
                "oilP90LastSegmentSegmentType": "string",
                "oilP90LastSegmentStartDate": "string",
                "oilP90LastSegmentSwDate": "string",
                "oilPrice": 123.45,
                "oilProcessingExpense": 123.45,
                "oilRevenue": 123.45,
                "oilSeveranceTax": 123.45,
                "oilShrinkage": 123.45,
                "oilShrunkEur": 123.45,
                "oilTransportationExpense": 123.45,
                "oilWellHeadEur": 123.45,
                "oilBoeConversion": 123.45,
                "oilDifferentials1": 123.45,
                "oilDifferentials2": 123.45,
                "oilProductionAsOfDate": 123.45,
                "oilRisk": 123.45,
                "oilShrunkEurOverPll": 123.45,
                "oilTcRisk": 123.45,
                "oilWellHeadEurOverPll": 123.45,
                "oneMonthGrossBoeSalesVolume": 123.45,
                "oneMonthGrossBoeWellHeadVolume": 123.45,
                "oneMonthGrossDripCondensateSalesVolume": 123.45,
                "oneMonthGrossGasSalesVolume": 123.45,
                "oneMonthGrossGasWellHeadVolume": 123.45,
                "oneMonthGrossNglSalesVolume": 123.45,
                "oneMonthGrossOilSalesVolume": 123.45,
                "oneMonthGrossOilWellHeadVolume": 123.45,
                "oneMonthGrossWaterWellHeadVolume": 123.45,
                "oneMonthNetBoeSalesVolume": 123.45,
                "oneMonthNetDripCondensateSalesVolume": 123.45,
                "oneMonthNetGasSalesVolume": 123.45,
                "oneMonthNetNglSalesVolume": 123.45,
                "oneMonthNetOilSalesVolume": 123.45,
                "oneMonthWiBoeSalesVolume": 123.45,
                "oneMonthWiDripCondensateSalesVolume": 123.45,
                "oneMonthWiGasSalesVolume": 123.45,
                "oneMonthWiNglSalesVolume": 123.45,
                "oneMonthWiOilSalesVolume": 123.45,
                "oneYearGrossBoeSalesVolume": 123.45,
                "oneYearGrossBoeWellHeadVolume": 123.45,
                "oneYearGrossDripCondensateSalesVolume": 123.45,
                "oneYearGrossGasSalesVolume": 123.45,
                "oneYearGrossGasWellHeadVolume": 123.45,
                "oneYearGrossNglSalesVolume": 123.45,
                "oneYearGrossOilSalesVolume": 123.45,
                "oneYearGrossOilWellHeadVolume": 123.45,
                "oneYearGrossWaterWellHeadVolume": 123.45,
                "oneYearNetBoeSalesVolume": 123.45,
                "oneYearNetDripCondensateSalesVolume": 123.45,
                "oneYearNetGasSalesVolume": 123.45,
                "oneYearNetNglSalesVolume": 123.45,
                "oneYearNetOilSalesVolume": 123.45,
                "oneYearWiBoeSalesVolume": 123.45,
                "oneYearWiDripCondensateSalesVolume": 123.45,
                "oneYearWiGasSalesVolume": 123.45,
                "oneYearWiNglSalesVolume": 123.45,
                "operationsModelName": "string",
                "operationsQualifier": "string",
                "oneYearWiOilSalesVolume": 123.45,
                "originalWiDripCondensate": 123.45,
                "originalWiGas": 123.45,
                "originalWiNgl": 123.45,
                "originalWiOil": 123.45,
                "otherMonthlyCost_1": 123.45,
                "otherMonthlyCost_2": 123.45,
                "payoutDuration": 123.45,
                "secondDiscountCashFlow": 123.45,
                "secondDiscountRoi": 123.45,
                "secondDiscountNetIncome": 123.45,
                "secondDiscountPayout": "string",
                "secondDiscountPayoutDuration": 123.45,
                "secondDiscountRoiUndiscountedCapex": 123.45,
                "secondDiscountedCapex": 123.45,
                "shrunkGasBtu": 123.45,
                "sixMonthGrossBoeSalesVolume": 123.45,
                "sixMonthGrossBoeWellHeadVolume": 123.45,
                "sixMonthGrossDripCondensateSalesVolume": 123.45,
                "sixMonthGrossGasSalesVolume": 123.45,
                "sixMonthGrossGasWellHeadVolume": 123.45,
                "sixMonthGrossNglSalesVolume": 123.45,
                "sixMonthGrossOilSalesVolume": 123.45,
                "sixMonthGrossOilWellHeadVolume": 123.45,
                "sixMonthGrossWaterWellHeadVolume": 123.45,
                "sixMonthNetBoeSalesVolume": 123.45,
                "sixMonthNetDripCondensateSalesVolume": 123.45,
                "sixMonthNetGasSalesVolume": 123.45,
                "sixMonthNetNglSalesVolume": 123.45,
                "sixMonthNetOilSalesVolume": 123.45,
                "sixMonthWiBoeSalesVolume": 123.45,
                "sixMonthWiDripCondensateSalesVolume": 123.45,
                "sixMonthWiGasSalesVolume": 123.45,
                "sixMonthWiNglSalesVolume": 123.45,
                "sixMonthWiOilSalesVolume": 123.45,
                "stateIncomeTax": 123.45,
                "tangibleAbandonment": 123.45,
                "tangibleAppraisal": 123.45,
                "tangibleArtificialLift": 123.45,
                "tangibleCompletion": 123.45,
                "tangibleDevelopment": 123.45,
                "tangibleDrilling": 123.45,
                "tangibleExploration": 123.45,
                "tangibleFacilities": 123.45,
                "tangibleLeasehold": 123.45,
                "tangibleLegal": 123.45,
                "tangibleOtherInvestment": 123.45,
                "tangiblePad": 123.45,
                "tangiblePipelines": 123.45,
                "tangibleSalvage": 123.45,
                "tangibleWaterline": 123.45,
                "tangibleWorkover": 123.45,
                "taxableIncome": 123.45,
                "tenYearGrossBoeSalesVolume": 123.45,
                "tenYearGrossBoeWellHeadVolume": 123.45,
                "tenYearGrossDripCondensateSalesVolume": 123.45,
                "tenYearGrossGasSalesVolume": 123.45,
                "tenYearGrossGasWellHeadVolume": 123.45,
                "tenYearGrossNglSalesVolume": 123.45,
                "tenYearGrossOilSalesVolume": 123.45,
                "tenYearGrossOilWellHeadVolume": 123.45,
                "tenYearGrossWaterWellHeadVolume": 123.45,
                "tenYearNetBoeSalesVolume": 123.45,
                "tenYearNetDripCondensateSalesVolume": 123.45,
                "tenYearNetGasSalesVolume": 123.45,
                "tenYearNetNglSalesVolume": 123.45,
                "tenYearNetOilSalesVolume": 123.45,
                "tenYearWiBoeSalesVolume": 123.45,
                "tenYearWiDripCondensateSalesVolume": 123.45,
                "tenYearWiGasSalesVolume": 123.45,
                "tenYearWiNglSalesVolume": 123.45,
                "tenYearWiOilSalesVolume": 123.45,
                "threeMonthGrossBoeSalesVolume": 123.45,
                "threeMonthGrossBoeWellHeadVolume": 123.45,
                "threeMonthGrossDripCondensateSalesVolume": 123.45,
                "threeMonthGrossGasSalesVolume": 123.45,
                "threeMonthGrossGasWellHeadVolume": 123.45,
                "threeMonthGrossNglSalesVolume": 123.45,
                "threeMonthGrossOilSalesVolume": 123.45,
                "threeMonthGrossOilWellHeadVolume": 123.45,
                "threeMonthGrossWaterWellHeadVolume": 123.45,
                "threeMonthNetBoeSalesVolume": 123.45,
                "threeMonthNetDripCondensateSalesVolume": 123.45,
                "threeMonthNetGasSalesVolume": 123.45,
                "threeMonthNetNglSalesVolume": 123.45,
                "threeMonthNetOilSalesVolume": 123.45,
                "threeMonthWiBoeSalesVolume": 123.45,
                "threeMonthWiDripCondensateSalesVolume": 123.45,
                "threeMonthWiGasSalesVolume": 123.45,
                "threeMonthWiNglSalesVolume": 123.45,
                "threeMonthWiOilSalesVolume": 123.45,
                "threeYearGrossBoeSalesVolume": 123.45,
                "threeYearGrossBoeWellHeadVolume": 123.45,
                "threeYearGrossDripCondensateSalesVolume": 123.45,
                "threeYearGrossGasSalesVolume": 123.45,
                "threeYearGrossGasWellHeadVolume": 123.45,
                "threeYearGrossNglSalesVolume": 123.45,
                "threeYearGrossOilSalesVolume": 123.45,
                "threeYearGrossOilWellHeadVolume": 123.45,
                "threeYearGrossWaterWellHeadVolume": 123.45,
                "threeYearNetBoeSalesVolume": 123.45,
                "threeYearNetDripCondensateSalesVolume": 123.45,
                "threeYearNetGasSalesVolume": 123.45,
                "threeYearNetNglSalesVolume": 123.45,
                "threeYearNetOilSalesVolume": 123.45,
                "threeYearWiBoeSalesVolume": 123.45,
                "threeYearWiDripCondensateSalesVolume": 123.45,
                "threeYearWiGasSalesVolume": 123.45,
                "threeYearWiNglSalesVolume": 123.45,
                "threeYearWiOilSalesVolume": 123.45,
                "totalAbandonment": 123.45,
                "totalAppraisal": 123.45,
                "totalArtificialLift": 123.45,
                "totalCapex": 123.45,
                "totalCompletion": 123.45,
                "totalDevelopment": 123.45,
                "totalDrilling": 123.45,
                "totalDripCondensateVariableExpense": 123.45,
                "totalExpense": 123.45,
                "totalExploration": 123.45,
                "totalFacilities": 123.45,
                "totalFixedExpense": 123.45,
                "totalGasVariableExpense": 123.45,
                "totalIntangibleCapex": 123.45,
                "totalLeasehold": 123.45,
                "totalLegal": 123.45,
                "totalNegativeCashFlowMonthCount": 123.45,
                "totalNglVariableExpense": 123.45,
                "totalOilVariableExpense": 123.45,
                "totalOtherInvestment": 123.45,
                "totalPad": 123.45,
                "totalPipelines": 123.45,
                "totalProductionTax": 123.45,
                "totalRevenue": 123.45,
                "totalSalvage": 123.45,
                "totalSeveranceTax": 123.45,
                "totalTangibleCapex": 123.45,
                "totalVariableExpense": 123.45,
                "totalWaterline": 123.45,
                "totalWorkover": 123.45,
                "totalGrossCapex": 123.45,
                "twoYearGrossBoeSalesVolume": 123.45,
                "twoYearGrossBoeWellHeadVolume": 123.45,
                "twoYearGrossDripCondensateSalesVolume": 123.45,
                "twoYearGrossGasSalesVolume": 123.45,
                "twoYearGrossGasWellHeadVolume": 123.45,
                "twoYearGrossNglSalesVolume": 123.45,
                "twoYearGrossOilSalesVolume": 123.45,
                "twoYearGrossOilWellHeadVolume": 123.45,
                "twoYearGrossWaterWellHeadVolume": 123.45,
                "twoYearNetBoeSalesVolume": 123.45,
                "twoYearNetDripCondensateSalesVolume": 123.45,
                "twoYearNetGasSalesVolume": 123.45,
                "twoYearNetNglSalesVolume": 123.45,
                "twoYearNetOilSalesVolume": 123.45,
                "twoYearWiBoeSalesVolume": 123.45,
                "twoYearWiDripCondensateSalesVolume": 123.45,
                "twoYearWiGasSalesVolume": 123.45,
                "twoYearWiNglSalesVolume": 123.45,
                "twoYearWiOilSalesVolume": 123.45,
                "undiscountedPayout": "string",
                "undiscountedRoi": 123.45,
                "undiscountedPvr": 123.45,
                "unshrunkGasBtu": 123.45,
                "waterAssignedPSeriesFirstSegmentB": 123.45,
                "waterAssignedPSeriesFirstSegmentD1Nominal": 123.45,
                "waterAssignedPSeriesFirstSegmentDiEffSec": 123.45,
                "waterAssignedPSeriesFirstSegmentEndDate": "string",
                "waterAssignedPSeriesFirstSegmentQEnd": 123.45,
                "waterAssignedPSeriesFirstSegmentQStart": 123.45,
                "waterAssignedPSeriesFirstSegmentRealizedDSwEffSec": 123.45,
                "waterAssignedPSeriesFirstSegmentSegmentType": "string",
                "waterAssignedPSeriesFirstSegmentStartDate": "string",
                "waterAssignedPSeriesFirstSegmentSwDate": "string",
                "waterAssignedPSeriesLastSegmentB": 123.45,
                "waterAssignedPSeriesLastSegmentD1Nominal": 123.45,
                "waterAssignedPSeriesLastSegmentDiEffSec": 123.45,
                "waterAssignedPSeriesLastSegmentEndDate": "string",
                "waterAssignedPSeriesLastSegmentQEnd": 123.45,
                "waterAssignedPSeriesLastSegmentQStart": 123.45,
                "waterAssignedPSeriesLastSegmentRealizedDSwEffSec": 123.45,
                "waterAssignedPSeriesLastSegmentSegmentType": "string",
                "waterAssignedPSeriesLastSegmentStartDate": "string",
                "waterAssignedPSeriesLastSegmentSwDate": "string",
                "waterBestFitFirstSegmentB": 123.45,
                "waterBestFitFirstSegmentD1Nominal": 123.45,
                "waterBestFitFirstSegmentDiEffSec": 123.45,
                "waterBestFitFirstSegmentEndDate": "string",
                "waterBestFitFirstSegmentQEnd": 123.45,
                "waterBestFitFirstSegmentQStart": 123.45,
                "waterBestFitFirstSegmentRealizedDSwEffSec": 123.45,
                "waterBestFitFirstSegmentSegmentType": "string",
                "waterBestFitFirstSegmentStartDate": "string",
                "waterBestFitFirstSegmentSwDate": "string",
                "waterBestFitLastSegmentB": 123.45,
                "waterBestFitLastSegmentD1Nominal": 123.45,
                "waterBestFitLastSegmentDiEffSec": 123.45,
                "waterBestFitLastSegmentEndDate": "string",
                "waterBestFitLastSegmentQEnd": 123.45,
                "waterBestFitLastSegmentQStart": 123.45,
                "waterBestFitLastSegmentRealizedDSwEffSec": 123.45,
                "waterBestFitLastSegmentSegmentType": "string",
                "waterBestFitLastSegmentStartDate": "string",
                "waterBestFitLastSegmentSwDate": "string",
                "waterDisposal": 123.45,
                "waterP10FirstSegmentB": 123.45,
                "waterP10FirstSegmentD1Nominal": 123.45,
                "waterP10FirstSegmentDiEffSec": 123.45,
                "waterP10FirstSegmentEndDate": "string",
                "waterP10FirstSegmentQEnd": 123.45,
                "waterP10FirstSegmentQStart": 123.45,
                "waterP10FirstSegmentRealizedDSwEffSec": 123.45,
                "waterP10FirstSegmentSegmentType": "string",
                "waterP10FirstSegmentStartDate": "string",
                "waterP10FirstSegmentSwDate": "string",
                "waterP10LastSegmentB": 123.45,
                "waterP10LastSegmentD1Nominal": 123.45,
                "waterP10LastSegmentDiEffSec": 123.45,
                "waterP10LastSegmentEndDate": "string",
                "waterP10LastSegmentQEnd": 123.45,
                "waterP10LastSegmentQStart": 123.45,
                "waterP10LastSegmentRealizedDSwEffSec": 123.45,
                "waterP10LastSegmentSegmentType": "string",
                "waterP10LastSegmentStartDate": "string",
                "waterP10LastSegmentSwDate": "string",
                "waterP50FirstSegmentB": 123.45,
                "waterP50FirstSegmentD1Nominal": 123.45,
                "waterP50FirstSegmentDiEffSec": 123.45,
                "waterP50FirstSegmentEndDate": "string",
                "waterP50FirstSegmentQEnd": 123.45,
                "waterP50FirstSegmentQStart": 123.45,
                "waterP50FirstSegmentRealizedDSwEffSec": 123.45,
                "waterP50FirstSegmentSegmentType": "string",
                "waterP50FirstSegmentStartDate": "string",
                "waterP50FirstSegmentSwDate": "string",
                "waterP50LastSegmentB": 123.45,
                "waterP50LastSegmentD1Nominal": 123.45,
                "waterP50LastSegmentDiEffSec": 123.45,
                "waterP50LastSegmentEndDate": "string",
                "waterP50LastSegmentQEnd": 123.45,
                "waterP50LastSegmentQStart": 123.45,
                "waterP50LastSegmentRealizedDSwEffSec": 123.45,
                "waterP50LastSegmentSegmentType": "string",
                "waterP50LastSegmentStartDate": "string",
                "waterP50LastSegmentSwDate": "string",
                "waterP90FirstSegmentB": 123.45,
                "waterP90FirstSegmentD1Nominal": 123.45,
                "waterP90FirstSegmentDiEffSec": 123.45,
                "waterP90FirstSegmentEndDate": "string",
                "waterP90FirstSegmentQEnd": 123.45,
                "waterP90FirstSegmentQStart": 123.45,
                "waterP90FirstSegmentRealizedDSwEffSec": 123.45,
                "waterP90FirstSegmentSegmentType": "string",
                "waterP90FirstSegmentStartDate": "string",
                "waterP90FirstSegmentSwDate": "string",
                "waterP90LastSegmentB": 123.45,
                "waterP90LastSegmentD1Nominal": 123.45,
                "waterP90LastSegmentDiEffSec": 123.45,
                "waterP90LastSegmentEndDate": "string",
                "waterP90LastSegmentQEnd": 123.45,
                "waterP90LastSegmentQStart": 123.45,
                "waterP90LastSegmentRealizedDSwEffSec": 123.45,
                "waterP90LastSegmentSegmentType": "string",
                "waterP90LastSegmentStartDate": "string",
                "waterP90LastSegmentSwDate": "string",
                "waterWellHeadEur": 123.45,
                "waterProductionAsOfDate": 123.45,
                "waterRisk": 123.45,
                "waterTcRisk": 123.45,
                "waterWellHeadEurOverPll": 123.45,
                "wellLife": 123.45,
                "wetGasBoeConversion": 123.45,
                "wiBoeSalesVolume": 123.45,
                "wiDripCondensate": 123.45,
                "wiDripCondensateSalesVolume": 123.45,
                "wiGas": 123.45,
                "wiGasSalesVolume": 123.45,
                "wiNgl": 123.45,
                "wiNglSalesVolume": 123.45,
                "wiOil": 123.45,
                "wiOilSalesVolume": 123.45,
                "wiMcfeSalesVolume": 123.45
            },
            "well": "string"
        }
        """
        url = self.get_econ_run_oneline_by_id_url(project_id, scenario_id, econ_run_id, oneline_id)
        items = self._get_items(url)

        return cast(Item, flatten_outputs(items[0]))

    def get_econ_run_monthly_econ_result_by_id(
        self, project_id: str, scenario_id: str, econ_run_id: str, columns: List[str]
    ) -> ItemList:
        """
        Returns the monthly econ results for a specific project id, scenario id,
        and econ run id.

        `columns` is REQUIRED by the API -- a request without it returns
        `MonthlyEconResultBadRequestError: "Columns are required"`. Pass the
        snake_case result column names to return, e.g.
        ['gross_oil_well_head_volume', 'net_income']; an invalid name returns a
        `MonthlyEconResultBadRequestError` naming a suggested column.

        https://docs.api.combocurve.com/api/get-monthly-econ-result-by-id

        Example response:
        {
            "combos": [
                {
                    "combo_name": "string",
                    "wells": [
                        {
                            "well_id": "string",
                            "well_chosen_id": "string",
                            "columns": {
                                "econ_prms_reserves_category": [
                                    "string"
                                ],
                                "econ_prms_reserves_sub_category": [
                                    "string"
                                ],
                                "econ_prms_resources_class": [
                                    "string"
                                ],
                                "oil_price": [
                                    123.45
                                ],
                                "gas_price": [
                                    123.45
                                ],
                                "company_custom_stream_1_price": [
                                    123.45
                                ],
                                "company_custom_stream_2_price": [
                                    123.45
                                ],
                                "company_custom_stream_3_price": [
                                    123.45
                                ],
                                "company_custom_stream_4_price": [
                                    123.45
                                ],
                                "company_custom_stream_5_price": [
                                    123.45
                                ],
                                "company_custom_stream_6_price": [
                                    123.45
                                ],
                                "company_custom_stream_7_price": [
                                    123.45
                                ],
                                "company_custom_stream_8_price": [
                                    123.45
                                ],
                                "company_custom_stream_9_price": [
                                    123.45
                                ],
                                "company_custom_stream_10_price": [
                                    123.45
                                ],
                                "company_custom_stream_11_price": [
                                    123.45
                                ],
                                "company_custom_stream_12_price": [
                                    123.45
                                ],
                                "company_custom_stream_13_price": [
                                    123.45
                                ],
                                "company_custom_stream_14_price": [
                                    123.45
                                ],
                                "company_custom_stream_15_price": [
                                    123.45
                                ],
                                "company_custom_stream_16_price": [
                                    123.45
                                ],
                                "company_custom_stream_17_price": [
                                    123.45
                                ],
                                "company_custom_stream_18_price": [
                                    123.45
                                ],
                                "company_custom_stream_19_price": [
                                    123.45
                                ],
                                "company_custom_stream_20_price": [
                                    123.45
                                ],
                                "project_custom_stream_1_price": [
                                    123.45
                                ],
                                "project_custom_stream_2_price": [
                                    123.45
                                ],
                                "project_custom_stream_3_price": [
                                    123.45
                                ],
                                "project_custom_stream_4_price": [
                                    123.45
                                ],
                                "project_custom_stream_5_price": [
                                    123.45
                                ],
                                "project_custom_stream_6_price": [
                                    123.45
                                ],
                                "project_custom_stream_7_price": [
                                    123.45
                                ],
                                "project_custom_stream_8_price": [
                                    123.45
                                ],
                                "project_custom_stream_9_price": [
                                    123.45
                                ],
                                "project_custom_stream_10_price": [
                                    123.45
                                ],
                                "project_custom_stream_11_price": [
                                    123.45
                                ],
                                "project_custom_stream_12_price": [
                                    123.45
                                ],
                                "project_custom_stream_13_price": [
                                    123.45
                                ],
                                "project_custom_stream_14_price": [
                                    123.45
                                ],
                                "project_custom_stream_15_price": [
                                    123.45
                                ],
                                "project_custom_stream_16_price": [
                                    123.45
                                ],
                                "project_custom_stream_17_price": [
                                    123.45
                                ],
                                "project_custom_stream_18_price": [
                                    123.45
                                ],
                                "project_custom_stream_19_price": [
                                    123.45
                                ],
                                "project_custom_stream_20_price": [
                                    123.45
                                ],
                                "ngl_price": [
                                    123.45
                                ],
                                "drip_condensate_price": [
                                    123.45
                                ],
                                "oil_revenue": [
                                    123.45
                                ],
                                "gas_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_1_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_2_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_3_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_4_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_5_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_6_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_7_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_8_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_9_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_10_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_11_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_12_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_13_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_14_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_15_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_16_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_17_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_18_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_19_revenue": [
                                    123.45
                                ],
                                "company_custom_stream_20_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_1_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_2_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_3_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_4_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_5_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_6_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_7_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_8_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_9_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_10_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_11_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_12_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_13_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_14_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_15_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_16_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_17_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_18_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_19_revenue": [
                                    123.45
                                ],
                                "project_custom_stream_20_revenue": [
                                    123.45
                                ],
                                "ngl_revenue": [
                                    123.45
                                ],
                                "drip_condensate_revenue": [
                                    123.45
                                ],
                                "oil_severance_tax": [
                                    123.45
                                ],
                                "gas_severance_tax": [
                                    123.45
                                ],
                                "ngl_severance_tax": [
                                    123.45
                                ],
                                "drip_condensate_severance_tax": [
                                    123.45
                                ],
                                "nri_oil": [
                                    123.45
                                ],
                                "nri_gas": [
                                    123.45
                                ],
                                "nri_company_custom_stream_1": [
                                    123.45
                                ],
                                "nri_company_custom_stream_2": [
                                    123.45
                                ],
                                "nri_company_custom_stream_3": [
                                    123.45
                                ],
                                "nri_company_custom_stream_4": [
                                    123.45
                                ],
                                "nri_company_custom_stream_5": [
                                    123.45
                                ],
                                "nri_company_custom_stream_6": [
                                    123.45
                                ],
                                "nri_company_custom_stream_7": [
                                    123.45
                                ],
                                "nri_company_custom_stream_8": [
                                    123.45
                                ],
                                "nri_company_custom_stream_9": [
                                    123.45
                                ],
                                "nri_company_custom_stream_10": [
                                    123.45
                                ],
                                "nri_company_custom_stream_11": [
                                    123.45
                                ],
                                "nri_company_custom_stream_12": [
                                    123.45
                                ],
                                "nri_company_custom_stream_13": [
                                    123.45
                                ],
                                "nri_company_custom_stream_14": [
                                    123.45
                                ],
                                "nri_company_custom_stream_15": [
                                    123.45
                                ],
                                "nri_company_custom_stream_16": [
                                    123.45
                                ],
                                "nri_company_custom_stream_17": [
                                    123.45
                                ],
                                "nri_company_custom_stream_18": [
                                    123.45
                                ],
                                "nri_company_custom_stream_19": [
                                    123.45
                                ],
                                "nri_company_custom_stream_20": [
                                    123.45
                                ],
                                "nri_project_custom_stream_1": [
                                    123.45
                                ],
                                "nri_project_custom_stream_2": [
                                    123.45
                                ],
                                "nri_project_custom_stream_3": [
                                    123.45
                                ],
                                "nri_project_custom_stream_4": [
                                    123.45
                                ],
                                "nri_project_custom_stream_5": [
                                    123.45
                                ],
                                "nri_project_custom_stream_6": [
                                    123.45
                                ],
                                "nri_project_custom_stream_7": [
                                    123.45
                                ],
                                "nri_project_custom_stream_8": [
                                    123.45
                                ],
                                "nri_project_custom_stream_9": [
                                    123.45
                                ],
                                "nri_project_custom_stream_10": [
                                    123.45
                                ],
                                "nri_project_custom_stream_11": [
                                    123.45
                                ],
                                "nri_project_custom_stream_12": [
                                    123.45
                                ],
                                "nri_project_custom_stream_13": [
                                    123.45
                                ],
                                "nri_project_custom_stream_14": [
                                    123.45
                                ],
                                "nri_project_custom_stream_15": [
                                    123.45
                                ],
                                "nri_project_custom_stream_16": [
                                    123.45
                                ],
                                "nri_project_custom_stream_17": [
                                    123.45
                                ],
                                "nri_project_custom_stream_18": [
                                    123.45
                                ],
                                "nri_project_custom_stream_19": [
                                    123.45
                                ],
                                "nri_project_custom_stream_20": [
                                    123.45
                                ],
                                "nri_ngl": [
                                    123.45
                                ],
                                "nri_drip_condensate": [
                                    123.45
                                ],
                                "nri_well_count": [
                                    123.45
                                ],
                                "total_oil_variable_expense": [
                                    123.45
                                ],
                                "total_gas_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_1_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_2_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_3_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_4_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_5_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_6_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_7_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_8_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_9_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_10_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_11_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_12_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_13_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_14_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_15_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_16_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_17_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_18_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_19_variable_expense": [
                                    123.45
                                ],
                                "total_company_custom_stream_20_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_1_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_2_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_3_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_4_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_5_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_6_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_7_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_8_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_9_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_10_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_11_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_12_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_13_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_14_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_15_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_16_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_17_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_18_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_19_variable_expense": [
                                    123.45
                                ],
                                "total_project_custom_stream_20_variable_expense": [
                                    123.45
                                ],
                                "total_ngl_variable_expense": [
                                    123.45
                                ],
                                "total_drip_condensate_variable_expense": [
                                    123.45
                                ],
                                "wi_oil": [
                                    123.45
                                ],
                                "wi_gas": [
                                    123.45
                                ],
                                "wi_company_custom_stream_1": [
                                    123.45
                                ],
                                "wi_company_custom_stream_2": [
                                    123.45
                                ],
                                "wi_company_custom_stream_3": [
                                    123.45
                                ],
                                "wi_company_custom_stream_4": [
                                    123.45
                                ],
                                "wi_company_custom_stream_5": [
                                    123.45
                                ],
                                "wi_company_custom_stream_6": [
                                    123.45
                                ],
                                "wi_company_custom_stream_7": [
                                    123.45
                                ],
                                "wi_company_custom_stream_8": [
                                    123.45
                                ],
                                "wi_company_custom_stream_9": [
                                    123.45
                                ],
                                "wi_company_custom_stream_10": [
                                    123.45
                                ],
                                "wi_company_custom_stream_11": [
                                    123.45
                                ],
                                "wi_company_custom_stream_12": [
                                    123.45
                                ],
                                "wi_company_custom_stream_13": [
                                    123.45
                                ],
                                "wi_company_custom_stream_14": [
                                    123.45
                                ],
                                "wi_company_custom_stream_15": [
                                    123.45
                                ],
                                "wi_company_custom_stream_16": [
                                    123.45
                                ],
                                "wi_company_custom_stream_17": [
                                    123.45
                                ],
                                "wi_company_custom_stream_18": [
                                    123.45
                                ],
                                "wi_company_custom_stream_19": [
                                    123.45
                                ],
                                "wi_company_custom_stream_20": [
                                    123.45
                                ],
                                "wi_project_custom_stream_1": [
                                    123.45
                                ],
                                "wi_project_custom_stream_2": [
                                    123.45
                                ],
                                "wi_project_custom_stream_3": [
                                    123.45
                                ],
                                "wi_project_custom_stream_4": [
                                    123.45
                                ],
                                "wi_project_custom_stream_5": [
                                    123.45
                                ],
                                "wi_project_custom_stream_6": [
                                    123.45
                                ],
                                "wi_project_custom_stream_7": [
                                    123.45
                                ],
                                "wi_project_custom_stream_8": [
                                    123.45
                                ],
                                "wi_project_custom_stream_9": [
                                    123.45
                                ],
                                "wi_project_custom_stream_10": [
                                    123.45
                                ],
                                "wi_project_custom_stream_11": [
                                    123.45
                                ],
                                "wi_project_custom_stream_12": [
                                    123.45
                                ],
                                "wi_project_custom_stream_13": [
                                    123.45
                                ],
                                "wi_project_custom_stream_14": [
                                    123.45
                                ],
                                "wi_project_custom_stream_15": [
                                    123.45
                                ],
                                "wi_project_custom_stream_16": [
                                    123.45
                                ],
                                "wi_project_custom_stream_17": [
                                    123.45
                                ],
                                "wi_project_custom_stream_18": [
                                    123.45
                                ],
                                "wi_project_custom_stream_19": [
                                    123.45
                                ],
                                "wi_project_custom_stream_20": [
                                    123.45
                                ],
                                "wi_ngl": [
                                    123.45
                                ],
                                "wi_drip_condensate": [
                                    123.45
                                ],
                                "wi_well_count": [
                                    123.45
                                ],
                                "wi_oil_sales_volume": [
                                    123.45
                                ],
                                "wi_gas_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_1_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_2_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_3_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_4_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_5_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_6_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_7_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_8_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_9_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_10_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_11_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_12_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_13_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_14_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_15_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_16_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_17_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_18_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_19_sales_volume": [
                                    123.45
                                ],
                                "wi_company_custom_stream_20_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_1_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_2_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_3_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_4_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_5_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_6_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_7_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_8_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_9_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_10_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_11_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_12_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_13_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_14_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_15_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_16_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_17_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_18_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_19_sales_volume": [
                                    123.45
                                ],
                                "wi_project_custom_stream_20_sales_volume": [
                                    123.45
                                ],
                                "wi_ngl_sales_volume": [
                                    123.45
                                ],
                                "wi_drip_condensate_sales_volume": [
                                    123.45
                                ],
                                "wi_water_sales_volume": [
                                    123.45
                                ],
                                "input_oil_price": [
                                    123.45
                                ],
                                "input_gas_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_1_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_2_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_3_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_4_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_5_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_6_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_7_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_8_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_9_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_10_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_11_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_12_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_13_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_14_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_15_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_16_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_17_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_18_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_19_price": [
                                    123.45
                                ],
                                "input_company_custom_stream_20_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_1_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_2_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_3_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_4_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_5_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_6_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_7_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_8_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_9_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_10_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_11_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_12_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_13_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_14_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_15_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_16_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_17_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_18_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_19_price": [
                                    123.45
                                ],
                                "input_project_custom_stream_20_price": [
                                    123.45
                                ],
                                "input_ngl_price": [
                                    123.45
                                ],
                                "input_drip_condensate_price": [
                                    123.45
                                ],
                                "oil_risk": [
                                    123.45
                                ],
                                "gas_risk": [
                                    123.45
                                ],
                                "ngl_risk": [
                                    123.45
                                ],
                                "drip_condensate_risk": [
                                    123.45
                                ],
                                "water_risk": [
                                    123.45
                                ],
                                "pre_risk_oil_volume": [
                                    123.45
                                ],
                                "pre_risk_gas_volume": [
                                    123.45
                                ],
                                "pre_risk_ngl_volume": [
                                    123.45
                                ],
                                "pre_risk_drip_condensate_volume": [
                                    123.45
                                ],
                                "pre_risk_water_volume": [
                                    123.45
                                ],
                                "oil_start_using_forecast_date": [
                                    "2020-01-01"
                                ],
                                "gas_start_using_forecast_date": [
                                    "2020-01-01"
                                ],
                                "water_start_using_forecast_date": [
                                    "2020-01-01"
                                ],
                                "oil_shrinkage": [
                                    123.45
                                ],
                                "gas_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_1_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_2_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_3_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_4_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_5_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_6_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_7_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_8_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_9_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_10_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_11_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_12_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_13_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_14_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_15_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_16_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_17_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_18_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_19_shrinkage": [
                                    123.45
                                ],
                                "company_custom_stream_20_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_1_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_2_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_3_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_4_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_5_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_6_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_7_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_8_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_9_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_10_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_11_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_12_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_13_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_14_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_15_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_16_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_17_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_18_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_19_shrinkage": [
                                    123.45
                                ],
                                "project_custom_stream_20_shrinkage": [
                                    123.45
                                ],
                                "pre_yield_gas_volume_ngl": [
                                    123.45
                                ],
                                "pre_yield_gas_volume_drip_condensate": [
                                    123.45
                                ],
                                "oil_loss": [
                                    123.45
                                ],
                                "gas_loss": [
                                    123.45
                                ],
                                "unshrunk_oil_volume": [
                                    123.45
                                ],
                                "unshrunk_gas_volume": [
                                    123.45
                                ],
                                "oil_gathering_expense": [
                                    123.45
                                ],
                                "oil_processing_expense": [
                                    123.45
                                ],
                                "oil_transportation_expense": [
                                    123.45
                                ],
                                "oil_marketing_expense": [
                                    123.45
                                ],
                                "oil_other_expense": [
                                    123.45
                                ],
                                "gas_gathering_expense": [
                                    123.45
                                ],
                                "gas_processing_expense": [
                                    123.45
                                ],
                                "gas_transportation_expense": [
                                    123.45
                                ],
                                "gas_marketing_expense": [
                                    123.45
                                ],
                                "gas_other_expense": [
                                    123.45
                                ],
                                "ngl_gathering_expense": [
                                    123.45
                                ],
                                "ngl_processing_expense": [
                                    123.45
                                ],
                                "ngl_transportation_expense": [
                                    123.45
                                ],
                                "ngl_marketing_expense": [
                                    123.45
                                ],
                                "ngl_other_expense": [
                                    123.45
                                ],
                                "drip_condensate_gathering_expense": [
                                    123.45
                                ],
                                "drip_condensate_processing_expense": [
                                    123.45
                                ],
                                "drip_condensate_transportation_expense": [
                                    123.45
                                ],
                                "drip_condensate_marketing_expense": [
                                    123.45
                                ],
                                "drip_condensate_other_expense": [
                                    123.45
                                ],
                                "oil_differentials_1": [
                                    123.45
                                ],
                                "oil_differentials_2": [
                                    123.45
                                ],
                                "oil_differentials_3": [
                                    123.45
                                ],
                                "gas_differentials_1": [
                                    123.45
                                ],
                                "gas_differentials_2": [
                                    123.45
                                ],
                                "gas_differentials_3": [
                                    123.45
                                ],
                                "ngl_differentials_1": [
                                    123.45
                                ],
                                "ngl_differentials_2": [
                                    123.45
                                ],
                                "ngl_differentials_3": [
                                    123.45
                                ],
                                "drip_condensate_differentials_1": [
                                    123.45
                                ],
                                "drip_condensate_differentials_2": [
                                    123.45
                                ],
                                "drip_condensate_differentials_3": [
                                    123.45
                                ],
                                "company_custom_stream_1_differential": [
                                    123.45
                                ],
                                "company_custom_stream_2_differential": [
                                    123.45
                                ],
                                "company_custom_stream_3_differential": [
                                    123.45
                                ],
                                "company_custom_stream_4_differential": [
                                    123.45
                                ],
                                "company_custom_stream_5_differential": [
                                    123.45
                                ],
                                "company_custom_stream_6_differential": [
                                    123.45
                                ],
                                "company_custom_stream_7_differential": [
                                    123.45
                                ],
                                "company_custom_stream_8_differential": [
                                    123.45
                                ],
                                "company_custom_stream_9_differential": [
                                    123.45
                                ],
                                "company_custom_stream_10_differential": [
                                    123.45
                                ],
                                "company_custom_stream_11_differential": [
                                    123.45
                                ],
                                "company_custom_stream_12_differential": [
                                    123.45
                                ],
                                "company_custom_stream_13_differential": [
                                    123.45
                                ],
                                "company_custom_stream_14_differential": [
                                    123.45
                                ],
                                "company_custom_stream_15_differential": [
                                    123.45
                                ],
                                "company_custom_stream_16_differential": [
                                    123.45
                                ],
                                "company_custom_stream_17_differential": [
                                    123.45
                                ],
                                "company_custom_stream_18_differential": [
                                    123.45
                                ],
                                "company_custom_stream_19_differential": [
                                    123.45
                                ],
                                "company_custom_stream_20_differential": [
                                    123.45
                                ],
                                "project_custom_stream_1_differential": [
                                    123.45
                                ],
                                "project_custom_stream_2_differential": [
                                    123.45
                                ],
                                "project_custom_stream_3_differential": [
                                    123.45
                                ],
                                "project_custom_stream_4_differential": [
                                    123.45
                                ],
                                "project_custom_stream_5_differential": [
                                    123.45
                                ],
                                "project_custom_stream_6_differential": [
                                    123.45
                                ],
                                "project_custom_stream_7_differential": [
                                    123.45
                                ],
                                "project_custom_stream_8_differential": [
                                    123.45
                                ],
                                "project_custom_stream_9_differential": [
                                    123.45
                                ],
                                "project_custom_stream_10_differential": [
                                    123.45
                                ],
                                "project_custom_stream_11_differential": [
                                    123.45
                                ],
                                "project_custom_stream_12_differential": [
                                    123.45
                                ],
                                "project_custom_stream_13_differential": [
                                    123.45
                                ],
                                "project_custom_stream_14_differential": [
                                    123.45
                                ],
                                "project_custom_stream_15_differential": [
                                    123.45
                                ],
                                "project_custom_stream_16_differential": [
                                    123.45
                                ],
                                "project_custom_stream_17_differential": [
                                    123.45
                                ],
                                "project_custom_stream_18_differential": [
                                    123.45
                                ],
                                "project_custom_stream_19_differential": [
                                    123.45
                                ],
                                "project_custom_stream_20_differential": [
                                    123.45
                                ],
                                "gross_oil_well_head_volume": [
                                    123.45
                                ],
                                "gross_gas_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_1_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_2_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_3_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_4_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_5_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_6_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_7_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_8_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_9_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_10_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_11_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_12_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_13_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_14_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_15_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_16_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_17_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_18_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_19_well_head_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_20_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_1_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_2_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_3_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_4_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_5_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_6_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_7_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_8_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_9_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_10_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_11_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_12_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_13_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_14_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_15_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_16_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_17_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_18_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_19_well_head_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_20_well_head_volume": [
                                    123.45
                                ],
                                "gross_water_well_head_volume": [
                                    123.45
                                ],
                                "net_oil_well_head_volume": [
                                    123.45
                                ],
                                "net_gas_well_head_volume": [
                                    123.45
                                ],
                                "net_water_well_head_volume": [
                                    123.45
                                ],
                                "net_gas_sales_volume_mmbtu": [
                                    123.45
                                ],
                                "gross_oil_sales_volume": [
                                    123.45
                                ],
                                "gross_gas_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_1_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_2_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_3_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_4_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_5_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_6_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_7_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_8_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_9_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_10_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_11_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_12_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_13_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_14_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_15_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_16_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_17_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_18_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_19_sales_volume": [
                                    123.45
                                ],
                                "gross_company_custom_stream_20_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_1_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_2_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_3_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_4_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_5_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_6_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_7_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_8_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_9_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_10_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_11_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_12_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_13_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_14_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_15_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_16_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_17_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_18_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_19_sales_volume": [
                                    123.45
                                ],
                                "gross_project_custom_stream_20_sales_volume": [
                                    123.45
                                ],
                                "gross_ngl_sales_volume": [
                                    123.45
                                ],
                                "gross_drip_condensate_sales_volume": [
                                    123.45
                                ],
                                "net_oil_sales_volume": [
                                    123.45
                                ],
                                "net_gas_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_1_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_2_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_3_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_4_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_5_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_6_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_7_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_8_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_9_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_10_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_11_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_12_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_13_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_14_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_15_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_16_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_17_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_18_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_19_sales_volume": [
                                    123.45
                                ],
                                "net_company_custom_stream_20_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_1_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_2_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_3_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_4_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_5_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_6_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_7_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_8_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_9_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_10_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_11_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_12_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_13_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_14_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_15_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_16_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_17_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_18_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_19_sales_volume": [
                                    123.45
                                ],
                                "net_project_custom_stream_20_sales_volume": [
                                    123.45
                                ],
                                "net_water_sales_volume": [
                                    123.45
                                ],
                                "net_ngl_sales_volume": [
                                    123.45
                                ],
                                "net_drip_condensate_sales_volume": [
                                    123.45
                                ],
                                "created_at": [
                                    "2020-01-01"
                                ],
                                "state_tax_rate": [
                                    123.45
                                ],
                                "federal_tax_rate": [
                                    123.45
                                ],
                                "ad_valorem_tax": [
                                    123.45
                                ],
                                "afit_first_discount_cash_flow": [
                                    123.45
                                ],
                                "afit_second_discount_cash_flow": [
                                    123.45
                                ],
                                "after_income_tax_cash_flow": [
                                    123.45
                                ],
                                "before_income_tax_cash_flow": [
                                    123.45
                                ],
                                "capex_qualifier": [
                                    "string"
                                ],
                                "combo_name": [
                                    "string"
                                ],
                                "date": [
                                    "2020-01-01"
                                ],
                                "dates_qualifier": [
                                    "string"
                                ],
                                "depletion": [
                                    123.45
                                ],
                                "depreciation": [
                                    123.45
                                ],
                                "error": [
                                    "string"
                                ],
                                "expenses_qualifier": [
                                    "string"
                                ],
                                "federal_income_tax": [
                                    123.45
                                ],
                                "first_discount_cash_flow": [
                                    123.45
                                ],
                                "forecast_p_series_qualifier": [
                                    "string"
                                ],
                                "forecast_qualifier": [
                                    "string"
                                ],
                                "gross_boe_sales_volume": [
                                    123.45
                                ],
                                "gross_boe_well_head_volume": [
                                    123.45
                                ],
                                "intangible_abandonment": [
                                    123.45
                                ],
                                "intangible_appraisal": [
                                    123.45
                                ],
                                "intangible_artificial_lift": [
                                    123.45
                                ],
                                "intangible_completion": [
                                    123.45
                                ],
                                "intangible_depletion": [
                                    123.45
                                ],
                                "intangible_depreciation": [
                                    123.45
                                ],
                                "intangible_development": [
                                    123.45
                                ],
                                "intangible_drilling": [
                                    123.45
                                ],
                                "intangible_exploration": [
                                    123.45
                                ],
                                "intangible_facilities": [
                                    123.45
                                ],
                                "intangible_leasehold": [
                                    123.45
                                ],
                                "intangible_legal": [
                                    123.45
                                ],
                                "intangible_other_investment": [
                                    123.45
                                ],
                                "intangible_pad": [
                                    123.45
                                ],
                                "intangible_pipelines": [
                                    123.45
                                ],
                                "intangible_salvage": [
                                    123.45
                                ],
                                "intangible_waterline": [
                                    123.45
                                ],
                                "intangible_workover": [
                                    123.45
                                ],
                                "monthly_well_cost": [
                                    123.45
                                ],
                                "net_boe_sales_volume": [
                                    123.45
                                ],
                                "net_profit": [
                                    123.45
                                ],
                                "other_monthly_cost_1": [
                                    123.45
                                ],
                                "other_monthly_cost_2": [
                                    123.45
                                ],
                                "other_monthly_cost_3": [
                                    123.45
                                ],
                                "other_monthly_cost_4": [
                                    123.45
                                ],
                                "other_monthly_cost_5": [
                                    123.45
                                ],
                                "other_monthly_cost_6": [
                                    123.45
                                ],
                                "other_monthly_cost_7": [
                                    123.45
                                ],
                                "other_monthly_cost_8": [
                                    123.45
                                ],
                                "ownership_reversion_qualifier": [
                                    "string"
                                ],
                                "percentage_depletion": [
                                    123.45
                                ],
                                "production_taxes_qualifier": [
                                    "string"
                                ],
                                "production_vs_fit_qualifier": [
                                    "string"
                                ],
                                "reserves_category_qualifier": [
                                    "string"
                                ],
                                "risking_qualifier": [
                                    "string"
                                ],
                                "run_date": [
                                    "2020-01-01"
                                ],
                                "run_id": [
                                    "string"
                                ],
                                "schedule_qualifier": [
                                    "string"
                                ],
                                "second_discount_cash_flow": [
                                    123.45
                                ],
                                "state_income_tax": [
                                    123.45
                                ],
                                "stream_properties_qualifier": [
                                    "string"
                                ],
                                "tangible_abandonment": [
                                    123.45
                                ],
                                "tangible_appraisal": [
                                    123.45
                                ],
                                "tangible_artificial_lift": [
                                    123.45
                                ],
                                "tangible_completion": [
                                    123.45
                                ],
                                "tangible_depletion": [
                                    123.45
                                ],
                                "tangible_depreciation": [
                                    123.45
                                ],
                                "tangible_development": [
                                    123.45
                                ],
                                "tangible_drilling": [
                                    123.45
                                ],
                                "tangible_exploration": [
                                    123.45
                                ],
                                "tangible_facilities": [
                                    123.45
                                ],
                                "tangible_leasehold": [
                                    123.45
                                ],
                                "tangible_legal": [
                                    123.45
                                ],
                                "tangible_other_investment": [
                                    123.45
                                ],
                                "tangible_pad": [
                                    123.45
                                ],
                                "tangible_pipelines": [
                                    123.45
                                ],
                                "tangible_salvage": [
                                    123.45
                                ],
                                "tangible_waterline": [
                                    123.45
                                ],
                                "tangible_workover": [
                                    123.45
                                ],
                                "taxable_income": [
                                    123.45
                                ],
                                "total_abandonment": [
                                    123.45
                                ],
                                "total_appraisal": [
                                    123.45
                                ],
                                "total_artificial_lift": [
                                    123.45
                                ],
                                "total_capex": [
                                    123.45
                                ],
                                "total_completion": [
                                    123.45
                                ],
                                "total_deductions": [
                                    123.45
                                ],
                                "total_development": [
                                    123.45
                                ],
                                "total_drilling": [
                                    123.45
                                ],
                                "total_expense": [
                                    123.45
                                ],
                                "total_exploration": [
                                    123.45
                                ],
                                "total_facilities": [
                                    123.45
                                ],
                                "total_fixed_expense": [
                                    123.45
                                ],
                                "total_intangible_capex": [
                                    123.45
                                ],
                                "total_leasehold": [
                                    123.45
                                ],
                                "total_legal": [
                                    123.45
                                ],
                                "total_other_investment": [
                                    123.45
                                ],
                                "total_pad": [
                                    123.45
                                ],
                                "total_pipelines": [
                                    123.45
                                ],
                                "total_production_tax": [
                                    123.45
                                ],
                                "total_revenue": [
                                    123.45
                                ],
                                "total_salvage": [
                                    123.45
                                ],
                                "total_severance_tax": [
                                    123.45
                                ],
                                "total_tangible_capex": [
                                    123.45
                                ],
                                "total_variable_expense": [
                                    123.45
                                ],
                                "total_waterline": [
                                    123.45
                                ],
                                "total_workover": [
                                    123.45
                                ],
                                "warning": [
                                    "string"
                                ],
                                "water_disposal": [
                                    123.45
                                ],
                                "well_id": [
                                    "string"
                                ],
                                "well_index": [
                                    123.45
                                ],
                                "wi_boe_sales_volume": [
                                    123.45
                                ],
                                "combo_well_id": [
                                    "string"
                                ],
                                "gross_well_count": [
                                    123.45
                                ],
                                "reversion_date": [
                                    "string"
                                ],
                                "gor": [
                                    123.45
                                ],
                                "wor": [
                                    123.45
                                ],
                                "water_cut": [
                                    123.45
                                ],
                                "econ_first_production_date": [
                                    "2020-01-01"
                                ],
                                "pricing_qualifier": [
                                    "string"
                                ],
                                "differentials_qualifier": [
                                    "string"
                                ],
                                "incremental_name": [
                                    "string"
                                ],
                                "incremental_index": [
                                    123
                                ],
                                "combo_well_incremental_id": [
                                    "string"
                                ],
                                "first_discounted_capex": [
                                    123.45
                                ],
                                "second_discounted_capex": [
                                    123.45
                                ],
                                "net_income": [
                                    123.45
                                ],
                                "first_discount_net_income": [
                                    123.45
                                ],
                                "second_discount_net_income": [
                                    123.45
                                ],
                                "ngl_yield": [
                                    123.45
                                ],
                                "drip_condensate_yield": [
                                    123.45
                                ],
                                "gas_flare": [
                                    123.45
                                ],
                                "gross_mcfe_well_head_volume": [
                                    123.45
                                ],
                                "gross_mcfe_sales_volume": [
                                    123.45
                                ],
                                "wi_mcfe_sales_volume": [
                                    123.45
                                ],
                                "net_mcfe_sales_volume": [
                                    123.45
                                ],
                                "lease_nri": [
                                    123.45
                                ],
                                "pre_flare_gas_volume": [
                                    123.45
                                ],
                                "total_gross_capex": [
                                    123.45
                                ],
                                "gross_co2e_mass_emission": [
                                    123.45
                                ],
                                "wi_co2e_mass_emission": [
                                    123.45
                                ],
                                "nri_co2e_mass_emission": [
                                    123.45
                                ],
                                "gross_co2_mass_emission": [
                                    123.45
                                ],
                                "wi_co2_mass_emission": [
                                    123.45
                                ],
                                "nri_co2_mass_emission": [
                                    123.45
                                ],
                                "gross_ch4_mass_emission": [
                                    123.45
                                ],
                                "wi_ch4_mass_emission": [
                                    123.45
                                ],
                                "nri_ch4_mass_emission": [
                                    123.45
                                ],
                                "gross_n2o_mass_emission": [
                                    123.45
                                ],
                                "wi_n2o_mass_emission": [
                                    123.45
                                ],
                                "nri_n2o_mass_emission": [
                                    123.45
                                ],
                                "co2e_expense": [
                                    123.45
                                ],
                                "co2_expense": [
                                    123.45
                                ],
                                "ch4_expense": [
                                    123.45
                                ],
                                "n2o_expense": [
                                    123.45
                                ],
                                "total_carbon_expense": [
                                    123.45
                                ],
                                "tax_credit": [
                                    123.45
                                ],
                                "comp_n2_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_n2_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_n2_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_n2_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_n2_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_n2_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_n2_ngl_input_price": [
                                    123.45
                                ],
                                "comp_n2_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_n2_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_n2_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_n2_gas_net_volume": [
                                    123.45
                                ],
                                "comp_n2_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_n2_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_n2_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_n2_gas_input_price": [
                                    123.45
                                ],
                                "comp_n2_gas_realized_price": [
                                    123.45
                                ],
                                "comp_co2_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_co2_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_co2_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_co2_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_co2_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_co2_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_co2_ngl_input_price": [
                                    123.45
                                ],
                                "comp_co2_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_co2_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_co2_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_co2_gas_net_volume": [
                                    123.45
                                ],
                                "comp_co2_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_co2_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_co2_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_co2_gas_input_price": [
                                    123.45
                                ],
                                "comp_co2_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c1_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c1_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c1_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c1_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c1_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c1_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c1_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c1_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c1_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c1_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c1_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c1_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c1_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c1_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c1_gas_input_price": [
                                    123.45
                                ],
                                "comp_c1_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c2_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c2_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c2_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c2_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c2_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c2_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c2_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c2_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c2_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c2_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c2_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c2_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c2_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c2_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c2_gas_input_price": [
                                    123.45
                                ],
                                "comp_c2_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c3_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c3_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c3_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c3_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c3_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c3_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c3_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c3_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c3_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c3_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c3_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c3_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c3_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c3_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c3_gas_input_price": [
                                    123.45
                                ],
                                "comp_c3_gas_realized_price": [
                                    123.45
                                ],
                                "comp_ic4_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_ic4_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_ic4_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_ic4_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_ic4_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_ic4_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_ic4_ngl_input_price": [
                                    123.45
                                ],
                                "comp_ic4_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_ic4_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_ic4_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_ic4_gas_net_volume": [
                                    123.45
                                ],
                                "comp_ic4_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_ic4_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_ic4_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_ic4_gas_input_price": [
                                    123.45
                                ],
                                "comp_ic4_gas_realized_price": [
                                    123.45
                                ],
                                "comp_nc4_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_nc4_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_nc4_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_nc4_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_nc4_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_nc4_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_nc4_ngl_input_price": [
                                    123.45
                                ],
                                "comp_nc4_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_nc4_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_nc4_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_nc4_gas_net_volume": [
                                    123.45
                                ],
                                "comp_nc4_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_nc4_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_nc4_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_nc4_gas_input_price": [
                                    123.45
                                ],
                                "comp_nc4_gas_realized_price": [
                                    123.45
                                ],
                                "comp_ic5_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_ic5_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_ic5_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_ic5_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_ic5_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_ic5_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_ic5_ngl_input_price": [
                                    123.45
                                ],
                                "comp_ic5_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_ic5_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_ic5_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_ic5_gas_net_volume": [
                                    123.45
                                ],
                                "comp_ic5_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_ic5_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_ic5_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_ic5_gas_input_price": [
                                    123.45
                                ],
                                "comp_ic5_gas_realized_price": [
                                    123.45
                                ],
                                "comp_nc5_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_nc5_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_nc5_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_nc5_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_nc5_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_nc5_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_nc5_ngl_input_price": [
                                    123.45
                                ],
                                "comp_nc5_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_nc5_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_nc5_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_nc5_gas_net_volume": [
                                    123.45
                                ],
                                "comp_nc5_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_nc5_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_nc5_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_nc5_gas_input_price": [
                                    123.45
                                ],
                                "comp_nc5_gas_realized_price": [
                                    123.45
                                ],
                                "comp_ic6_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_ic6_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_ic6_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_ic6_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_ic6_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_ic6_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_ic6_ngl_input_price": [
                                    123.45
                                ],
                                "comp_ic6_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_ic6_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_ic6_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_ic6_gas_net_volume": [
                                    123.45
                                ],
                                "comp_ic6_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_ic6_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_ic6_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_ic6_gas_input_price": [
                                    123.45
                                ],
                                "comp_ic6_gas_realized_price": [
                                    123.45
                                ],
                                "comp_nc6_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_nc6_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_nc6_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_nc6_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_nc6_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_nc6_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_nc6_ngl_input_price": [
                                    123.45
                                ],
                                "comp_nc6_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_nc6_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_nc6_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_nc6_gas_net_volume": [
                                    123.45
                                ],
                                "comp_nc6_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_nc6_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_nc6_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_nc6_gas_input_price": [
                                    123.45
                                ],
                                "comp_nc6_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c7_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c7_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c7_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c7_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c7_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c7_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c7_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c7_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c7_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c7_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c7_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c7_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c7_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c7_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c7_gas_input_price": [
                                    123.45
                                ],
                                "comp_c7_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c8_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c8_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c8_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c8_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c8_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c8_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c8_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c8_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c8_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c8_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c8_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c8_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c8_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c8_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c8_gas_input_price": [
                                    123.45
                                ],
                                "comp_c8_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c9_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c9_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c9_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c9_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c9_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c9_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c9_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c9_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c9_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c9_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c9_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c9_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c9_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c9_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c9_gas_input_price": [
                                    123.45
                                ],
                                "comp_c9_gas_realized_price": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_input_price": [
                                    123.45
                                ],
                                "comp_c10plus_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_c10plus_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_c10plus_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_c10plus_gas_net_volume": [
                                    123.45
                                ],
                                "comp_c10plus_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_c10plus_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_c10plus_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_c10plus_gas_input_price": [
                                    123.45
                                ],
                                "comp_c10plus_gas_realized_price": [
                                    123.45
                                ],
                                "comp_h2s_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_h2s_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_h2s_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_h2s_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_h2s_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_h2s_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_h2s_ngl_input_price": [
                                    123.45
                                ],
                                "comp_h2s_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_h2s_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_h2s_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_h2s_gas_net_volume": [
                                    123.45
                                ],
                                "comp_h2s_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_h2s_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_h2s_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_h2s_gas_input_price": [
                                    123.45
                                ],
                                "comp_h2s_gas_realized_price": [
                                    123.45
                                ],
                                "comp_h2_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_h2_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_h2_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_h2_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_h2_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_h2_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_h2_ngl_input_price": [
                                    123.45
                                ],
                                "comp_h2_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_h2_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_h2_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_h2_gas_net_volume": [
                                    123.45
                                ],
                                "comp_h2_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_h2_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_h2_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_h2_gas_input_price": [
                                    123.45
                                ],
                                "comp_h2_gas_realized_price": [
                                    123.45
                                ],
                                "comp_h2o_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_h2o_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_h2o_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_h2o_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_h2o_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_h2o_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_h2o_ngl_input_price": [
                                    123.45
                                ],
                                "comp_h2o_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_h2o_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_h2o_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_h2o_gas_net_volume": [
                                    123.45
                                ],
                                "comp_h2o_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_h2o_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_h2o_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_h2o_gas_input_price": [
                                    123.45
                                ],
                                "comp_h2o_gas_realized_price": [
                                    123.45
                                ],
                                "comp_he_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_he_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_he_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_he_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_he_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_he_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_he_ngl_input_price": [
                                    123.45
                                ],
                                "comp_he_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_he_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_he_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_he_gas_net_volume": [
                                    123.45
                                ],
                                "comp_he_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_he_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_he_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_he_gas_input_price": [
                                    123.45
                                ],
                                "comp_he_gas_realized_price": [
                                    123.45
                                ],
                                "comp_o2_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_o2_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_o2_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_o2_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_o2_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_o2_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_o2_ngl_input_price": [
                                    123.45
                                ],
                                "comp_o2_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_o2_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_o2_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_o2_gas_net_volume": [
                                    123.45
                                ],
                                "comp_o2_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_o2_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_o2_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_o2_gas_input_price": [
                                    123.45
                                ],
                                "comp_o2_gas_realized_price": [
                                    123.45
                                ],
                                "comp_remaining_ngl_gross_volume": [
                                    123.45
                                ],
                                "comp_remaining_ngl_wi_volume": [
                                    123.45
                                ],
                                "comp_remaining_ngl_net_volume": [
                                    123.45
                                ],
                                "comp_remaining_ngl_gross_revenue": [
                                    123.45
                                ],
                                "comp_remaining_ngl_wi_revenue": [
                                    123.45
                                ],
                                "comp_remaining_ngl_net_revenue": [
                                    123.45
                                ],
                                "comp_remaining_ngl_input_price": [
                                    123.45
                                ],
                                "comp_remaining_ngl_realized_price": [
                                    123.45
                                ],
                                "comp_remaining_gas_gross_volume": [
                                    123.45
                                ],
                                "comp_remaining_gas_wi_volume": [
                                    123.45
                                ],
                                "comp_remaining_gas_net_volume": [
                                    123.45
                                ],
                                "comp_remaining_gas_gross_revenue": [
                                    123.45
                                ],
                                "comp_remaining_gas_wi_revenue": [
                                    123.45
                                ],
                                "comp_remaining_gas_net_revenue": [
                                    123.45
                                ],
                                "comp_remaining_gas_input_price": [
                                    123.45
                                ],
                                "comp_remaining_gas_realized_price": [
                                    123.45
                                ],
                                "company_custom_stream_1_gathering_expense": [
                                    123.45
                                ],
                                "operations_qualifier": [
                                    "string"
                                ]
                            }
                        }
                    ]
                }
            ],
            "scenario_name": "string",
            "scenario_id": "string"
        }
        """
        if not columns:
            raise ValueError('columns is required; the API rejects a monthly-econ-results request without columns')

        filters = {'columns': ','.join(columns)}
        url = self.get_econ_run_monthly_econ_result_by_id_url(project_id, scenario_id, econ_run_id, filters)
        params = {'take': GET_LIMIT}

        return self._get_items(url, params)

    def update_econ_run_combo_names(self, econruns: ItemList, project_id: str, scenario_id: str) -> None:
        """
        Add combo names to the econ run data.
        """
        for i, run in enumerate(econruns):
            econ_run_id = str(run['id'])
            combo_names = self.get_econ_run_combo_names(project_id, scenario_id, econ_run_id)
            run['comboNames'] = combo_names
            # _ = run.pop('outputParams')
            econruns[i] = run

        return

    def post_econ_run_monthly_export(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Create a monthly export for a specific project id, scenario id,
        econ run id, and returns a monthly export id to get the results.
        """
        url = self.get_econ_run_monthly_export_id_url(project_id, scenario_id, econ_run_id)

        items = self._post_items(url, data=[])
        id_ = str(items[0]['id'])

        return id_

    def get_econ_run_monthly_export(
        self, project_id: str, scenario_id: str, econ_run_id: str, monthly_export_id: str
    ) -> ItemList:
        """
        Returns a list of monthly exports for a specific project id,
        scenario id, econ run id, and monthly export id.
        """
        url = self.get_econ_run_monthly_export_url(project_id, scenario_id, econ_run_id, monthly_export_id)

        params = {
            'take': GET_LIMIT_MONTHLY_EXPORTS,
            'concurrency': CONCURRENCY_MONTHLY_EXPORTS,
        }
        items = self._get_items(url, params)

        results = cast(ItemList, items[0]['results'])

        results_flat = [result for result in (flatten_outputs(result) for result in results) if result is not None]
        return results_flat

    def get_stream_econ_run_monthly_export(
        self, project_id: str, scenario_id: str, econ_run_id: str, monthly_export_id: str
    ) -> Iterator[ItemList]:
        """
        Similar to `get_econ_run_monthly_export` but instead streams the data
        yielding chunks of 100 items at a time, where each item is a list of
        monthly exports for a specific project id, scenario id, econ run id,
        and monthly export id.
        """
        url = self.get_econ_run_monthly_export_url(project_id, scenario_id, econ_run_id, monthly_export_id)

        params = {
            'take': GET_LIMIT_MONTHLY_EXPORTS,
            'concurrency': CONCURRENCY_MONTHLY_EXPORTS,
        }
        iter_items = self._get_items_iterator(url, params)

        for items in iter_items:
            for item in items:
                results = cast(ItemList, item['results'])

                results_flat = [
                    result for result in (flatten_outputs(result) for result in results) if result is not None
                ]
                yield results_flat
