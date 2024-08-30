__version__ = '1.1.4'

from .root import Root
from .projects import Projects
from .scenarios import Scenarios
from .production import Production
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
    Production,
    EconRuns,
    Wells,
    Models,
    Forecasts,
    TypeCurves,
    Directional
):
    """
    This class is the primary interface for interacting with the Combo Curve
    API. It inherits all of the API endpoints from the other classes in this
    module. It is intended to be used as a single entrypoint for interacting
    with the ComboCurve API.
    """
    pass
