import os
from pathlib import Path

import pytest

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.config import find_native_credentials_directory

CONFIG_PATH = Path.home() / '.combocurve/dev'

# Live test: hits the real CC API and needs local dev creds. Skipped unless
# CC_LIVE_TEST=1 and ~/.combocurve/dev holds an unzipped ComboCurve credential download
# (api-key.txt with api-credentials.json or api-service-account-key.json), so CI and
# other machines are unaffected (matches test_assignments_live.py).
pytestmark = pytest.mark.skipif(
    not os.environ.get('CC_LIVE_TEST') or find_native_credentials_directory(CONFIG_PATH) is None,
    reason='requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials',
)


@pytest.fixture
def api() -> ComboCurveAPI:
    return ComboCurveAPI.from_credentials_directory(CONFIG_PATH)


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
