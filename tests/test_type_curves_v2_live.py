"""Type Curve 2.0 live round trip. WRITES: creates and deletes throwaway objects named
'API Helper Fixture *'. Skips unless CC_LIVE_TEST=1 and both CC_TC2_* ids are set."""

import os
import uuid
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

import pytest

from combocurve_api_helper import ComboCurveAPI, fits_for_put, normalization_for_put

if TYPE_CHECKING:
    from combocurve_api_helper.base import Item

PROJECT_ID = os.environ.get('CC_TC2_PROJECT_ID', '')
SOURCE_TYPE_CURVE_ID = os.environ.get('CC_TC2_TYPE_CURVE_ID', '')

pytestmark = pytest.mark.skipif(
    not os.environ.get('CC_LIVE_TEST') or not PROJECT_ID or not SOURCE_TYPE_CURVE_ID,
    reason='live Type Curve 2.0 test: needs CC_LIVE_TEST=1, CC_TC2_PROJECT_ID, CC_TC2_TYPE_CURVE_ID',
)


@pytest.fixture(scope='module')
def api() -> ComboCurveAPI:
    """One client for the module: one OAuth token (10 tokens per 15 minutes per client id)."""
    return ComboCurveAPI()


@pytest.fixture
def throwaway_type_curve(api: ComboCurveAPI) -> Iterator[str]:
    source = api.get_type_curve_by_id(PROJECT_ID, SOURCE_TYPE_CURVE_ID)
    wells = list(cast('Any', source['wells']))[:10]
    created = api.post_type_curve(
        PROJECT_ID,
        {'name': f'API Helper Fixture {uuid.uuid4().hex[:8]}', 'forecast': source['forecast'], 'wells': wells},
    )
    type_curve_id = str(created['id'])
    try:
        yield type_curve_id
    finally:
        api.delete_type_curves(PROJECT_ID, id=type_curve_id)


def test_fits_normalization_volumes_and_wells_round_trip(api: ComboCurveAPI, throwaway_type_curve: str) -> None:
    source_fits = api.get_type_curve_fits(PROJECT_ID, SOURCE_TYPE_CURVE_ID)
    api.put_type_curve_fits(PROJECT_ID, throwaway_type_curve, fits_for_put(source_fits))
    stored_fits = api.get_type_curve_fits(PROJECT_ID, throwaway_type_curve)
    for phase, fit in source_fits.items():
        assert cast('Any', stored_fits[phase])['best'] == cast('Any', fit)['best']

    source_normalization = api.get_type_curve_normalization(PROJECT_ID, SOURCE_TYPE_CURVE_ID)
    api.put_type_curve_normalization(PROJECT_ID, throwaway_type_curve, normalization_for_put(source_normalization))

    assert api.get_type_curve_volumes(PROJECT_ID, throwaway_type_curve, 'monthly')
    assert api.count_type_curve_wells(PROJECT_ID, throwaway_type_curve) == 10
    with pytest.warns(DeprecationWarning):
        rows = api.get_type_curve_representative_fits(PROJECT_ID, throwaway_type_curve)
    assert len(rows) == 10


def test_v1_shaped_lookup_table_is_translated(api: ComboCurveAPI, throwaway_type_curve: str) -> None:
    v1_table: Item = {
        'name': f'API Helper Fixture Table {uuid.uuid4().hex[:8]}',
        'rules': [
            {
                'filter': [{'key': 'state', 'operator': 'equal', 'value': 'TX'}],
                'typeCurve': throwaway_type_curve,
                'applySeries': 'best',
                'fpdSource': 'first_prod_date',
                'riskFactorOil': 1,
                'applyNormalization': True,
                'phase': 'oil',
            }
        ],
    }
    with pytest.warns(DeprecationWarning):
        stored = api.post_type_curve_lookup_table(PROJECT_ID, v1_table)
    try:
        rule = cast('Any', stored['rules'])[0]
        assert rule['riskFactorPeakOil'] == 1
        assert rule['normalization'] == {'source': 'own'}
    finally:
        api.delete_type_curve_lookup_table_by_id(PROJECT_ID, str(stored['id']))


def test_delete_with_no_match_reads_zero(api: ComboCurveAPI) -> None:
    headers = api.delete_type_curves(PROJECT_ID, name=f'API Helper Fixture Missing {uuid.uuid4().hex[:8]}')

    assert headers['X-Delete-Count'] == '0'
