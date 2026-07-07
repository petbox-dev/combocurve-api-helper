# Econ-model method codegen — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ~90 hand-written per-type econ-model methods with typed, generated methods driven by `econModels.json`, add the missing assignment-write surface, and normalize six irregular names.

**Architecture:** `econModels.json` (extended with `methodBase`/`hasCrud`/`assignable`) is the single source of truth. A committed generator script emits a typed mixin `_GeneratedModelMethods` (real source, `# DO NOT EDIT`). Generic delegate methods (existing GET + new POST/PUT/DELETE assignment primitives) live in a base the mixin extends; `Models` inherits the mixin. No runtime metaprogramming.

**Tech Stack:** Python 3, `combocurve_api_helper` (setuptools, src-layout), pytest (`testpaths=["src"]`, tests co-located as `src/combocurve_api_helper/test_*.py`), flake8 (max-line 120), mypy.

## Global Constraints

- flake8 max line length: **120**.
- mypy must pass (config in `pyproject.toml`).
- Tests live at `src/combocurve_api_helper/test_<name>.py`; run `pytest` from repo root.
- The install is **non-editable** — consumers (vdr) only see changes after rebuild + reinstall (final task).
- `methodBase` = `route.replace('-','_')` for every type **except `FluidModel` = `fluid`**.
- `assignable` types (16): actualOrForecast, capex, dates, depreciation, differentials, emission, escalation, expenses, fluidModel, operations, ownershipReversion, pricing, productionTaxes, reservesCategory, risking, streamProperties. **Not assignable:** generalOptions; null-route forecast/network/pSeries/schedule.
- Six method renames (no aliases): `get_differential_models`→`get_differentials_models`, `get_emission_models`→`get_emissions_models`, `get_expense_models`→`get_expenses_models`, `get_risking_models`→`get_riskings_models`, `get_fluid_models_by_id_url`→`get_fluid_model_by_id_url`, `get_reserves_categories_by_id`→`get_reserves_categories_model_by_id`.

---

### Task 1: Extend `econModels.json` with `methodBase`/`hasCrud`/`assignable`

**Files:**
- Modify: `src/combocurve_api_helper/assets/econModels.json`
- Test: `src/combocurve_api_helper/test_econ_models_config.py`

**Interfaces:**
- Produces: each JSON entry gains `methodBase: str|None`, `hasCrud: bool`, `assignable: bool`. `config.ECON_MODELS` (already `List[Dict[str,str]]`) now carries them.

- [ ] **Step 1: Write the failing test**

```python
# src/combocurve_api_helper/test_econ_models_config.py
from combocurve_api_helper import config

def test_every_entry_has_capability_fields() -> None:
    for m in config.ECON_MODELS:
        assert set(m) >= {"qualifier", "econModelType", "route", "methodBase", "hasCrud", "assignable"}
        assert m["hasCrud"] == (m["route"] is not None)
        if m["route"] is None:
            assert m["methodBase"] is None
            assert m["assignable"] is False
        else:
            assert isinstance(m["methodBase"], str) and m["methodBase"]

def test_fluid_model_base_is_fluid() -> None:
    fluid = next(m for m in config.ECON_MODELS if m["econModelType"] == "FluidModel")
    assert fluid["methodBase"] == "fluid"

def test_assignable_set() -> None:
    assignable = {m["econModelType"] for m in config.ECON_MODELS if m["assignable"]}
    assert assignable == {
        "ActualOrForecast", "Capex", "Dates", "Depreciation", "Differentials",
        "Emission", "Escalation", "Expenses", "FluidModel", "Operations",
        "OwnershipReversion", "Pricing", "ProductionTaxes", "ReservesCategory",
        "Risking", "StreamProperties",
    }
    assert "GeneralOptions" not in assignable
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src/combocurve_api_helper/test_econ_models_config.py -v`
Expected: FAIL (`KeyError`/`AssertionError` — fields absent).

- [ ] **Step 3: Edit the JSON**

Add to every entry `"methodBase"`, `"hasCrud"`, `"assignable"`. `methodBase` = `route` with `-`→`_` (e.g. `date-settings`→`date_settings`), except `FluidModel`→`fluid`. Null-route entries: `"methodBase": null, "hasCrud": false, "assignable": false`. Example entries:

```json
{ "qualifier": "capex", "econModelType": "Capex", "route": "capex",
  "methodBase": "capex", "hasCrud": true, "assignable": true },
{ "qualifier": "dates", "econModelType": "Dates", "route": "date-settings",
  "methodBase": "date_settings", "hasCrud": true, "assignable": true },
{ "qualifier": "generalOptions", "econModelType": "GeneralOptions", "route": "general-options",
  "methodBase": "general_options", "hasCrud": true, "assignable": false },
{ "qualifier": "fluidModel", "econModelType": "FluidModel", "route": "fluid-models",
  "methodBase": "fluid", "hasCrud": true, "assignable": true },
{ "qualifier": "operations", "econModelType": "Operations", "route": "operations",
  "methodBase": "operations", "hasCrud": true, "assignable": true },
{ "qualifier": "forecast", "econModelType": "Forecast", "route": null,
  "methodBase": null, "hasCrud": false, "assignable": false }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest src/combocurve_api_helper/test_econ_models_config.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/combocurve_api_helper/assets/econModels.json src/combocurve_api_helper/test_econ_models_config.py
git commit -m "feat: add methodBase/hasCrud/assignable to econModels.json"
```

---

### Task 2: New generic assignment-write primitives

**Files:**
- Modify: `src/combocurve_api_helper/models.py`
- Test: `src/combocurve_api_helper/test_assignment_write_generics.py`

**Interfaces:**
- Consumes: existing `get_econ_model_assignments_by_type_by_id_url(self, project_id, econ_model_type, model_id, filters=None) -> str`; base `_post_items(url, data) -> ItemList`, `_put_items(url, data) -> ItemList`, `_delete_responses(url, data) -> List[Response]`.
- Produces: on `Models` — `post_econ_model_assignments_by_type_by_id(self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList`; `put_…(…) -> ItemList`; `delete_…(self, project_id, econ_model_type, model_id, data: ItemList) -> ItemList`.

- [ ] **Step 1: Write the failing test** (delegation verified without network via monkeypatch)

```python
# src/combocurve_api_helper/test_assignment_write_generics.py
from combocurve_api_helper.models import Models

def test_post_put_delete_assignment_generics_delegate(monkeypatch) -> None:
    m = Models.__new__(Models)  # no auth/__init__
    calls = {}
    monkeypatch.setattr(m, "get_econ_model_assignments_by_type_by_id_url",
                        lambda pid, t, mid, filters=None: f"URL/{pid}/{t}/{mid}")
    monkeypatch.setattr(m, "_post_items", lambda url, data: ("POST", url, data))
    monkeypatch.setattr(m, "_put_items", lambda url, data: ("PUT", url, data))
    monkeypatch.setattr(m, "_delete_responses", lambda url, data: ("DEL", url, data))
    body = [{"scenario": "s", "qualifierName": "P50", "wells": ["w"], "allWells": False}]
    assert m.post_econ_model_assignments_by_type_by_id("p", "Capex", "id", body) == ("POST", "URL/p/Capex/id", body)
    assert m.put_econ_model_assignments_by_type_by_id("p", "Capex", "id", body) == ("PUT", "URL/p/Capex/id", body)
    assert m.delete_econ_model_assignments_by_type_by_id("p", "Capex", "id", body) == ("DEL", "URL/p/Capex/id", body)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src/combocurve_api_helper/test_assignment_write_generics.py -v`
Expected: FAIL (`AttributeError: post_econ_model_assignments_by_type_by_id`).

- [ ] **Step 3: Add the three generics to `Models`** (place near `get_econ_model_assignments_by_type_by_id`)

```python
    def post_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList:
        """Create assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._post_items(url, data)

    def put_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList:
        """Upsert assignments for a specific econ model (by type + id)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._put_items(url, data)

    def delete_econ_model_assignments_by_type_by_id(
            self, project_id: str, econ_model_type: str, model_id: str, data: ItemList) -> ItemList:
        """Delete assignments for a specific econ model (by type + id).

        NOTE: the delete request body/filters for this route are confirmed by
        the live dev test in Task 6; adjust here if the live response shows a
        different shape (e.g. query filters instead of a JSON body)."""
        url = self.get_econ_model_assignments_by_type_by_id_url(project_id, econ_model_type, model_id)
        return self._delete_responses(url, data)  # type: ignore[return-value]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest src/combocurve_api_helper/test_assignment_write_generics.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/combocurve_api_helper/models.py src/combocurve_api_helper/test_assignment_write_generics.py
git commit -m "feat: generic post/put/delete econ-model assignment methods"
```

---

### Task 3: Generator script + generated mixin

**Files:**
- Create: `scripts/generate_model_methods.py`
- Create (generated, committed): `src/combocurve_api_helper/_models_generated.py`
- Test: `src/combocurve_api_helper/test_generated_models.py`

**Interfaces:**
- Consumes: `config.ECON_MODELS` (Task 1 fields); the generic delegates on `Models` (`get_econ_models_by_type[_url]`, `get_econ_model_by_type_by_id[_url]`, `get_econ_model_assignments_by_type_by_id[_url]`, and Task 2 write generics).
- Produces: `_models_generated.py` defining `class _GeneratedModelMethods(_EconModelMethodsBase)` with per-type methods. `_EconModelMethodsBase` is introduced in Task 4; until then the generated module imports it. **Do Task 4's base extraction (Step 3a) before running the generator**, or run the generator after Task 4 — sequencing note below.

> Sequencing: Task 4 extracts `_EconModelMethodsBase`. The generator imports it. Implement Task 4 Step "create `_EconModelMethodsBase`" first, then return here to run the generator. (They share one review; treat 3+4 as a pair.)

- [ ] **Step 1: Write the failing test**

```python
# src/combocurve_api_helper/test_generated_models.py
import subprocess, sys, pathlib
from combocurve_api_helper import config
from combocurve_api_helper._models_generated import _GeneratedModelMethods

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN = REPO / "scripts" / "generate_model_methods.py"
OUT = pathlib.Path(__file__).with_name("_models_generated.py")

def _expected_method_names() -> set[str]:
    names: set[str] = set()
    for m in config.ECON_MODELS:
        b = m["methodBase"]
        if m["hasCrud"]:
            names |= {f"get_{b}_models", f"get_{b}_models_url",
                      f"get_{b}_model_by_id", f"get_{b}_model_by_id_url"}
        if m["assignable"]:
            names |= {f"get_{b}_assignments_by_id", f"get_{b}_assignments_by_id_url",
                      f"post_{b}_assignments_by_id", f"put_{b}_assignments_by_id",
                      f"delete_{b}_assignments_by_id"}
    return names

def test_generated_method_set_matches_config() -> None:
    actual = {n for n in dir(_GeneratedModelMethods) if not n.startswith("_")}
    assert actual == _expected_method_names()

def test_forecast_and_null_route_types_have_no_methods() -> None:
    actual = {n for n in dir(_GeneratedModelMethods) if not n.startswith("_")}
    for token in ("forecast", "network", "pseries", "schedule"):
        assert not any(token in n for n in actual)

def test_generated_file_is_current() -> None:
    fresh = subprocess.run([sys.executable, str(GEN), "--stdout"],
                           capture_output=True, text=True, check=True).stdout
    assert fresh == OUT.read_text(encoding="utf-8"), "Re-run scripts/generate_model_methods.py and commit."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src/combocurve_api_helper/test_generated_models.py -v`
Expected: FAIL (`ModuleNotFoundError: _models_generated` / generator missing).

- [ ] **Step 3: Write the generator** (`scripts/generate_model_methods.py`)

```python
"""Generate src/combocurve_api_helper/_models_generated.py from econModels.json.

Run: python scripts/generate_model_methods.py          # writes the file
     python scripts/generate_model_methods.py --stdout # prints (used by tests)
"""
from __future__ import annotations
import sys, pathlib
from combocurve_api_helper import config

HEADER = '''\
# DO NOT EDIT -- generated by scripts/generate_model_methods.py from econModels.json.
# Re-run that script after changing econModels.json.
from __future__ import annotations

from typing import Dict, Optional, Union

from .base import Item, ItemList
from ._econ_model_base import _EconModelMethodsBase


class _GeneratedModelMethods(_EconModelMethodsBase):
    """Per-type econ-model methods (generated). Mixed into Models."""
'''

CRUD = '''
    def get_{b}_models_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        return self.get_econ_models_by_type_url(project_id, "{t}", filters)

    def get_{b}_models(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        return self.get_econ_models_by_type(project_id, "{t}", filters)

    def get_{b}_model_by_id_url(self, project_id: str, model_id: str,
                                filters: Optional[Dict[str, str]] = None) -> str:
        return self.get_econ_model_by_type_by_id_url(project_id, "{t}", model_id, filters)

    def get_{b}_model_by_id(self, project_id: str, model_id: str) -> Union[Item, None]:
        return self.get_econ_model_by_type_by_id(project_id, "{t}", model_id)
'''

ASSIGN = '''
    def get_{b}_assignments_by_id_url(self, project_id: str, model_id: str,
                                      filters: Optional[Dict[str, str]] = None) -> str:
        return self.get_econ_model_assignments_by_type_by_id_url(project_id, "{t}", model_id, filters)

    def get_{b}_assignments_by_id(self, project_id: str, model_id: str) -> Union[ItemList, None]:
        return self.get_econ_model_assignments_by_type_by_id(project_id, "{t}", model_id)

    def post_{b}_assignments_by_id(self, project_id: str, model_id: str, data: ItemList) -> ItemList:
        return self.post_econ_model_assignments_by_type_by_id(project_id, "{t}", model_id, data)

    def put_{b}_assignments_by_id(self, project_id: str, model_id: str, data: ItemList) -> ItemList:
        return self.put_econ_model_assignments_by_type_by_id(project_id, "{t}", model_id, data)

    def delete_{b}_assignments_by_id(self, project_id: str, model_id: str, data: ItemList) -> ItemList:
        return self.delete_econ_model_assignments_by_type_by_id(project_id, "{t}", model_id, data)
'''


def render() -> str:
    parts = [HEADER]
    for m in config.ECON_MODELS:
        b, t = m["methodBase"], m["econModelType"]
        if m["hasCrud"]:
            parts.append(CRUD.format(b=b, t=t))
        if m["assignable"]:
            parts.append(ASSIGN.format(b=b, t=t))
    return "".join(parts)


def main() -> None:
    text = render()
    if "--stdout" in sys.argv:
        sys.stdout.write(text)
        return
    out = pathlib.Path(__file__).resolve().parents[1] / "src" / "combocurve_api_helper" / "_models_generated.py"
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Generate the file, then run tests**

Run:
```bash
python scripts/generate_model_methods.py
pytest src/combocurve_api_helper/test_generated_models.py -v
```
Expected: file written; 3 tests PASS. (Requires Task 4's `_econ_model_base.py` to exist — do Task 4 Step 3a first.)

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_model_methods.py src/combocurve_api_helper/_models_generated.py src/combocurve_api_helper/test_generated_models.py
git commit -m "feat: generator + generated per-type econ-model methods"
```

---

### Task 4: Extract generics base, compose Models, remove hand-written per-type methods

**Files:**
- Create: `src/combocurve_api_helper/_econ_model_base.py`
- Modify: `src/combocurve_api_helper/models.py`
- Test: reuse `test_generated_models.py`; add a parity check.

**Interfaces:**
- Produces: `class _EconModelMethodsBase(APIBase)` holding the generic delegates (`get_econ_models[_url]`, `get_econ_models_by_type[_url]`, `get_econ_model_by_type_by_id[_url]`, `get_econ_model_assignments_by_type_by_id[_url]`, and Task 2 write generics). `class Models(_GeneratedModelMethods)` — inherits generated per-type methods; `ComboCurveAPI` MRO unchanged.

- [ ] **Step 3a (do before Task 3 Step 4): create `_econ_model_base.py`**

Move the generic, non-per-type econ-model methods out of `models.py` into `_EconModelMethodsBase(APIBase)`: `get_econ_models[_url]`, `get_econ_models_by_type[_url]`, `get_econ_model_by_type_by_id[_url]`, `get_econ_model_assignments_by_type_by_id[_url]`, and the three Task-2 write generics. Keep their bodies identical.

- [ ] **Step 1: Add parity test**

```python
# append to test_generated_models.py
def test_no_handwritten_per_type_methods_remain() -> None:
    import inspect
    from combocurve_api_helper import models
    src = inspect.getsource(models)
    for bad in ("def get_capex_models", "def get_differential_models",
                "def get_reserves_categories_by_id", "def get_fluid_models_by_id_url"):
        assert bad not in src, f"hand-written per-type method still in models.py: {bad}"
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest src/combocurve_api_helper/test_generated_models.py::test_no_handwritten_per_type_methods_remain -v`
Expected: FAIL (methods still present).

- [ ] **Step 3: Edit `models.py`**

Delete all hand-written per-type methods (every `get_<type>_models[_url]`, `get_<type>_model_by_id[_url]`, `get_<type>_assignments_by_id[_url]`, and the irregular singular/`_by_id` variants). Change the class to:

```python
from ._econ_model_base import _EconModelMethodsBase  # noqa: F401 (kept for clarity)
from ._models_generated import _GeneratedModelMethods


class Models(_GeneratedModelMethods):
    """Econ-model endpoints: generic delegates (via _EconModelMethodsBase) +
    generated per-type methods (via _GeneratedModelMethods)."""
    pass
```

(`_GeneratedModelMethods` already extends `_EconModelMethodsBase(APIBase)`, so `Models` gets everything. Leave any genuinely non-econ-model methods that were in `Models` in place by keeping them on a small retained class or folding into the base — verify none are dropped.)

- [ ] **Step 4: Run full helper test suite + mypy + flake8**

Run:
```bash
pytest
mypy src/combocurve_api_helper
flake8 src/combocurve_api_helper
```
Expected: all pass; method-set, freshness, parity, and existing tests green.

- [ ] **Step 5: Commit**

```bash
git add src/combocurve_api_helper/
git commit -m "refactor: Models composes generated per-type methods; drop hand-written sprawl"
```

---

### Task 5: Add the scenario-grid GET wrapper (already drafted) under test

**Files:**
- Modify: `src/combocurve_api_helper/scenarios.py` (the `get_scenario_econ_model_assignments[_url]` added during design — verify present)
- Test: `src/combocurve_api_helper/test_scenario_assignments.py`

**Interfaces:**
- Produces: `get_scenario_econ_model_assignments(self, project_id: str, scenario_id: str) -> ItemList` and `_url` variant.

- [ ] **Step 1: Write the failing test**

```python
# src/combocurve_api_helper/test_scenario_assignments.py
from combocurve_api_helper.scenarios import Scenarios

def test_scenario_assignments_url_and_fetch(monkeypatch) -> None:
    s = Scenarios.__new__(Scenarios)
    monkeypatch.setattr(s, "get_scenario_by_id_url", lambda p, sc: f"BASE/{p}/{sc}")
    assert s.get_scenario_econ_model_assignments_url("p", "sc") == "BASE/p/sc/assignments/econ-models"
    monkeypatch.setattr(s, "_get_items", lambda url: [("grid", url)])
    assert s.get_scenario_econ_model_assignments("p", "sc") == [("grid", "BASE/p/sc/assignments/econ-models")]
```

- [ ] **Step 2: Run to verify** (passes if the design-time methods are present; if not, add them per the spec) — Run: `pytest src/combocurve_api_helper/test_scenario_assignments.py -v`.

- [ ] **Step 3: Ensure the methods exist** (added during design; confirm/add `get_scenario_econ_model_assignments_url` after `get_scenario_wells_url`, and `get_scenario_econ_model_assignments` after `get_scenario_wells`, using `self._get_items(url)`).

- [ ] **Step 4: Run test** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/combocurve_api_helper/scenarios.py src/combocurve_api_helper/test_scenario_assignments.py
git commit -m "feat: get_scenario_econ_model_assignments (scenario assignment grid)"
```

---

### Task 6: Live dev write test (skip-by-default)

**Files:**
- Create: `src/combocurve_api_helper/test_assignments_live.py`

**Interfaces:**
- Consumes: `ComboCurveAPI.from_alternate_config(combocurve_json_path, cc_api_config_json_path)`; the Task-2/3 write methods; Task-5 grid read.

- [ ] **Step 1: Write the skip-gated live test**

```python
# src/combocurve_api_helper/test_assignments_live.py
import os, pathlib, time
import pytest
from combocurve_api_helper import ComboCurveAPI

DEV = pathlib.Path.home() / ".combocurve" / "dev"
pytestmark = pytest.mark.skipif(
    not (DEV / "combocurve.json").exists() or not os.environ.get("CC_LIVE_TEST"),
    reason="dev creds + CC_LIVE_TEST=1 required",
)

# Set these to an existing dev project/scenario/well before running (see plan).
PROJECT_ID = os.environ.get("CC_DEV_PROJECT_ID", "")
SCENARIO_ID = os.environ.get("CC_DEV_SCENARIO_ID", "")
WELL_ID = os.environ.get("CC_DEV_WELL_ID", "")
QUALIFIER = os.environ.get("CC_DEV_QUALIFIER", "Default")


def _dev_api() -> ComboCurveAPI:
    return ComboCurveAPI.from_alternate_config(
        combocurve_json_path=DEV / "combocurve.json",
        cc_api_config_json_path=DEV / "cc-api.config.json",
    )


def test_capex_assignment_roundtrip() -> None:
    api = _dev_api()
    name = f"zz_apitest_{int(time.time())}"
    # minimal valid capex body confirmed against the API doc/data-dictionary:
    body = [{"name": name, "unique": False, "otherCapex": {"rows": []}}]
    api.put_capex_models(PROJECT_ID, data=body) if hasattr(api, "put_capex_models") else api._put_items(
        api.get_capex_models_url(PROJECT_ID), body)
    models = api.get_capex_models(PROJECT_ID, filters={"name": name})
    model_id = api.extract_id(models, name=name)
    try:
        api.put_capex_assignments_by_id(PROJECT_ID, model_id,
            [{"scenario": SCENARIO_ID, "allWells": False, "qualifierName": QUALIFIER, "wells": [WELL_ID]}])
        grid = api.get_scenario_econ_model_assignments(PROJECT_ID, SCENARIO_ID)
        match = [w for w in grid if w.get("wellId") == WELL_ID]
        assert match, "test well not found in scenario grid"
    finally:
        # cleanup: delete the throwaway model (removes its assignments)
        api._delete_responses(api.get_capex_model_by_id_url(PROJECT_ID, model_id), data=[])
```

- [ ] **Step 2: Run against dev** (you provide project/scenario/well + cleanup-OK)

Run: `CC_LIVE_TEST=1 CC_DEV_PROJECT_ID=… CC_DEV_SCENARIO_ID=… CC_DEV_WELL_ID=… pytest src/combocurve_api_helper/test_assignments_live.py -v`
Expected: PASS; throwaway model deleted. **If the assignment PUT or capex create errors, adjust the body to the data-dictionary shape and re-run** — this is the step that validates the real payloads.

- [ ] **Step 3: Confirm skip behavior** — Run `pytest src/combocurve_api_helper/test_assignments_live.py -v` without env vars; Expected: SKIPPED.

- [ ] **Step 4: Commit**

```bash
git add src/combocurve_api_helper/test_assignments_live.py
git commit -m "test: skip-by-default live dev assignment round-trip"
```

---

### Task 7: Fix renamed-method callers across repos

**Files:**
- Modify: any usages in `~/Projects/util/cc-afe-sync`, `~/Projects/util/cc-insert-wells`, `~/Projects/claude/VDR`, and within the helper itself.

- [ ] **Step 1: Grep for the six old names**

```bash
for d in ~/Projects/util/cc-afe-sync ~/Projects/util/cc-insert-wells ~/Projects/claude/VDR \
         ~/Projects/petbox-dev/combocurve-api-helper/src; do
  grep -rnE "get_differential_models|get_emission_models|get_expense_models|get_risking_models|get_fluid_models_by_id_url|get_reserves_categories_by_id\b" "$d" 2>/dev/null
done
```
Expected: a list of call sites (possibly empty).

- [ ] **Step 2: Rename each hit** to its normalized name (table in Global Constraints). Edit in place.

- [ ] **Step 3: Verify no stragglers** — re-run the grep; Expected: empty.

- [ ] **Step 4: Commit (per repo touched)**

```bash
# in each repo with changes:
git add -A && git commit -m "refactor: rename to normalized econ-model helper methods"
```

---

### Task 8: Release helper + switch `vdr qc cc` off `_get_items`

**Files:**
- Modify: `src/combocurve_api_helper/__init__.py` (`__version__`)
- Modify: `~/Projects/claude/VDR/src/vdr/qc/cc/command.py`

- [ ] **Step 1: Bump version + build + reinstall**

```bash
cd ~/Projects/petbox-dev/combocurve-api-helper
# bump __version__ (e.g. 1.2.0 -> 1.3.0) in src/combocurve_api_helper/__init__.py
python -m build
twine upload -r internal dist/*        # internal PyPI (per project convention)
pip install -U combocurve_api_helper   # in the `core` env
python -c "from combocurve_api_helper import ComboCurveAPI; print(hasattr(ComboCurveAPI, 'get_scenario_econ_model_assignments'))"
```
Expected: prints `True`.

- [ ] **Step 2: Switch the vdr fetch to the named method**

In `vdr/qc/cc/command.py`, `_fetch_forecast_assignment_grid`:
```python
def _fetch_forecast_assignment_grid(api: Any, project_id: str, scenario_id: str) -> list[dict[str, Any]]:
    """Fetch the scenario econ-model assignment grid (cursor-paginated)."""
    grid: list[dict[str, Any]] = api.get_scenario_econ_model_assignments(project_id, scenario_id)
    return grid
```

- [ ] **Step 3: Verify vdr**

Run:
```bash
cd ~/Projects/claude/VDR
python -m pytest tests/test_qc_cc.py tests/test_integration.py -q
ruff check src/vdr/qc/cc/ && python -m mypy src/vdr/qc/cc/ --strict
```
Expected: pass.

- [ ] **Step 4: Live re-check** (optional) — run the vdr validation against Granite Ridge; expect 824 wells, all OK.

- [ ] **Step 5: Commit (vdr)**

```bash
git add src/vdr/qc/cc/command.py
git commit -m "refactor(qc): use helper get_scenario_econ_model_assignments wrapper"
```

---

## Self-Review

- **Spec coverage:** §1 source-of-truth → Task 1. §2 generator → Task 3. §3 write generics → Task 2 (generic) + Task 3 (per-type). §4 composition → Task 4. §5 back-compat renames → Task 4 (drop) + Task 7 (callers). §6 verification → Tasks 1/3/4 (offline) + Task 6 (live). §7 rollout → Task 8. Scenario-grid GET → Task 5. All covered.
- **Placeholder scan:** delete-assignment body shape is flagged for live confirmation (Task 2/6), not left vague — the method is concrete, the live test validates the payload. No TODO/TBD requirements.
- **Type consistency:** generated methods call exactly the generic signatures defined in Task 2 / existing code (`get_econ_models_by_type`, `…by_type_by_id -> Union[Item,None]`, `…assignments_by_type_by_id -> Union[ItemList,None]`, write generics `-> ItemList`). `methodBase`/`assignable` sets match Global Constraints.
