import copy
import importlib.util
import pathlib
from types import ModuleType

from combocurve_api_helper.econ_models import MAPPERS, drift
from tests.econ_models.test_expenses import API as EXPENSES_API

# Test file lives at <repo>/tests/econ_models/test_drift.py, so the repo root --
# which holds scripts/ -- is parents[2].
_AUDIT_SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[2] / 'scripts' / 'audit_econ_model_drift.py'


def _load_audit_script() -> ModuleType:
    """Load `scripts/audit_econ_model_drift.py` as a module without adding `scripts/` to
    `sys.path` (it is outside `testpaths`). Safe to import: it only defines `ComboCurveAPI`
    usage inside `main()`, never instantiates it at module scope, so no live credentials
    are required."""
    spec = importlib.util.spec_from_file_location('audit_econ_model_drift', _AUDIT_SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_keys_recurses_dicts_and_lists() -> None:
    payload = {'a': 1, 'b': {'c': 2, 'd': [{'e': 3}, {'f': 4}]}}
    assert drift.collect_keys(payload) == frozenset({'a', 'b', 'c', 'd', 'e', 'f'})


def test_every_registered_type_has_a_baseline() -> None:
    """A mapper without a baseline entry would flag every key as drift; keep the baseline
    in lockstep with the registry so that can't happen silently."""
    assert set(drift._BASELINE_KEYS) == set(MAPPERS)


def test_audit_script_getters_cover_every_registered_mapper() -> None:
    """`scripts/audit_econ_model_drift.py`'s GETTERS table maps each econ-model type to
    the ComboCurveAPI getter used to fetch real models for the live drift audit. A type
    registered in MAPPERS but missing from GETTERS would be silently skipped by that
    audit; a stale GETTERS entry for a type no longer in MAPPERS would reference a getter
    for a mapper that no longer exists. Keep the two in lockstep."""
    audit_script = _load_audit_script()
    assert set(audit_script.GETTERS) == set(MAPPERS)


def test_no_drift_on_real_fixture() -> None:
    """The real Expenses fixture maps cleanly and uses only baseline keys."""
    assert drift.audit_model('Expenses', EXPENSES_API) is None


def test_key_drift_flags_unknown_nested_key() -> None:
    """A brand-new key CC adds deep in the payload is surfaced, not silently dropped."""
    model = copy.deepcopy(EXPENSES_API)
    model['variableExpenses']['oil']['gathering']['someBrandNewCcField'] = 1
    finding = drift.audit_model('Expenses', model)
    assert finding is not None
    assert 'someBrandNewCcField' in finding.unknown_keys


def test_envelope_keys_are_never_drift() -> None:
    model = copy.deepcopy(EXPENSES_API)
    model['tags'] = ['anything']
    assert drift.key_drift('Expenses', model) == []


def test_roundtrip_diff_matches_and_differs() -> None:
    """The pure round-trip comparison: identical param cells -> None; a changed param cell or
    a changed row count -> a description. Context/timestamp columns are ignored."""
    cols = ['Model Id', 'Model Name', 'Key', 'Value', 'Last Update']
    a = [{'Model Name': 'M', 'Key': 'oil', 'Value': '97', 'Model Id': 'x', 'Last Update': 't1'}]
    same_params = [{'Model Name': 'M', 'Key': 'oil', 'Value': '97', 'Model Id': 'DIFFERENT', 'Last Update': 't2'}]
    assert drift._roundtrip_diff(a, same_params, cols) is None  # context cols excluded
    changed = [{'Model Name': 'M', 'Key': 'oil', 'Value': '85'}]
    assert drift._roundtrip_diff(a, changed, cols) is not None  # Value changed
    assert drift._roundtrip_diff(a, a + a, cols) is not None  # row count changed


def test_roundtrip_drift_none_on_real_fixture() -> None:
    """The real Expenses fixture is CSV-idempotent (inverse reproduces the forward CSV)."""
    assert drift.roundtrip_drift('Expenses', EXPENSES_API) is None
    assert drift.audit_model('Expenses', EXPENSES_API) is None


def test_value_drift_flags_unmappable_model() -> None:
    """An unknown category the mapper cannot render is reported, not silently mapped."""
    bad = {
        'name': 'bad-ptax',
        'unique': False,
        'data': {
            'state': 'custom',
            'rows': [
                {
                    'key': 'oil',
                    'category': 'totally_unknown_category',
                    'criteria': 'entire_well_life',
                    'period': ['Flat'],
                    'value': [1.0],
                    'unit': 'pct_of_revenue',
                }
            ],
        },
    }
    err = drift.value_drift('ProductionTaxes', bad)
    assert err is not None
    assert 'totally_unknown_category' in err


def test_value_drift_none_on_clean_model() -> None:
    assert drift.value_drift('Expenses', EXPENSES_API) is None


def test_audit_models_returns_only_findings() -> None:
    dirty = copy.deepcopy(EXPENSES_API)
    dirty['variableExpenses']['oil']['gathering']['brandNewField'] = 1
    findings = drift.audit_models('Expenses', [EXPENSES_API, dirty])
    assert len(findings) == 1
    assert findings[0].model_name == dirty['name']
