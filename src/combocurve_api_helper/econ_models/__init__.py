from typing import Dict

from .actual_or_forecast import ActualOrForecastMapper
from .base import Context, EconModelMapper
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

MAPPERS: Dict[str, EconModelMapper] = {
    m.econ_model_type: m
    for m in (
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
    try:
        return MAPPERS[econ_model_type]
    except KeyError:
        raise KeyError(f'No econ model mapper registered for econModelType: {econ_model_type!r}') from None


__all__ = [
    'Context',
    'EconModelMapper',
    'MAPPERS',
    'get_mapper',
    'StreamPropertiesMapper',
    'DifferentialsMapper',
    'ProductionTaxesMapper',
    'ExpensesMapper',
    'CapexMapper',
    'ReservesCategoryMapper',
    'PricingMapper',
    'DateSettingsMapper',
    'OwnershipReversionMapper',
    'ActualOrForecastMapper',
    'RiskingMapper',
]
