import os
import pytest
from pathlib import Path

from combocurve_api_helper import ComboCurveAPI

CONFIG_PATH = Path.home() / '.combocurve/dev'

# Live test: hits the real CC API and needs local dev creds. Skipped unless
# CC_LIVE_TEST=1 and ~/.combocurve/dev creds are present, so CI and other
# machines are unaffected (matches test_assignments_live.py).
pytestmark = pytest.mark.skipif(
    not os.environ.get('CC_LIVE_TEST')
    or not (CONFIG_PATH / 'combocurve.json').exists()
    or not (CONFIG_PATH / 'cc_api_config.json').exists(),
    reason='requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials',
)


@pytest.fixture
def api() -> ComboCurveAPI:
    api = ComboCurveAPI.from_alternate_config(
        combocurve_json_path=CONFIG_PATH / 'combocurve.json', cc_api_config_json_path=CONFIG_PATH / 'cc_api_config.json'
    )

    return api


class TestRoot:
    def test_custom_columns(self, api: ComboCurveAPI) -> None:
        result = api.get_custom_columns('wells')
        assert isinstance(result, dict)
