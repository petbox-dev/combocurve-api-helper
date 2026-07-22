"""Econ-model mapper registry: `MAPPERS` (econModelType -> mapper) and `get_mapper`.

Extracted from this subpackage's `__init__` so the generated `_csv_generated`
convenience functions can import `get_mapper` without an import cycle through the
package `__init__` (which itself imports the generated module).
"""

from typing import Dict

from .actual_or_forecast import ActualOrForecastMapper
from .base import EconModelMapper
from .capex import CapexMapper
from .date_settings import DateSettingsMapper
from .differentials import DifferentialsMapper
from .expenses import ExpensesMapper
from .ownership_reversion import OwnershipReversionMapper
from .pricing import PricingMapper
from .production_taxes import ProductionTaxesMapper
from .reserves_category import ReservesCategoryMapper
from .risking import RiskingMapper
from .stream_properties import StreamPropertiesMapper

# PascalCase econModelType (as in econModels.json) -> the singleton mapper for that type.
MAPPERS: Dict[str, EconModelMapper] = {
    mapper.econ_model_type: mapper
    for mapper in (
        StreamPropertiesMapper(),
        DifferentialsMapper(),
        ProductionTaxesMapper(),
        ExpensesMapper(),
        CapexMapper(),
        ReservesCategoryMapper(),
        PricingMapper(),
        DateSettingsMapper(),
        OwnershipReversionMapper(),
        ActualOrForecastMapper(),
        RiskingMapper(),
    )
}


def get_mapper(econ_model_type: str) -> EconModelMapper:
    """Return the mapper for a PascalCase `econModelType` (e.g. 'Capex', 'Dates').

    Raises `KeyError` if no mapper is registered for that type.
    """
    try:
        return MAPPERS[econ_model_type]
    except KeyError:
        raise KeyError(f'No econ model mapper registered for econModelType: {econ_model_type!r}') from None
