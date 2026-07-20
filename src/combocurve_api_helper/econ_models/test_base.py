from typing import Any, Dict

from combocurve_api_helper.econ_models.csv_columns import COLUMNS
from combocurve_api_helper.econ_models.base import Context, common_columns


def test_columns_have_all_types_and_lead_with_common() -> None:
    assert set(COLUMNS) == {
        'StreamProperties',
        'Differentials',
        'ProductionTaxes',
        'Expenses',
        'Capex',
        'ReservesCategory',
        'Pricing',
        'DateSettings',
        'OwnershipReversion',
        'ActualOrForecast',
        'Risking',
    }
    for cols in COLUMNS.values():
        assert cols[:7] == [
            'Model Id',
            'Created At',
            'Project Name',
            'Model Type',
            'Model Name',
            'New Name',
            'Embedded Lookup Table',
        ]
        assert cols[-1] == 'Last Update'


def test_common_columns_with_context() -> None:
    m: Dict[str, Any] = {
        'id': 'x1',
        'name': 'M',
        'unique': False,
        'createdAt': '2026-05-08T14:18:05.000Z',
        'updatedAt': '2026-05-08T14:18:05.000Z',
    }
    ctx = Context(id='x1', created_at=m['createdAt'], project_name='ProjA')
    c = common_columns(m, ctx)
    assert c['Model Id'] == 'x1'
    assert c['Project Name'] == 'ProjA'
    assert c['Model Type'] == 'project'
    assert c['Model Name'] == 'M'
    assert c['New Name'] == '' and c['Embedded Lookup Table'] == ''
    assert c['Last Update'] == '05/08/2026 14:18:05'


def test_common_columns_without_context_omits_pipeline_cols() -> None:
    m: Dict[str, Any] = {
        'id': 'x1',
        'name': 'M',
        'unique': True,
        'createdAt': '2026-05-08T14:18:05.000Z',
        'updatedAt': '2026-05-08T14:18:05.000Z',
    }
    c = common_columns(m, None)
    assert 'Model Id' not in c and 'Project Name' not in c
    assert c['Model Type'] == 'unique'
