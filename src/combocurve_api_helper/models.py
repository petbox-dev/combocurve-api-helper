from ._econ_model_base import _EconModelMethodsBase  # noqa: F401 (kept for clarity)
from ._models_generated import _GeneratedModelMethods


class Models(_GeneratedModelMethods):
    """
    Econ-model endpoints. Composes the generic, type-parameterized delegates
    (via `_EconModelMethodsBase`) with the generated per-type convenience
    methods (via `_GeneratedModelMethods`). All per-type methods are generated
    from `assets/econModels.json` by `scripts/generate_model_methods.py`; edit
    that data/generator rather than hand-writing methods here.
    """
    pass
