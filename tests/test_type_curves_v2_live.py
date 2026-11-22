"""Type Curve 2.0 live round trip on the DEV tenant. WRITES: creates and deletes throwaway objects named
'API Helper Fixture *' in the dev project. Skips unless the dev live tests are enabled (CC_LIVE_TEST=1 and
~/.combocurve/dev credentials), CC_DEV_PROJECT_ID is set, and CC_DEV_TYPE_CURVE_ID names a type curve of that
project with fits on every phase, a normalization and at least 10 wells (it is read, never written).

Until 2026-11-21 this test ran on production, because the dev tenant was not enrolled in Type Curve 2.0; dev
answers the v2 routes since (checked 2026-11-22)."""

import os
import uuid
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

import pytest

from combocurve_api_helper import ComboCurveAPI, fits_for_put, normalization_for_put
from tests.live_support import FIXTURE_PREFIX, live_tests_enabled

if TYPE_CHECKING:
    from combocurve_api_helper.base import Item

PROJECT_ID = os.environ.get('CC_DEV_PROJECT_ID', '')
SOURCE_TYPE_CURVE_ID = os.environ.get('CC_DEV_TYPE_CURVE_ID', '')

pytestmark = pytest.mark.skipif(
    not live_tests_enabled() or not PROJECT_ID or not SOURCE_TYPE_CURVE_ID,
    reason='live Type Curve 2.0 test: needs CC_LIVE_TEST=1, ~/.combocurve/dev, CC_DEV_PROJECT_ID, CC_DEV_TYPE_CURVE_ID',
)


@pytest.fixture
def api(dev_api: ComboCurveAPI) -> ComboCurveAPI:
    """The session's dev client (`tests/conftest.py`): one OAuth token for every live test of the run."""
    return dev_api


@pytest.fixture
def throwaway_type_curve(api: ComboCurveAPI) -> Iterator[str]:
    source = api.get_type_curve_by_id(PROJECT_ID, SOURCE_TYPE_CURVE_ID)
    wells = list(cast('Any', source['wells']))[:10]
    created = api.post_type_curve(
        PROJECT_ID,
        {'name': f'{FIXTURE_PREFIX} {uuid.uuid4().hex[:8]}', 'forecast': source['forecast'], 'wells': wells},
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
        'name': f'{FIXTURE_PREFIX} Table {uuid.uuid4().hex[:8]}',
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
    headers = api.delete_type_curves(PROJECT_ID, name=f'{FIXTURE_PREFIX} Missing {uuid.uuid4().hex[:8]}')

    assert headers['X-Delete-Count'] == '0'
