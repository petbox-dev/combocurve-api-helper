import os
from pathlib import Path

import pytest

from combocurve_api_helper import ComboCurveAPI

CONFIG_PATH = Path.home() / '.combocurve/dev'

# Live test: hits the real CC API and needs local dev creds. Skipped unless
# CC_LIVE_TEST=1 and ~/.combocurve/dev creds are present, so CI and other
# machines are unaffected (matches test_assignments_live.py).
pytestmark = pytest.mark.skipif(
    not os.environ.get('CC_LIVE_TEST')
    or not (CONFIG_PATH / 'combocurve.json').exists()
    or not (CONFIG_PATH / 'cc-api.config.json').exists(),
    reason='requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials',
)


@pytest.fixture
def api() -> ComboCurveAPI:
    api = ComboCurveAPI.from_alternate_config(
        combocurve_json_path=CONFIG_PATH / 'combocurve.json', cc_api_config_json_path=CONFIG_PATH / 'cc-api.config.json'
    )

    return api


class TestRoot:
    def test_custom_columns(self, api: ComboCurveAPI) -> None:
        result = api.get_custom_columns('wells')
        assert isinstance(result, dict)

    def test_project_custom_columns(self, api: ComboCurveAPI) -> None:
        # `custom_column='headers'` is the only value the live API accepts (verified
        # 2026-09-06: every other value, including the collection names 'wells' /
        # 'daily-productions' that `get_custom_columns` takes, 404s with
        # CustomColumnHeaderNotFoundError). The response is a list -- 0 entries for a
        # project with no custom headers, one per header for a project that has them.
        # No default id: this repo is public, so the dev project id comes from the environment.
        project_id = os.environ.get('CC_DEV_PROJECT_ID')
        if not project_id:
            pytest.skip('requires CC_DEV_PROJECT_ID')
        result = api.get_project_custom_columns(project_id, 'headers')
        assert isinstance(result, list)
        for header in result:
            assert {'headerName', 'headerLabel', 'headerType'} <= header.keys()
