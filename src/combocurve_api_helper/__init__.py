__version__ = '2.2.1'

from ._batch import BatchChunk as BatchChunk
from ._batch import BatchWriteResult as BatchWriteResult

# Explicit re-export (`as`) so downstream `mypy --strict`
# (--no-implicit-reexport) sees these public types as exported.
from .base import Item as Item
from .base import ItemList as ItemList
from .base import JsonValue as JsonValue
from .base import WriteError as WriteError
from .base import WriteResponse as WriteResponse
from .company_models import CompanyModels
from .directional import Directional
from .econ_runs import EconRuns
from .exports import Exports
from .forecast_configurations import ForecastConfigurations
from .forecast_parameters import FORECAST_PARAMETERS_COLUMNS as FORECAST_PARAMETERS_COLUMNS
from .forecast_parameters import ForecastParametersConverter as ForecastParametersConverter
from .forecast_parameters import forecast_parameters_to_csv as forecast_parameters_to_csv
from .forecast_parameters import forecast_parameters_to_row_dicts as forecast_parameters_to_row_dicts
from .forecast_parameters import write_forecast_parameters_csv as write_forecast_parameters_csv
from .forecasts import Forecasts
from .models import Models
from .ownership_qualifiers import OwnershipQualifiers
from .production import Production
from .projects import Projects
from .root import Root
from .scenarios import Scenarios
from .typecurves import TypeCurves
from .wells import Wells


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
