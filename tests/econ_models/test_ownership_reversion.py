import copy
from typing import Any, Dict

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.ownership_reversion import OwnershipReversionMapper

# Initial-only -- ALL 20 reversion keys explicitly present and null.
EIGHT_EIGHTHS: Dict[str, Any] = {
    'id': '000000000000000000000016',
    'name': '8/8ths',
    'unique': False,
    'createdAt': '2024-11-05T17:02:51.157Z',
    'updatedAt': '2024-11-05T17:02:51.157Z',
    'econModelType': 'OwnershipReversion',
    'ownership': {
        'initialOwnership': {
            'workingInterest': 100,
            'netProfitInterestType': 'expense',
            'netProfitInterest': 0,
            'netRevenueInterest': 75,
            'leaseNetRevenueInterest': 75,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
        },
        'firstReversion': None,
        'secondReversion': None,
        'thirdReversion': None,
        'fourthReversion': None,
        'fifthReversion': None,
        'sixthReversion': None,
        'seventhReversion': None,
        'eighthReversion': None,
        'ninthReversion': None,
        'tenthReversion': None,
        'eleventhReversion': None,
        'twelfthReversion': None,
        'thirteenthReversion': None,
        'fourteenthReversion': None,
        'fifteenthReversion': None,
        'sixteenthReversion': None,
        'seventeenthReversion': None,
        'eighteenthReversion': None,
        'nineteenthReversion': None,
        'twentiethReversion': None,
    },
}

# One active tier (firstReversion). Note firstReversion carries NO 'reversionTiedTo' key at all
# (a genuine absence) -- see ownership_reversion._REVERSION_TIED_TO_CSV_DEFAULT.
SAMPLE_REVERSION_A_W_PO: Dict[str, Any] = {
    'id': '000000000000000000000014',
    'name': 'Sample Reversion A w PO',
    'unique': False,
    'createdAt': '2024-11-05T17:02:50.960Z',
    'updatedAt': '2024-11-05T17:02:50.960Z',
    'econModelType': 'OwnershipReversion',
    'ownership': {
        'initialOwnership': {
            'workingInterest': 0,
            'netProfitInterestType': 'expense',
            'netProfitInterest': 0,
            'netRevenueInterest': 0,
            'leaseNetRevenueInterest': 75.00140853,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
        },
        'firstReversion': {
            'reversionType': 'PayoutWithoutInvestment',
            'reversionValue': 12290000,
            'balance': 'gross',
            'includeNetProfitInterest': 'yes',
            'workingInterest': 0.177749,
            'netRevenueInterest': 0.132697,
            'leaseNetRevenueInterest': 75.00140853,
            'netProfitInterest': 0,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
        },
        **{
            f'{o}Reversion': None
            for o in (
                'second',
                'third',
                'fourth',
                'fifth',
                'sixth',
                'seventh',
                'eighth',
                'ninth',
                'tenth',
                'eleventh',
                'twelfth',
                'thirteenth',
                'fourteenth',
                'fifteenth',
                'sixteenth',
                'seventeenth',
                'eighteenth',
                'nineteenth',
                'twentieth',
            )
        },
    },
}

# One active tier, but here 'reversionTiedTo' IS explicit ({"type": "as_of"}) -- unlike
# SAMPLE_REVERSION_A_W_PO above.
SAMPLE_WELL_2: Dict[str, Any] = {
    'id': '000000000000000000000015',
    'name': 'Sample Well 2 - PO 100%',
    'unique': False,
    'createdAt': '2024-11-05T17:02:51.021Z',
    'updatedAt': '2024-11-05T17:02:51.021Z',
    'econModelType': 'OwnershipReversion',
    'ownership': {
        'initialOwnership': {
            'workingInterest': 0,
            'netProfitInterestType': 'expense',
            'netProfitInterest': 0,
            'netRevenueInterest': 0,
            'leaseNetRevenueInterest': 75.2085885,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
        },
        'firstReversion': {
            'reversionType': 'PayoutWithoutInvestment',
            'reversionValue': 11540170,
            'balance': 'gross',
            'includeNetProfitInterest': 'yes',
            'workingInterest': 3.237211,
            'netRevenueInterest': 2.4346607,
            'leaseNetRevenueInterest': 75.2085885,
            'netProfitInterest': 0,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
            'reversionTiedTo': {'type': 'as_of'},
        },
        **{
            f'{o}Reversion': None
            for o in (
                'second',
                'third',
                'fourth',
                'fifth',
                'sixth',
                'seventh',
                'eighth',
                'ninth',
                'tenth',
                'eleventh',
                'twelfth',
                'thirteenth',
                'fourteenth',
                'fifteenth',
                'sixteenth',
                'seventeenth',
                'eighteenth',
                'nineteenth',
                'twentieth',
            )
        },
    },
}


# A `PayoutWithInvestment` firstReversion tier -- previously raised `NotImplementedError`. Also
# exercises a `reversionTiedTo` WITH a `value` (`{"type": "date", "value": "2021-10-01"}`), fully
# distinct from the tier's own dollar-amount `reversionValue`.
PAYOUT_WITH_INVESTMENT: Dict[str, Any] = {
    'id': '000000000000000000000006',
    'name': 'sample-model-0001',
    'unique': True,
    'createdAt': '2022-01-04T18:55:49.870Z',
    'updatedAt': '2023-03-02T18:09:03.997Z',
    'econModelType': 'OwnershipReversion',
    'ownership': {
        'initialOwnership': {
            'workingInterest': 15,
            'netProfitInterestType': 'expense',
            'netProfitInterest': 0,
            'netRevenueInterest': 11.352571,
            'leaseNetRevenueInterest': 75.6838067,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
        },
        'firstReversion': {
            'reversionType': 'PayoutWithInvestment',
            'reversionValue': 28588998.75,
            'balance': 'gross',
            'includeNetProfitInterest': 'yes',
            'workingInterest': 8.05018875,
            'netRevenueInterest': 6.037641563,
            'leaseNetRevenueInterest': 75,
            'netProfitInterest': 0,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
            'reversionTiedTo': {'type': 'date', 'value': '2021-10-01'},
        },
        **{
            f'{o}Reversion': None
            for o in (
                'second',
                'third',
                'fourth',
                'fifth',
                'sixth',
                'seventh',
                'eighth',
                'ninth',
                'tenth',
                'eleventh',
                'twelfth',
                'thirteenth',
                'fourteenth',
                'fifteenth',
                'sixteenth',
                'seventeenth',
                'eighteenth',
                'nineteenth',
                'twentieth',
            )
        },
    },
}

# A `Date` firstReversion tier -- `reversionValue` is a plain ISO date STRING ('2022-09-01'), not
# a number (previously raised a `ReversionTierData` `ValidationError`). Also: `balance`/
# `includeNetProfitInterest` are the empty string (not null/absent), and `reversionTiedTo`
# carries `{"type": "date", "value": "2023-09-01"}` -- a DIFFERENT date than the tier's own
# `reversionValue`.
DATE_TYPE_REVERSION: Dict[str, Any] = {
    'id': '000000000000000000000005',
    'name': 'sample-model-0002',
    'unique': True,
    'createdAt': '2022-01-04T18:54:40.940Z',
    'updatedAt': '2024-02-13T18:42:20.532Z',
    'econModelType': 'OwnershipReversion',
    'ownership': {
        'initialOwnership': {
            'workingInterest': 25,
            'netProfitInterestType': 'expense',
            'netProfitInterest': 0,
            'netRevenueInterest': 18.75,
            'leaseNetRevenueInterest': 75,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
        },
        'firstReversion': {
            'reversionType': 'Date',
            'reversionValue': '2022-09-01',
            'balance': '',
            'includeNetProfitInterest': '',
            'workingInterest': 23.25,
            'netRevenueInterest': 17.4375,
            'leaseNetRevenueInterest': 75,
            'netProfitInterest': 0,
            'oilNetRevenueInterest': None,
            'gasNetRevenueInterest': None,
            'nglNetRevenueInterest': None,
            'dripCondensateNetRevenueInterest': None,
            'reversionTiedTo': {'type': 'date', 'value': '2023-09-01'},
        },
        **{
            f'{o}Reversion': None
            for o in (
                'second',
                'third',
                'fourth',
                'fifth',
                'sixth',
                'seventh',
                'eighth',
                'ninth',
                'tenth',
                'eleventh',
                'twelfth',
                'thirteenth',
                'fourteenth',
                'fifteenth',
                'sixteenth',
                'seventeenth',
                'eighteenth',
                'nineteenth',
                'twentieth',
            )
        },
    },
}


def test_to_row_dicts_initial_only_emits_one_row() -> None:
    rows = OwnershipReversionMapper().to_row_dicts(EIGHT_EIGHTHS)
    assert len(rows) == 1


def test_to_row_dicts_initial_only_forward_shape() -> None:
    row = OwnershipReversionMapper().to_row_dicts(EIGHT_EIGHTHS)[0]
    assert row['Key'] == 'initial'
    assert row['WI %'] == '100'
    assert row['NRI %'] == '75'
    assert row['Lease NRI %'] == '75'
    assert row['NPI Type'] == 'expense'
    assert row['NPI %'] == '0'
    for col in ('Oil NRI %', 'Gas NRI %', 'NGL NRI %', 'Drip Cond. NRI %'):
        assert row[col] == ''
    for col in (
        'Reversion Type',
        'Reversion Value',
        'Reversion Tied To',
        'Balance',
        'Include NPI',
        'Rev Basis WI %',
        'Rev Basis NRI %',
    ):
        assert row[col] == ''
    assert row['Model Name'] == '8/8ths'
    assert row['Model Type'] == 'project'


def test_to_row_dicts_with_reversion_emits_two_rows() -> None:
    rows = OwnershipReversionMapper().to_row_dicts(SAMPLE_REVERSION_A_W_PO)
    assert len(rows) == 2
    assert [r['Key'] for r in rows] == ['initial', 'first']


def test_to_row_dicts_reversion_row_forward_shape() -> None:
    rows = OwnershipReversionMapper().to_row_dicts(SAMPLE_REVERSION_A_W_PO)
    reversion_row = rows[1]
    assert reversion_row['Reversion Type'] == 'po'
    assert reversion_row['Reversion Value'] == '12290000'
    assert reversion_row['WI %'] == '0.177749'
    assert reversion_row['NRI %'] == '0.132697'
    assert reversion_row['Lease NRI %'] == '75.00140853'
    assert reversion_row['Balance'] == 'gross'
    assert reversion_row['Include NPI'] == 'yes'
    assert reversion_row['NPI Type'] == ''
    assert reversion_row['NPI %'] == '0'
    # 'reversionTiedTo' is an ABSENCE on this model's firstReversion, yet CC's CSV still renders
    # 'as of' -- the documented display-default fallback.
    assert reversion_row['Reversion Tied To'] == 'as of'
    for col in ('Oil NRI %', 'Gas NRI %', 'NGL NRI %', 'Drip Cond. NRI %', 'Rev Basis WI %', 'Rev Basis NRI %'):
        assert reversion_row[col] == ''


def test_to_row_dicts_reversion_tied_to_explicit_renders_same_as_absent() -> None:
    # SAMPLE_WELL_2 carries an EXPLICIT reversionTiedTo={'type': 'as_of'} (unlike
    # SAMPLE_REVERSION_A_W_PO's absence) -- both render the identical CSV cell.
    rows = OwnershipReversionMapper().to_row_dicts(SAMPLE_WELL_2)
    assert rows[1]['Reversion Tied To'] == 'as of'


def test_roundtrip_exact_initial_only() -> None:
    m = OwnershipReversionMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(EIGHT_EIGHTHS))
    assert rebuilt['name'] == EIGHT_EIGHTHS['name']
    assert rebuilt['unique'] == EIGHT_EIGHTHS['unique']
    assert rebuilt['ownership'] == EIGHT_EIGHTHS['ownership']


def test_roundtrip_null_reversions_stay_null() -> None:
    m = OwnershipReversionMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(EIGHT_EIGHTHS))
    ownership = rebuilt['ownership']
    for ordinal in (
        'first',
        'second',
        'third',
        'fourth',
        'fifth',
        'sixth',
        'seventh',
        'eighth',
        'ninth',
        'tenth',
        'eleventh',
        'twelfth',
        'thirteenth',
        'fourteenth',
        'fifteenth',
        'sixteenth',
        'seventeenth',
        'eighteenth',
        'nineteenth',
        'twentieth',
    ):
        assert ownership[f'{ordinal}Reversion'] is None


def test_roundtrip_exact_with_reversion() -> None:
    m = OwnershipReversionMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(SAMPLE_WELL_2))
    assert rebuilt['name'] == SAMPLE_WELL_2['name']
    assert rebuilt['unique'] == SAMPLE_WELL_2['unique']
    assert rebuilt['ownership'] == SAMPLE_WELL_2['ownership']


def test_roundtrip_reversion_tied_to_absent_reconstructs_as_explicit() -> None:
    # Documented residual: the CSV cannot distinguish an absence of 'reversionTiedTo'
    # (SAMPLE_REVERSION_A_W_PO) from an explicit {"type": "as_of"} (SAMPLE_WELL_2) --
    # from_row_dicts always reconstructs the explicit form.
    m = OwnershipReversionMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(SAMPLE_REVERSION_A_W_PO))
    assert rebuilt['ownership']['firstReversion']['reversionTiedTo'] == {'type': 'as_of'}
    assert 'reversionTiedTo' not in SAMPLE_REVERSION_A_W_PO['ownership']['firstReversion']


def test_reversion_tied_to_fpd_round_trips() -> None:
    # reversionTiedTo {'type': 'fpd'} (reverts at first production date; no value) renders the
    # literal 'fpd' cell and round-trips losslessly -- distinct from 'as of' and a formatted date.
    model = copy.deepcopy(SAMPLE_WELL_2)
    model['ownership']['firstReversion']['reversionTiedTo'] = {'type': 'fpd'}
    m = OwnershipReversionMapper()
    rows = m.to_row_dicts(model)
    assert rows[1]['Reversion Tied To'] == 'fpd'
    rebuilt = m.from_row_dicts(rows)
    assert rebuilt['ownership']['firstReversion']['reversionTiedTo'] == {'type': 'fpd'}
    assert rebuilt['ownership'] == model['ownership']


def test_to_row_dicts_payout_with_investment_forward_shape() -> None:
    rows = OwnershipReversionMapper().to_row_dicts(PAYOUT_WITH_INVESTMENT)
    reversion_row = rows[1]
    assert reversion_row['Reversion Type'] == 'poi'
    assert reversion_row['Reversion Value'] == '28588998.75'
    assert reversion_row['WI %'] == '8.05018875'
    assert reversion_row['NRI %'] == '6.037641563'
    assert reversion_row['Balance'] == 'gross'
    assert reversion_row['Include NPI'] == 'yes'
    # reversionTiedTo={'type': 'date', 'value': '2021-10-01'} -- distinct from the tier's
    # own dollar-amount reversionValue -- renders as the formatted tied-to date.
    assert reversion_row['Reversion Tied To'] == '10/01/2021'


def test_roundtrip_exact_payout_with_investment() -> None:
    m = OwnershipReversionMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(PAYOUT_WITH_INVESTMENT))
    assert rebuilt['ownership'] == PAYOUT_WITH_INVESTMENT['ownership']


def test_to_row_dicts_date_type_forward_shape() -> None:
    rows = OwnershipReversionMapper().to_row_dicts(DATE_TYPE_REVERSION)
    reversion_row = rows[1]
    assert reversion_row['Reversion Type'] == 'date'
    # reversionValue '2022-09-01' (ISO) -> 'Reversion Value' MM/DD/YYYY.
    assert reversion_row['Reversion Value'] == '09/01/2022'
    assert reversion_row['WI %'] == '23.25'
    assert reversion_row['NRI %'] == '17.4375'
    # balance/includeNetProfitInterest are '' (not null/absent) for a 'Date' tier, where neither
    # concept applies.
    assert reversion_row['Balance'] == ''
    assert reversion_row['Include NPI'] == ''
    # reversionTiedTo={'type': 'date', 'value': '2023-09-01'} -- a DIFFERENT date than the
    # tier's own reversionValue ('2022-09-01') -- renders as ITS OWN formatted date.
    assert reversion_row['Reversion Tied To'] == '09/01/2023'


def test_roundtrip_exact_date_type() -> None:
    m = OwnershipReversionMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(DATE_TYPE_REVERSION))
    assert rebuilt['ownership'] == DATE_TYPE_REVERSION['ownership']


def test_unknown_reversion_type_raises() -> None:
    model: Dict[str, Any] = {
        'name': 'Bad',
        'unique': False,
        'ownership': {
            'initialOwnership': {
                'workingInterest': 100,
                'netRevenueInterest': 75,
                'leaseNetRevenueInterest': 75,
            },
            'firstReversion': {
                'reversionType': 'SomeUnverifiedType',
                'reversionValue': 1,
                'workingInterest': 50,
                'netRevenueInterest': 37.5,
                'leaseNetRevenueInterest': 75,
            },
        },
    }
    with pytest.raises(NotImplementedError):
        OwnershipReversionMapper().to_row_dicts(model)


def test_rev_basis_columns_populated_raises_on_inverse() -> None:
    m = OwnershipReversionMapper()
    rows = m.to_row_dicts(EIGHT_EIGHTHS)
    rows[0]['Rev Basis WI %'] = '50'
    with pytest.raises(NotImplementedError):
        m.from_row_dicts(rows)


def test_registry_get_mapper() -> None:
    mapper = get_mapper('OwnershipReversion')
    assert isinstance(mapper, OwnershipReversionMapper)
    assert mapper is MAPPERS['OwnershipReversion']
    assert mapper.econ_model_type == 'OwnershipReversion'
