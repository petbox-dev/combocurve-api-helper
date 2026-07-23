__version__ = '2.0.0'

from .root import Root
from .projects import Projects
from .scenarios import Scenarios
from .production import Production
from .econ_runs import EconRuns
from .wells import Wells
from .models import Models
from .company_models import CompanyModels
from .forecasts import Forecasts
from .typecurves import TypeCurves
from .directional import Directional
from .forecast_configurations import ForecastConfigurations
from .ownership_qualifiers import OwnershipQualifiers
from .exports import Exports

# Explicit re-export (`as`) so downstream `mypy --strict`
# (--no-implicit-reexport) sees these public types as exported.
from .base import Item as Item
from .base import ItemList as ItemList
from .base import JsonValue as JsonValue
from .base import WriteResponse as WriteResponse
from .base import WriteError as WriteError
from ._batch import BatchChunk as BatchChunk
from ._batch import BatchWriteResult as BatchWriteResult


class ComboCurveAPI(
    Root,
    Projects,
    Scenarios,
    Production,
    EconRuns,
    Wells,
    Models,
    CompanyModels,
    Forecasts,
    TypeCurves,
    Directional,
    ForecastConfigurations,
    OwnershipQualifiers,
    Exports,
):
    """
    This class is the primary interface for interacting with the Combo Curve
    API. It inherits all of the API endpoints from the other classes in this
    module. It is intended to be used as a single entrypoint for interacting
    with the ComboCurve API.
    """

    pass
