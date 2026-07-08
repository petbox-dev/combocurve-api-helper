import subprocess
import sys
import pathlib
import inspect

from combocurve_api_helper import config
from combocurve_api_helper._models_generated import _GeneratedModelMethods

# Test file lives at <repo>/src/combocurve_api_helper/test_generated_models.py, so
# the repo root -- which holds scripts/ -- is parents[2], not parents[3] (the
# value in the brief was off by one for this layout).
REPO = pathlib.Path(__file__).resolve().parents[2]
GEN = REPO / 'scripts' / 'generate_model_methods.py'
OUT = pathlib.Path(__file__).with_name('_models_generated.py')


def _expected_method_names() -> set[str]:
    names: set[str] = set()
    for m in config.ECON_MODELS:
        b = m['methodBase']
        if m['hasCrud']:
            names |= {f'get_{b}_models', f'get_{b}_models_url', f'get_{b}_model_by_id', f'get_{b}_model_by_id_url'}
        if m['assignable']:
            names |= {
                f'get_{b}_assignments_by_id',
                f'get_{b}_assignments_by_id_url',
                f'post_{b}_assignments_by_id',
                f'put_{b}_assignments_by_id',
                f'delete_{b}_assignments_by_id',
            }
    return names


def _generated_method_names() -> set[str]:
    # Only the methods defined *on* the generated class -- not the generic
    # delegates inherited from _EconModelMethodsBase/APIBase, which dir() would
    # also surface.
    return {n for n in vars(_GeneratedModelMethods) if not n.startswith('_')}


def test_generated_method_set_matches_config() -> None:
    assert _generated_method_names() == _expected_method_names()


def test_forecast_and_null_route_types_have_no_methods() -> None:
    # Null-route econ-model types (Forecast, Network, PSeries, Schedule) must
    # generate no methods. A name like get_actual_forecast_models is legitimate
    # (methodBase "actual_forecast"), so a bare substring check on "forecast"
    # would false-positive -- match the leading base segment after the verb.
    verbs = ('get_', 'post_', 'put_', 'delete_')
    null_route_bases = {str(m['econModelType']).lower() for m in config.ECON_MODELS if m['route'] is None}
    for name in _generated_method_names():
        base = name
        for v in verbs:
            if base.startswith(v):
                base = base[len(v) :]
                break
        assert not any(base.startswith(token) for token in null_route_bases), (
            f'generated method {name!r} matches a null-route econ-model type'
        )


def test_generated_file_is_current() -> None:
    fresh = subprocess.run([sys.executable, str(GEN), '--stdout'], capture_output=True, text=True, check=True).stdout
    assert fresh == OUT.read_text(encoding='utf-8'), 'Re-run scripts/generate_model_methods.py and commit.'


def test_no_handwritten_per_type_methods_remain() -> None:
    from combocurve_api_helper import models

    src = inspect.getsource(models)
    for bad in (
        'def get_capex_models',
        'def get_differential_models',
        'def get_reserves_categories_by_id',
        'def get_fluid_models_by_id_url',
    ):
        assert bad not in src, f'hand-written per-type method still in models.py: {bad}'
