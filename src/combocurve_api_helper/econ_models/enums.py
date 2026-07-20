from enum import Enum
from typing import Dict


class StrEnum(str, Enum):  # Python <3.11 shim
    pass


class Criteria(StrEnum):
    FromHeaders = 'fromHeaders'
    FromSchedule = 'fromSchedule'
    Date = 'date'
    AsOf = 'offsetToAsOf'
    DiscountDate = 'offsetToDiscountDate'
    FPD = 'offsetToFpd'
    EconLimit = 'offsetToEconLimit'
    MajorSegment = 'offsetToMajorSegment'
    OilRate = 'oilRate'
    GasRate = 'gasRate'
    WaterRate = 'waterRate'
    TotalFluidRate = 'totalFluidRate'


class OffsetTo(StrEnum):
    _None = ''
    PermitDate = 'offset_to_permit_date'
    SpudDate = 'offset_to_spud_date'
    RigReleaseDate = 'offset_to_rig_release_date'
    DrillStartDate = 'offset_to_drill_start_date'
    DrillEndDate = 'offset_to_drill_end_date'
    CompletionStartDate = 'offset_to_completion_start_date'
    CompletionEndDate = 'offset_to_completion_end_date'
    # Verified live (project 'Sample Project A | AFE', 9 SAMPLE_LATERAL models): real
    # otherCapex `fromHeaders` rows carry the abbreviated token 'offset_to_first_prod_date'
    # (companion API date-key 'firstProdDate'), NOT the longer 'offset_to_first_production_
    # date' this member previously held (an unverified ported guess with no live consumer --
    # confirmed via a whole-repo grep before this fix, 2026-07-20).
    FirstProductionDate = 'offset_to_first_prod_date'
    TIL = 'offset_to_til'
    RefracDate = 'offset_to_refrac_date'
    FirstProdDateDailyCalc = 'offset_to_first_prod_date_daily_calc'
    FirstPProdDateMonthlyCalc = 'offset_to_first_prod_date_monthly_calc'
    LastProdDateDailyCalc = 'offset_to_last_prod_date_daily_calc'
    LastProdDateMonthlyCalc = 'offset_to_last_prod_date_monthly_calc'
    CustomDate0 = 'offset_to_custom_date_0'
    CustomDate1 = 'offset_to_custom_date_1'
    CustomDate2 = 'offset_to_custom_date_2'
    CustomDate3 = 'offset_to_custom_date_3'
    CustomDate4 = 'offset_to_custom_date_4'
    CustomDate5 = 'offset_to_custom_date_5'
    CustomDate6 = 'offset_to_custom_date_6'
    CustomDate7 = 'offset_to_custom_date_7'
    CustomDate8 = 'offset_to_custom_date_8'
    CustomDate9 = 'offset_to_custom_date_9'


class CapExCategory(StrEnum):
    Exploration = 'exploration'
    Appraisal = 'appraisal'
    Pad = 'pad'
    Drilling = 'drilling'
    Completion = 'completion'
    Facilities = 'facilities'
    OtherInvestment = 'other_investment'
    ArtificialLift = 'artificial_lift'
    Salvage = 'salvage'
    Abandonment = 'abandonment'
    Legal = 'legal'
    Workover = 'workover'
    Leasehold = 'leasehold'
    Development = 'development'
    Pipelines = 'pipelines'
    Waterline = 'waterline'


class GrossOrNet(StrEnum):
    Gross = 'gross'
    Net = 'net'


# API criteria value -> CSV Criteria string (verified against exports)
CRITERIA_TO_CSV: Dict[str, str] = {
    Criteria.FromHeaders.value: 'from headers',
    Criteria.FromSchedule.value: 'from schedule',
    Criteria.Date.value: 'date',
    Criteria.AsOf.value: 'as of',
    Criteria.DiscountDate.value: 'disc date',
    Criteria.FPD.value: 'fpd',
    Criteria.EconLimit.value: 'econ limit',
    Criteria.MajorSegment.value: 'maj seg',
    Criteria.OilRate.value: 'oil rate',
    Criteria.GasRate.value: 'gas rate',
    Criteria.WaterRate.value: 'water rate',
    Criteria.TotalFluidRate.value: 'total fluid rate',
}
CRITERIA_FROM_CSV: Dict[str, str] = {v: k for k, v in CRITERIA_TO_CSV.items()}

# OffsetTo value -> CSV display (only the values observed in exports are mapped;
# extend as new ones surface — an unmapped token raises in the mapper).
OFFSET_TO_HEADER_CSV: Dict[str, str] = {
    OffsetTo.SpudDate.value: 'Spud Date',
    OffsetTo.CompletionStartDate.value: 'Completion Start Date',
    # 'offset_to_first_prod_date' -> 'First Prod Date': strip the 'offset_to_' prefix and
    # title-case the remaining words, same convention as the other two entries above --
    # verified live (project 'Sample Project A | AFE', 9 SAMPLE_LATERAL models).
    OffsetTo.FirstProductionDate.value: 'First Prod Date',
}
OFFSET_TO_SCHEDULE_CSV: Dict[str, str] = {
    OffsetTo.SpudDate.value: 'Spud Start',
    OffsetTo.CompletionStartDate.value: 'Completion Start',
}
OFFSET_FROM_HEADER_CSV: Dict[str, str] = {v: k for k, v in OFFSET_TO_HEADER_CSV.items()}
OFFSET_FROM_SCHEDULE_CSV: Dict[str, str] = {v: k for k, v in OFFSET_TO_SCHEDULE_CSV.items()}

# OffsetTo value -> companion API date-header key carried alongside a fromHeaders/
# fromSchedule otherCapex row (e.g. {'fromHeaders': 'offset_to_spud_date', 'spudDate': 0}).
# Ported verbatim from cc-afe-sync `models/capex.py` `CapExRow._dateLookup`, re-keyed by
# the OffsetTo *value* (str) instead of the enum member so it composes with plain dict
# lookups elsewhere in this package. `_None` is intentionally omitted -- it is not a real
# fromHeaders/fromSchedule token.
OFFSET_TO_API_DATEKEY: Dict[str, str] = {
    OffsetTo.PermitDate.value: 'permitDate',
    OffsetTo.SpudDate.value: 'spudDate',
    OffsetTo.RigReleaseDate.value: 'dateRigRelease',
    OffsetTo.DrillStartDate.value: 'drillStartDate',
    OffsetTo.DrillEndDate.value: 'drillEndDate',
    OffsetTo.CompletionStartDate.value: 'completionStartDate',
    OffsetTo.CompletionEndDate.value: 'completionEndDate',
    OffsetTo.FirstProductionDate.value: 'firstProdDate',
    OffsetTo.TIL.value: 'til',
    OffsetTo.RefracDate.value: 'refracDate',
    OffsetTo.FirstProdDateDailyCalc.value: 'firstProdDateDaily',
    OffsetTo.FirstPProdDateMonthlyCalc.value: 'firstPProdDateMonthly',
    OffsetTo.LastProdDateDailyCalc.value: 'lastProdDateDaily',
    OffsetTo.LastProdDateMonthlyCalc.value: 'lastProdDateMonthly',
    OffsetTo.CustomDate0.value: 'customDateHeader0',
    OffsetTo.CustomDate1.value: 'customDateHeader1',
    OffsetTo.CustomDate2.value: 'customDateHeader2',
    OffsetTo.CustomDate3.value: 'customDateHeader3',
    OffsetTo.CustomDate4.value: 'customDateHeader4',
    OffsetTo.CustomDate5.value: 'customDateHeader5',
    OffsetTo.CustomDate6.value: 'customDateHeader6',
    OffsetTo.CustomDate7.value: 'customDateHeader7',
    OffsetTo.CustomDate8.value: 'customDateHeader8',
    OffsetTo.CustomDate9.value: 'customDateHeader9',
}
