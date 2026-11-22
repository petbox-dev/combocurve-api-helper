import os

import pytest

from combocurve_api_helper import ComboCurveAPI
from tests.live_support import LIVE_TEST_SKIP_REASON, live_tests_enabled

# Live test: hits the real CC API and needs local dev creds. Skipped unless
# CC_LIVE_TEST=1 and ~/.combocurve/dev holds an unzipped ComboCurve credential download
# (api-key.txt with api-credentials.json or api-service-account-key.json), so CI and
# other machines are unaffected. The client is the session's `dev_api` (tests/conftest.py).
pytestmark = pytest.mark.skipif(not live_tests_enabled(), reason=LIVE_TEST_SKIP_REASON)


class TestRoot:
    def test_custom_columns(self, dev_api: ComboCurveAPI) -> None:
        result = dev_api.get_custom_columns('wells')
        assert isinstance(result, dict)

    def test_project_custom_columns(self, dev_api: ComboCurveAPI) -> None:
        # `custom_column='headers'` is the only value the live API accepts (verified
        # 2026-09-06: every other value, including the collection names 'wells' /
        # 'daily-productions' that `get_custom_columns` takes, 404s with
        # CustomColumnHeaderNotFoundError). The response is a list -- 0 entries for a
        # project with no custom headers, one per header for a project that has them.
        # No default id: this repo is public, so the dev project id comes from the environment.
        project_id = os.environ.get('CC_DEV_PROJECT_ID')
        if not project_id:
            pytest.skip('requires CC_DEV_PROJECT_ID')
        result = dev_api.get_project_custom_columns(project_id, 'headers')
        assert isinstance(result, list)
        for header in result:
            assert {'headerName', 'headerLabel', 'headerType'} <= header.keys()
