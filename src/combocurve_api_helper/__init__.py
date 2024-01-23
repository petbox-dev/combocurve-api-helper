__version__ = '1.0.51'

from .root import Root
from .projects import Projects
from .scenarios import Scenarios
from .wells import Wells
from .models import Models
from .forecasts import Forecasts
from .typecurves import TypeCurves
from .directional import Directional

from .base import Item, ItemList

class ComboCurveAPI(Root, Projects, Scenarios, Wells, Models, Forecasts, TypeCurves, Directional):
    # all API calls should be made through this class
    pass
