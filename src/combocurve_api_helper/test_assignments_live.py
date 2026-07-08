"""Live dev round-trip for econ-model assignment writes (skip-by-default).

Verifies the new write surface against a real dev project: PUT an assignment
(using a multi-word type -> PascalCase econName), read it back from the
scenario grid, DELETE it via the corrected query-filter route, confirm removal.
Self-cleaning: creates and removes a throwaway qualifier slot.

Skipped unless CC_LIVE_TEST=1 and ~/.combocurve/dev creds are present, so CI
and other machines are unaffected. Verified 2026-07 against dev "Test Project".
"""

from __future__ import annotations

import os
import pathlib
import time
from typing import Any

import pytest
import requests

from combocurve_api_helper import ComboCurveAPI

DEV = pathlib.Path.home() / ".combocurve" / "dev"

pytestmark = pytest.mark.skipif(
    not os.environ.get("CC_LIVE_TEST") or not (DEV / "combocurve.json").exists(),
    reason="requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials",
)

# Dev "Test Project" defaults; override via env for a different target.
PROJECT_ID = os.environ.get("CC_DEV_PROJECT_ID", "65568dbb4a8039d4e89a2f4b")
SCENARIO_ID = os.environ.get("CC_DEV_SCENARIO_ID", "65568dbf4a8039d4e89b5059")
DATES_MODEL_ID = os.environ.get("CC_DEV_DATES_MODEL_ID", "65568dbb4a8039d4e89a2f6b")


def _dev_api() -> ComboCurveAPI:
    return ComboCurveAPI.from_alternate_config(
        str(DEV / "combocurve.json"),
        str(DEV / "cc-api.config.json"),
    )


def _dates_assignments(api: ComboCurveAPI, well: str) -> list[Any]:
    # Grid rows are dynamic live JSON; treat as Any rather than fight the
    # deeply-typed ItemList union.
    grid: list[Any] = list(api.get_scenario_econ_model_assignments(PROJECT_ID, SCENARIO_ID))
    row: Any = next((w for w in grid if str(w.get("wellId")) == well), None)
    if row is None:
        return []
    dates: Any = next((a for a in row.get("assumptions", []) if a.get("model") == "dates"), None)
    return list(dates.get("assignments", [])) if dates else []


def test_dates_assignment_roundtrip() -> None:
    """PUT (multi-word econName) -> read -> query-filter DELETE -> read; self-cleaning."""
    api = _dev_api()
    grid = api.get_scenario_econ_model_assignments(PROJECT_ID, SCENARIO_ID)
    assert grid, "scenario has no wells"
    well = str(grid[0]["wellId"])
    qname = "zz_apitest_%d" % int(time.time())

    # throwaway qualifier slot in the `dates` column
    api.post_scenario_qualifiers(PROJECT_ID, SCENARIO_ID, [{"econModel": "dates", "name": qname}])
    try:
        # PUT: assign the multi-word `Dates` model to our slot for one well
        api.put_date_settings_assignments_by_id(
            PROJECT_ID,
            DATES_MODEL_ID,
            [{"scenario": SCENARIO_ID, "allWells": False, "qualifierName": qname, "wells": [well]}],
        )
        assigned = _dates_assignments(api, well)
        assert any(
            a.get("qualifierName") == qname and a.get("econModelId") == DATES_MODEL_ID
            for a in assigned
        ), "PUT assignment not found in the scenario grid"

        # DELETE via query filters (scenarioId + qualifierName + wells)
        api.delete_date_settings_assignments_by_id(
            PROJECT_ID,
            DATES_MODEL_ID,
            scenario_id=SCENARIO_ID,
            qualifier_name=qname,
            wells=well,
        )
        after = _dates_assignments(api, well)
        assert not any(a.get("qualifierName") == qname for a in after), "DELETE left the assignment"
    finally:
        # Remove the throwaway slot. NOTE: the helper's delete_scenario_qualifiers
        # sends `econName` (singular) and 400s; the route needs `econNames`
        # (plural), so clean up with a direct call here.
        requests.delete(
            "%s/projects/%s/scenarios/%s/qualifiers" % (api.API_BASE_URL, PROJECT_ID, SCENARIO_ID),
            headers=api.auth.get_auth_headers(),
            params={"econNames": "dates", "qualifierNames": qname},
        )
