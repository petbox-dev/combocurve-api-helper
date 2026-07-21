from typing import Dict, List

_COMMON_HEAD = [
    'Model Id',
    'Created At',
    'Project Name',
    'Model Type',
    'Model Name',
    'New Name',
    'Embedded Lookup Table',
]

COLUMNS: Dict[str, List[str]] = {
    'StreamProperties': _COMMON_HEAD
    + [
        'Key',
        'Category',
        'Criteria',
        'Value',
        'Period',
        'Unit',
        'Gas Shrinkage Condition',
        'Rate Type',
        'Rate Rows Calculation Method',
        'Yield Source',
        'Yield (BBL/MMCF)',
        'Mol %',
        'Gal/lb-mol Factor',
        'Plant Eff (%)',
        'Shrink (% Remaining)',
        'BTU (MBTU/MCF)',
        'Post Extraction (%)',
    ]
    + ['Last Update'],
    'Differentials': _COMMON_HEAD
    + [
        'Key',
        'Phase',
        'Criteria',
        'Value',
        'Period',
        'Unit',
        'Escalation',
    ]
    + ['Last Update'],
    'ProductionTaxes': _COMMON_HEAD
    + [
        'Production Taxes State',
        'Key',
        'Stream Type',
        'Category',
        'Criteria',
        'Value',
        'Period',
        'Unit',
        'Description',
        'Shrinkage Condition',
        'Escalation',
        'Calculation',
        'Deduct Severance Tax',
        'Rate Type',
        'Rate Rows Calculation Method',
    ]
    + ['Last Update'],
    'Expenses': _COMMON_HEAD
    + [
        'Key',
        'Category',
        'Criteria',
        'Value',
        'Period',
        'Unit',
        'Description',
        'Shrinkage Condition',
        'Escalation',
        'Calculation',
        'Affect Econ Limit',
        'Deduct bef Sev Tax',
        'Deduct bef Ad Val Tax',
        'Stop at Econ Limit',
        'Expense bef FPD',
        'Cap',
        'Paying WI / Earning WI',
        'Rate Type',
        'Rate Rows Calculation Method',
    ]
    + ['Last Update'],
    'Capex': _COMMON_HEAD
    + [
        'Category',
        'Description',
        'Tangible (M$)',
        'Intangible (M$)',
        'Criteria',
        'From Schedule',
        'From Headers',
        'Value',
        'CAPEX or Expense',
        'Appear After Econ Limit',
        'Calculation',
        'Escalation',
        'Escalation Start Criteria',
        'Escalation Start Value (Days/Date)',
        'Depreciation',
        'Paying WI / Earning WI',
        # Model-level $/ft objects that CC's own CSV export omits; captured losslessly as
        # JSON by CapexMapper (CC ignores unknown headers on import). These header strings
        # MUST match capex._DRILLING_COST_COL / _COMPLETION_COST_COL.
        'Drilling Cost ($/ft)',
        'Completion Cost ($/ft)',
    ]
    + ['Last Update'],
    'ReservesCategory': _COMMON_HEAD
    + [
        'PRMS Class',
        'PRMS Category',
        'PRMS Sub Category',
    ]
    + ['Last Update'],
    'ActualOrForecast': _COMMON_HEAD
    + [
        'Key',
        'Category',
        'Criteria',
        'Value',
    ]
    + ['Last Update'],
    'Pricing': _COMMON_HEAD
    + [
        'Phase',
        'Category',
        'Criteria',
        'Value',
        'Period',
        'Unit',
        'Cap',
        'Price Ratio',
        'Escalation',
    ]
    + ['Last Update'],
    'DateSettings': _COMMON_HEAD
    + [
        'Max Econ Life (Years)',
        'As of Date',
        'Discount Date',
        'CF Prior To As Of Date',
        'Prod Data Resolution',
        '1st FPD Source',
        '2nd FPD Source',
        '3rd FPD Source',
        '4th FPD Source',
        'Use Forecast/Schedule When No Prod',
        'Cut Off Criteria',
        'Cut Off Value',
        'Align Dependent Phases',
        'Min Life Criteria',
        'Min Life Value',
        'Include CAPEX',
        'Discount',
        'Econ Limit Delay',
        'Trigger ECL CAPEX (Unecon)',
        'Tolerant Negative CF',
    ]
    + ['Last Update'],
    'OwnershipReversion': _COMMON_HEAD
    + [
        'Key',
        'Reversion Type',
        'Reversion Value',
        'WI %',
        'NRI %',
        'Lease NRI %',
        'Reversion Tied To',
        'Balance',
        'Include NPI',
        'NPI Type',
        'NPI %',
        'Oil NRI %',
        'Gas NRI %',
        'NGL NRI %',
        'Drip Cond. NRI %',
        'Rev Basis WI %',
        'Rev Basis NRI %',
    ]
    + ['Last Update'],
    'Risking': _COMMON_HEAD
    + [
        'Key',
        'Phase',
        'Category',
        'Description',
        'Risk Hist Prod',
        'Risk NGL & Drip Cond via Gas Risk',
        'Value',
        'Period',
        'Criteria',
        'Criteria Start',
        'Criteria End',
        'Repeat Range Of Dates',
        'Total Occurrences',
        'Unit',
        'Scale Post Shut-in Factor',
        'Scale Post Shut-In End Criteria',
        'Scale Post Shut-In End',
        'Fixed Expense',
        'CAPEX',
    ]
    + ['Last Update'],
}
