"""Unit tests for econ-run wrappers that carry validation logic (no live API)."""

import pytest

from combocurve_api_helper import ComboCurveAPI


def test_monthly_econ_results_requires_columns() -> None:
    # The API rejects a monthly-econ-results request without `columns`
    # ("Columns are required"), so the wrapper validates before calling out.
    api = ComboCurveAPI()
    with pytest.raises(ValueError, match='columns is required'):
        api.get_econ_run_monthly_econ_result_by_id('P', 'S', 'R', [])
