from typing import Any, Dict

import pytest

from combocurve_api_helper.econ_models import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.base import Context
from combocurve_api_helper.econ_models.reserves_category import ReservesCategoryMapper

# Real, FULL API shape: the nested 'reservesCategory' object is the entire model
# payload -- no rows[], no criteria.
NON_PRODUCING: Dict[str, Any] = {
    'id': 'rc-non-producing',
    'name': 'Reserves, Proved, Non Producing',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'ReservesCategory',
    'reservesCategory': {
        'prmsClass': 'reserves',
        'prmsCategory': 'proved',
        'prmsSubCategory': 'non_producing',
    },
}


def test_to_row_dicts_emits_exactly_one_row() -> None:
    rows = ReservesCategoryMapper().to_row_dicts(NON_PRODUCING)
    assert len(rows) == 1


def test_to_row_dicts_forward_passthrough() -> None:
    rows = ReservesCategoryMapper().to_row_dicts(NON_PRODUCING)
    row = rows[0]
    assert row['PRMS Class'] == 'reserves'
    assert row['PRMS Category'] == 'proved'
    # Underscore is passed through UNCHANGED -- no underscore->space transform, unlike
    # ProductionTaxes' Rate Type/Rate Rows Calculation Method columns.
    assert row['PRMS Sub Category'] == 'non_producing'
    assert row['Model Type'] == 'project'
    assert row['Model Name'] == 'Reserves, Proved, Non Producing'


def test_to_row_dicts_includes_common_columns_with_context() -> None:
    ctx = Context(id='rc-non-producing', created_at=NON_PRODUCING['createdAt'], project_name='Sample Project A')
    row = ReservesCategoryMapper().to_row_dicts(NON_PRODUCING, context=ctx)[0]
    assert row['Model Id'] == 'rc-non-producing'
    assert row['Project Name'] == 'Sample Project A'
    assert row['New Name'] == ''
    assert row['Embedded Lookup Table'] == ''
    assert row['Last Update'] == '05/10/2026 03:11:41'


def test_to_row_dicts_unique_model_type() -> None:
    model = dict(NON_PRODUCING, unique=True)
    row = ReservesCategoryMapper().to_row_dicts(model)[0]
    assert row['Model Type'] == 'unique'


@pytest.mark.parametrize(
    'prms_class, prms_category, prms_sub_category',
    [
        ('reserves', 'proved', 'producing'),
        ('reserves', 'proved', 'non_producing'),
        ('contingent', 'possible', 'undeveloped'),
        ('prospective', 'probable', 'undeveloped'),
    ],
)
def test_to_row_dicts_passthrough_all_verified_ground_truth_values(
    prms_class: str, prms_category: str, prms_sub_category: str
) -> None:
    model: Dict[str, Any] = {
        'name': 'X',
        'unique': False,
        'reservesCategory': {
            'prmsClass': prms_class,
            'prmsCategory': prms_category,
            'prmsSubCategory': prms_sub_category,
        },
    }
    row = ReservesCategoryMapper().to_row_dicts(model)[0]
    assert row['PRMS Class'] == prms_class
    assert row['PRMS Category'] == prms_category
    assert row['PRMS Sub Category'] == prms_sub_category


def test_roundtrip_exact() -> None:
    m = ReservesCategoryMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(NON_PRODUCING))
    assert set(rebuilt) == {'name', 'unique', 'reservesCategory'}
    assert rebuilt == {
        'name': NON_PRODUCING['name'],
        'unique': NON_PRODUCING['unique'],
        'reservesCategory': NON_PRODUCING['reservesCategory'],
    }


def test_roundtrip_exact_unique_model() -> None:
    model = dict(NON_PRODUCING, unique=True)
    m = ReservesCategoryMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(model))
    assert rebuilt['unique'] is True
    assert rebuilt['reservesCategory'] == model['reservesCategory']


def test_from_row_dicts_requires_exactly_one_row() -> None:
    m = ReservesCategoryMapper()
    with pytest.raises(NotImplementedError):
        m.from_row_dicts([])

    row = m.to_row_dicts(NON_PRODUCING)[0]
    with pytest.raises(NotImplementedError):
        m.from_row_dicts([row, dict(row)])


def test_registry_get_mapper() -> None:
    mapper = get_mapper('ReservesCategory')
    assert isinstance(mapper, ReservesCategoryMapper)
    assert mapper is MAPPERS['ReservesCategory']
    assert mapper.econ_model_type == 'ReservesCategory'
