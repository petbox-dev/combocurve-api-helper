from typing import Any

from combocurve_api_helper.econ_models.base import Context, common_columns, model_scope
from combocurve_api_helper.econ_models.csv_columns import COLUMNS


def test_columns_have_all_types_and_lead_with_common() -> None:
    assert set(COLUMNS) == {
        'StreamProperties',
        'Differentials',
        'ProductionTaxes',
        'Expenses',
        'Capex',
        'ReservesCategory',
        'Pricing',
        'Dates',
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
    m: dict[str, Any] = {
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


def test_common_columns_company_scope_stamps_company() -> None:
    m: dict[str, Any] = {'id': 'x1', 'name': 'M', 'unique': False, 'updatedAt': '2026-05-08T14:18:05.000Z'}
    ctx = Context(project_name='x', scope='company')
    assert common_columns(m, ctx)['Model Type'] == 'company'


def test_common_columns_company_scope_does_not_override_unique() -> None:
    # A `unique` model is 'unique' regardless of scope -- scope only names the shared-model home.
    m: dict[str, Any] = {'id': 'x1', 'name': 'M', 'unique': True, 'updatedAt': '2026-05-08T14:18:05.000Z'}
    ctx = Context(project_name='x', scope='company')
    assert common_columns(m, ctx)['Model Type'] == 'unique'


def test_common_columns_default_scope_is_project() -> None:
    m: dict[str, Any] = {'id': 'x1', 'name': 'M', 'unique': False, 'updatedAt': '2026-05-08T14:18:05.000Z'}
    assert common_columns(m, Context(project_name='x'))['Model Type'] == 'project'


def test_common_columns_without_context_omits_pipeline_cols() -> None:
    m: dict[str, Any] = {
        'id': 'x1',
        'name': 'M',
        'unique': True,
        'createdAt': '2026-05-08T14:18:05.000Z',
        'updatedAt': '2026-05-08T14:18:05.000Z',
    }
    c = common_columns(m, None)
    assert 'Model Id' not in c and 'Project Name' not in c
    assert c['Model Type'] == 'unique'


def test_model_scope_reads_company_from_model_type() -> None:
    """CC's export of a company-level model writes 'Model Type' 'company'
    (fixtures/stream_properties_company.csv). The API payload has no scope field, so the
    scope comes from the rows; 'project' and 'unique' are both project scope."""
    assert model_scope([{'Model Type': 'company'}]) == 'company'
    assert model_scope([{'Model Type': 'project'}]) == 'project'
    assert model_scope([{'Model Type': 'unique'}]) == 'project'
    assert model_scope([]) == 'project'
