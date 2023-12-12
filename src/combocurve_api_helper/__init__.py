__version__ = '1.0.5'

from .root import Root
from .projects import Projects
from .scenarios import Scenarios, VALID_ECON_MODEL_TYPES
from .econ_runs import EconRuns
from .wells import Wells
from .models import Models
from .forecasts import Forecasts
from .typecurves import TypeCurves
from .directional import Directional

from .base import Item, ItemList, PrimativeValue, IterableValue


class ComboCurveAPI(
    Root,
    Projects,
    Scenarios,
    EconRuns,
    Wells,
    Models,
    Forecasts,
    TypeCurves,
    Directional
):
    # all API calls should be made through this class
    pass
