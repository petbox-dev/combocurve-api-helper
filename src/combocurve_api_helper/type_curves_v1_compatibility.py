"""Deprecated v1 type-curve behavior kept on the v2 routes for transition (filled in Task 7)."""

from collections.abc import Mapping
from types import MappingProxyType

# Representative wells carry no timestamps; name then well id. The id key is `wellId`, not `id`.
_REP_WELL_SORT_ORDER: Mapping[str, int] = MappingProxyType({'wellName': 0, 'wellId': 1})
