import pytest
from pathlib import Path

from combocurve_api_helper import ComboCurveAPI


@pytest.fixture
def api() -> ComboCurveAPI:
    CONFIG_PATH = Path.home() / '.combocurve/dev'
    api = ComboCurveAPI.from_alternate_config(
        combocurve_json_path=CONFIG_PATH / 'combocurve.json',
        cc_api_config_json_path=CONFIG_PATH / 'cc_api_config.json')

    return api


class TestRoot:
    def test_custom_columns(self, api: ComboCurveAPI) -> None:
        result = api.get_custom_columns()
