from typing import Any, Dict

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.base import Context
from combocurve_api_helper.econ_models.pricing import PricingMapper

# API shape: flat pricing on all four phases, `breakeven.basedOnPriceRatio` False (the
# 'direct' CSV case).
FLAT_MODEL: Dict[str, Any] = {
    'id': '000000000000000000000001',
    'name': '$70 / $2.50 Flat',
    'unique': False,
    'createdAt': '2021-07-12T17:33:14.607Z',
    'updatedAt': '2021-08-04T01:53:03.568Z',
    'econModelType': 'Pricing',
    'priceModel': {
        'oil': {'cap': None, 'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'price': 70}]},
        'gas': {'cap': None, 'escalationModel': 'none', 'rows': [{'dollarPerMmbtu': 2.5, 'entireWellLife': 'Flat'}]},
        'ngl': {'cap': None, 'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'pctOfOilPrice': 100}]},
        'dripCondensate': {
            'cap': None,
            'escalationModel': 'none',
            'rows': [{'entireWellLife': 'Flat', 'pctOfOilPrice': 100}],
        },
    },
    'breakeven': {'basedOnPriceRatio': False, 'npvDiscount': 0, 'priceRatio': None},
}

# API shape: dated oil/gas prices, flat ngl (% of oil price) AND flat dripCondensate
# priced DIRECTLY per bbl (`dollarPerBbl` -- NOT `price`, unlike oil), plus a 'based on
# price ratio' breakeven.
BREAKEVEN_RATIO_MODEL: Dict[str, Any] = {
    'id': '000000000000000000000012',
    'name': '23Q4 Avg Strip',
    'unique': False,
    'createdAt': '2024-02-19T16:53:50.832Z',
    'updatedAt': '2024-02-19T16:55:34.000Z',
    'econModelType': 'Pricing',
    'priceModel': {
        'oil': {
            'cap': None,
            'escalationModel': 'none',
            'rows': [
                {'dates': '2024-01-01', 'price': 75.68},
                {'dates': '2025-01-01', 'price': 71.58},
            ],
        },
        'gas': {
            'cap': None,
            'escalationModel': 'none',
            'rows': [
                {'dates': '2024-01-01', 'dollarPerMmbtu': 3.25},
                {'dates': '2025-01-01', 'dollarPerMmbtu': 3.9},
            ],
        },
        'ngl': {'cap': None, 'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'pctOfOilPrice': 100}]},
        'dripCondensate': {
            'cap': None,
            'escalationModel': 'none',
            'rows': [{'entireWellLife': 'Flat', 'dollarPerBbl': 100}],
        },
    },
    'breakeven': {'basedOnPriceRatio': True, 'npvDiscount': 15, 'priceRatio': 20},
}


def test_to_row_dicts_flat_model_values() -> None:
    rows = PricingMapper().to_row_dicts(FLAT_MODEL)
    assert len(rows) == 5

    oil = next(r for r in rows if r['Phase'] == 'oil')
    assert (oil['Criteria'], oil['Period'], oil['Value'], oil['Unit']) == ('flat', '', '70', '$/bbl')
    assert oil['Category'] == ''
    assert oil['Escalation'] == 'None'

    gas = next(r for r in rows if r['Phase'] == 'gas')
    assert (gas['Criteria'], gas['Value'], gas['Unit']) == ('flat', '2.5', '$/mmbtu')

    ngl = next(r for r in rows if r['Phase'] == 'ngl')
    assert (ngl['Value'], ngl['Unit']) == ('100', '% of oil price')

    drip = next(r for r in rows if r['Phase'] == 'drip cond')
    assert (drip['Value'], drip['Unit']) == ('100', '% of oil price')

    breakeven = next(r for r in rows if r['Phase'] == 'breakeven')
    assert (breakeven['Criteria'], breakeven['Value'], breakeven['Unit']) == ('direct', '0', 'npv discount %')
    assert breakeven['Price Ratio'] == ''
    assert breakeven['Escalation'] == ''
    assert breakeven['Category'] == ''


def test_to_row_dicts_breakeven_based_on_price_ratio() -> None:
    rows = PricingMapper().to_row_dicts(BREAKEVEN_RATIO_MODEL)
    breakeven = next(r for r in rows if r['Phase'] == 'breakeven')
    assert breakeven['Criteria'] == 'based on price ratio'
    assert breakeven['Value'] == '15'
    assert breakeven['Price Ratio'] == '20'
    assert breakeven['Unit'] == 'npv discount %'


def test_to_row_dicts_drip_condensate_dollar_per_bbl_not_confused_with_oil_price() -> None:
    """dripCondensate's direct-$/bbl row uses API key `dollarPerBbl`, distinct from
    oil's `price` -- both render CSV Unit '$/bbl', but must not collide."""
    rows = PricingMapper().to_row_dicts(BREAKEVEN_RATIO_MODEL)
    drip = next(r for r in rows if r['Phase'] == 'drip cond')
    assert (drip['Criteria'], drip['Value'], drip['Unit']) == ('flat', '100', '$/bbl')
    oil_rows = [r for r in rows if r['Phase'] == 'oil']
    assert all(r['Unit'] == '$/bbl' for r in oil_rows)


def test_to_row_dicts_dated_criteria() -> None:
    rows = PricingMapper().to_row_dicts(BREAKEVEN_RATIO_MODEL)
    oil = [r for r in rows if r['Phase'] == 'oil']
    assert [(r['Criteria'], r['Period'], r['Value']) for r in oil] == [
        ('dates', '01/01/2024', '75.68'),
        ('dates', '01/01/2025', '71.58'),
    ]


def test_roundtrip_flat_model_exact() -> None:
    m = PricingMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(FLAT_MODEL))
    assert rebuilt['priceModel'] == FLAT_MODEL['priceModel']
    assert rebuilt['breakeven'] == FLAT_MODEL['breakeven']
    assert rebuilt['name'] == FLAT_MODEL['name']
    assert rebuilt['unique'] is False


def test_roundtrip_breakeven_ratio_model_exact() -> None:
    m = PricingMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(BREAKEVEN_RATIO_MODEL))
    assert rebuilt['priceModel'] == BREAKEVEN_RATIO_MODEL['priceModel']
    assert rebuilt['breakeven'] == BREAKEVEN_RATIO_MODEL['breakeven']


def test_to_row_dicts_includes_common_columns_with_context() -> None:
    ctx = Context(id=FLAT_MODEL['id'], created_at=FLAT_MODEL['createdAt'], project_name='Sample Project A')
    row = PricingMapper().to_row_dicts(FLAT_MODEL, context=ctx)[0]
    assert row['Model Id'] == FLAT_MODEL['id']
    assert row['Project Name'] == 'Sample Project A'
    assert row['Last Update'] == '08/04/2021 01:53:03'


def test_gas_component_category_not_implemented() -> None:
    """CC's CSV export shows compositional gas-component rows (Category in
    c1/co2/n2/remaining), but the API (the list and single-model-by-id GET endpoints)
    exposes NO field anywhere in `priceModel.gas` to hold this data -- it cannot be
    reconstructed from a CSV row, so from_row_dicts fails loud rather than silently
    dropping it."""
    rows = PricingMapper().to_row_dicts(FLAT_MODEL)
    gas_row = next(r for r in rows if r['Phase'] == 'gas')
    bad_row = dict(gas_row, Category='c1')
    with pytest.raises(NotImplementedError):
        PricingMapper().from_row_dicts([bad_row])


def test_full_stream_category_accepted_as_plain_row_not_round_trippable() -> None:
    """'full_stream' is CC's display label for the plain (non-compositional) gas/ngl
    price -- the underlying API row is IDENTICAL in shape to the blank-Category case, so
    from_row_dicts accepts it as an equivalent plain row (numeric data preserved), but the
    label itself is a CSV-inherent, non-recoverable field: to_row_dicts always emits
    Category=''."""
    rows = PricingMapper().to_row_dicts(FLAT_MODEL)
    gas_row = next(r for r in rows if r['Phase'] == 'gas')
    fs_row = dict(gas_row, Category='full_stream')
    rebuilt = PricingMapper().from_row_dicts([fs_row])
    assert rebuilt['priceModel']['gas'] == FLAT_MODEL['priceModel']['gas']
    # Round-tripping back through to_row_dicts loses the 'full_stream' label -- it comes
    # back as '', not the original 'full_stream' (documented CSV-inherent limitation).
    re_rows = PricingMapper().to_row_dicts(rebuilt)
    assert re_rows[0]['Category'] == ''


def test_unknown_category_raises() -> None:
    rows = PricingMapper().to_row_dicts(FLAT_MODEL)
    gas_row = next(r for r in rows if r['Phase'] == 'gas')
    bad_row = dict(gas_row, Category='bogus')
    with pytest.raises(NotImplementedError):
        PricingMapper().from_row_dicts([bad_row])


def test_unique_model_type() -> None:
    model = dict(FLAT_MODEL, unique=True)
    row = PricingMapper().to_row_dicts(model)[0]
    assert row['Model Type'] == 'unique'


def test_registry_get_mapper() -> None:
    mapper = get_mapper('Pricing')
    assert isinstance(mapper, PricingMapper)
    assert mapper is MAPPERS['Pricing']
    assert mapper.econ_model_type == 'Pricing'
