# Econ-Model model⇄CSV-file Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add file-level `to_csv`/`from_csv`/`read_csv`/`write_csv` over the existing row-level econ-model mappers, so a caller converts a whole multi-model CSV file ⇄ `list[dict]` in one call.

**Architecture:** Promote `EconModelMapper` from a `Protocol` to a concrete ABC that implements the four file-level methods once, in terms of the abstract `columns`/`to_csv_rows`/`from_csv_rows`. All 11 mappers inherit it. A codegen script then emits per-type `<base>_to_csv`/`<base>_from_csv`/`get_<base>_mapper` free functions alongside the existing `<base>_to_csv_rows`/`<base>_from_csv_rows`.

**Tech Stack:** Python 3, stdlib `csv`/`io`/`abc`, pydantic (already used by mappers), pytest, mypy.

## Global Constraints

- Full type annotations on every function; must pass `mypy --package combocurve_api_helper`.
- `from __future__ import annotations` stays at the top of modules that already use it.
- ASCII only in code and docstrings; no em-dashes/smart quotes.
- Level A sugar only: no new API calls, no fetch+convert fusion.
- The model dict IS the JSON: surface is CSV-text ⇄ `list[dict]`; no `to_json`/`from_json`.
- `get_<base>_mapper()` returns the base `EconModelMapper` type (program to the interface).
- `_csv_generated.py` is a generated artifact: never hand-edit it; change `scripts/generate_csv_functions.py` and regenerate.
- Multi-model grouping keys strictly off the `Model Name` column, first-seen order.
- `to_csv([])` returns a header-only string; never raises.

---

### Task 1: File-level methods on the mapper base class

**Files:**
- Modify: `src/combocurve_api_helper/econ_models/base.py` (imports; add `group_rows_by_model_name`; convert `EconModelMapper` Protocol → ABC with 4 concrete methods)
- Modify (one-line class-header each): `actual_or_forecast.py`, `capex.py`, `date_settings.py`, `differentials.py`, `expenses.py`, `ownership_reversion.py`, `pricing.py`, `production_taxes.py`, `reserves_category.py`, `risking.py`, `stream_properties.py` (all under `src/combocurve_api_helper/econ_models/`)
- Test: `tests/econ_models/test_csv_file_io.py` (create)

**Interfaces:**
- Consumes: each mapper's existing `columns: List[str]`, `to_csv_rows(model, context=None) -> List[Dict[str,str]]`, `from_csv_rows(rows) -> Dict[str,Any]`; test helpers `FIXTURE_FILES`, `FIXTURES_DIR`, `group_by_model_name`, `read_csv_rows`, `project_columns` from `tests/econ_models/csv_fixture_io.py`.
- Produces (relied on by Task 2):
  - `EconModelMapper.to_csv(self, models: List[Dict[str, Any]], context: Optional[Context] = None) -> str`
  - `EconModelMapper.from_csv(self, source: Union[str, TextIO]) -> List[Dict[str, Any]]`
  - `EconModelMapper.read_csv(self, path: Union[str, os.PathLike[str]]) -> List[Dict[str, Any]]`
  - `EconModelMapper.write_csv(self, path: Union[str, os.PathLike[str]], models: List[Dict[str, Any]], context: Optional[Context] = None) -> None`
  - module function `group_rows_by_model_name(rows: List[Dict[str, str]]) -> List[List[Dict[str, str]]]`

- [ ] **Step 1: Write the failing test**

Create `tests/econ_models/test_csv_file_io.py`:

```python
"""Tests for the file-level econ-model CSV layer (EconModelMapper.to_csv/from_csv/
read_csv/write_csv) against the real trimmed CC-export fixtures."""

import csv
import io
import os
import pathlib

import pytest

from combocurve_api_helper.econ_models import get_mapper
from combocurve_api_helper.econ_models.base import group_rows_by_model_name
from tests.econ_models.csv_fixture_io import (
    FIXTURE_FILES,
    FIXTURES_DIR,
    group_by_model_name,
    project_columns,
    read_csv_rows,
)


@pytest.mark.parametrize('econ_model_type', sorted(FIXTURE_FILES))
def test_from_csv_equals_per_model_from_csv_rows(econ_model_type: str) -> None:
    mapper = get_mapper(econ_model_type)
    for filename in FIXTURE_FILES[econ_model_type]:
        path = os.path.join(FIXTURES_DIR, filename)
        text = pathlib.Path(path).read_text(encoding='utf-8')
        rows = read_csv_rows(path)
        expected = [mapper.from_csv_rows(g) for g in group_by_model_name(rows).values()]
        assert mapper.from_csv(text) == expected, f'{econ_model_type} / {filename}'


@pytest.mark.parametrize('econ_model_type', sorted(FIXTURE_FILES))
def test_to_csv_reemits_model_parameter_columns(econ_model_type: str) -> None:
    mapper = get_mapper(econ_model_type)
    compare_columns = mapper.columns[3:-1]  # exclude Model Id/Created At/Project Name + Last Update
    for filename in FIXTURE_FILES[econ_model_type]:
        path = os.path.join(FIXTURES_DIR, filename)
        rows = read_csv_rows(path)
        models = [mapper.from_csv_rows(g) for g in group_by_model_name(rows).values()]
        reparsed = list(csv.DictReader(io.StringIO(mapper.to_csv(models))))
        expected = [project_columns(r, compare_columns) for r in rows]
        actual = [project_columns(r, compare_columns) for r in reparsed]
        assert actual == expected, f'{econ_model_type} / {filename}'


def test_to_csv_empty_is_header_only() -> None:
    mapper = get_mapper('Expenses')
    text = mapper.to_csv([])
    lines = text.splitlines()
    assert len(lines) == 1
    assert list(csv.reader([lines[0]]))[0] == mapper.columns
    assert mapper.from_csv(text) == []


def test_from_csv_accepts_string_and_file_like() -> None:
    mapper = get_mapper('Expenses')
    path = os.path.join(FIXTURES_DIR, FIXTURE_FILES['Expenses'][0])
    text = pathlib.Path(path).read_text(encoding='utf-8')
    from_string = mapper.from_csv(text)
    from_buffer = mapper.from_csv(io.StringIO(text))
    assert from_string == from_buffer


def test_from_csv_without_model_name_column_raises() -> None:
    mapper = get_mapper('Expenses')
    with pytest.raises(ValueError, match='Model Name'):
        mapper.from_csv('Key,Category\nfoo,bar\n')


def test_read_write_round_trip(tmp_path: pathlib.Path) -> None:
    mapper = get_mapper('Expenses')
    src = os.path.join(FIXTURES_DIR, FIXTURE_FILES['Expenses'][0])
    models = mapper.read_csv(src)
    out = tmp_path / 'out.csv'
    mapper.write_csv(out, models)
    assert mapper.read_csv(out) == models


def test_group_rows_by_model_name_preserves_first_seen_order() -> None:
    rows = [
        {'Model Name': 'b', 'x': '1'},
        {'Model Name': 'a', 'x': '2'},
        {'Model Name': 'b', 'x': '3'},
    ]
    groups = group_rows_by_model_name(rows)
    assert [g[0]['Model Name'] for g in groups] == ['b', 'a']
    assert [len(g) for g in groups] == [2, 1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/econ_models/test_csv_file_io.py -v`
Expected: FAIL — `ImportError: cannot import name 'group_rows_by_model_name'` (and `AttributeError: 'ExpensesMapper' object has no attribute 'from_csv'` once the import is added).

- [ ] **Step 3: Rewrite `base.py` imports and convert the class to an ABC**

Replace the top import block of `src/combocurve_api_helper/econ_models/base.py`:

```python
import csv
import io
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, NamedTuple, Optional, TextIO, Tuple, Union

from . import formats
```

Keep `Context`, `common_columns`, and `model_identity` exactly as they are. Add this module
function immediately before the class definition:

```python
def group_rows_by_model_name(rows: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    """Split CSV rows into per-model groups keyed by 'Model Name', preserving first-seen order.

    A CC econ-model CSV stacks many models of one type, each spanning one or more rows that
    share a 'Model Name'. This is the production counterpart of the test helper of the same
    intent; `from_csv` uses it to feed one model's rows at a time to `from_csv_rows`.
    """
    groups: Dict[str, List[Dict[str, str]]] = {}
    order: List[str] = []
    for row in rows:
        name = row.get('Model Name', '')
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(row)
    return [groups[name] for name in order]
```

Replace the `class EconModelMapper(Protocol):` block with:

```python
class EconModelMapper(ABC):
    """Base for econ-model API<->CSV mappers.

    Subclasses supply the type-specific pieces (`econ_model_type`, `columns`, `to_csv_rows`,
    `from_csv_rows`); this base implements the file-level conversions once in terms of them.
    """

    econ_model_type: str
    columns: List[str]

    @abstractmethod
    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        """Convert one econ-model API dict to its CSV rows (each keyed by `self.columns`)."""
        ...

    @abstractmethod
    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        """Reconstruct one econ-model API dict from the CSV rows of a single model."""
        ...

    def to_csv(self, models: List[Dict[str, Any]], context: Optional[Context] = None) -> str:
        """Serialize econ-model API dicts to a multi-model CSV string.

        The header (from `self.columns`) is always written, so `to_csv([])` returns a
        header-only string. Lines use the csv module's default CRLF terminator; write the
        result to a file opened with `newline=''` to avoid doubled newlines on Windows
        (`write_csv` does this).
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.columns)
        writer.writeheader()
        for model in models:
            writer.writerows(self.to_csv_rows(model, context))
        return buffer.getvalue()

    def from_csv(self, source: Union[str, TextIO]) -> List[Dict[str, Any]]:
        """Parse a multi-model CSV (a string or text file-like) into a list of API dicts, one
        per model, grouped by 'Model Name' in first-seen order.

        Raises `ValueError` if the CSV lacks a 'Model Name' column (not a CC econ-model export).
        """
        text = source if isinstance(source, str) else source.read()
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None or 'Model Name' not in reader.fieldnames:
            raise ValueError("CSV has no 'Model Name' column; not a ComboCurve econ-model export.")
        return [self.from_csv_rows(group) for group in group_rows_by_model_name(list(reader))]

    def read_csv(self, path: Union[str, os.PathLike[str]]) -> List[Dict[str, Any]]:
        """Read a multi-model CSV file into a list of econ-model API dicts."""
        with open(path, 'r', encoding='utf-8', newline='') as handle:
            return self.from_csv(handle)

    def write_csv(
        self,
        path: Union[str, os.PathLike[str]],
        models: List[Dict[str, Any]],
        context: Optional[Context] = None,
    ) -> None:
        """Write a list of econ-model API dicts to a multi-model CSV file (UTF-8)."""
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            handle.write(self.to_csv(models, context))
```

- [ ] **Step 4: Make all 11 mappers inherit the base**

In each of the 11 mapper modules listed under **Files**, add `EconModelMapper` to the existing
`from .base import ...` line and add it as the class base. Example for `capex.py`:

```python
# import line (add EconModelMapper)
from .base import Context, EconModelMapper, common_columns, model_identity
```
```python
# class header
class CapexMapper(EconModelMapper):
```

Apply the identical change to each module's mapper class:
`ActualOrForecastMapper`, `CapexMapper`, `DateSettingsMapper`, `DifferentialsMapper`,
`ExpensesMapper`, `OwnershipReversionMapper`, `PricingMapper`, `ProductionTaxesMapper`,
`ReservesCategoryMapper`, `RiskingMapper`, `StreamPropertiesMapper`. Each already defines
`columns`, `to_csv_rows`, and `from_csv_rows`, so no body changes are needed.

- [ ] **Step 5: Run the file-level tests to verify they pass**

Run: `python -m pytest tests/econ_models/test_csv_file_io.py -v`
Expected: PASS (all parametrized cases + edge cases).

- [ ] **Step 6: Run the full econ_models suite and mypy (nothing regressed)**

Run: `python -m pytest tests/econ_models -v`
Expected: PASS, including `test_fixtures.py` and `test_csv_generated.py` (unchanged behavior).

Run: `mypy --package combocurve_api_helper`
Expected: no errors (note `os.PathLike[str]`, `Union[str, TextIO]`, and the `isinstance(source, str)` narrowing).

- [ ] **Step 7: Commit**

```bash
git add src/combocurve_api_helper/econ_models/base.py \
        src/combocurve_api_helper/econ_models/actual_or_forecast.py \
        src/combocurve_api_helper/econ_models/capex.py \
        src/combocurve_api_helper/econ_models/date_settings.py \
        src/combocurve_api_helper/econ_models/differentials.py \
        src/combocurve_api_helper/econ_models/expenses.py \
        src/combocurve_api_helper/econ_models/ownership_reversion.py \
        src/combocurve_api_helper/econ_models/pricing.py \
        src/combocurve_api_helper/econ_models/production_taxes.py \
        src/combocurve_api_helper/econ_models/reserves_category.py \
        src/combocurve_api_helper/econ_models/risking.py \
        src/combocurve_api_helper/econ_models/stream_properties.py \
        tests/econ_models/test_csv_file_io.py
git commit -m "feat(econ-models): file-level to_csv/from_csv/read_csv/write_csv on mapper base

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Generate per-type to_csv / from_csv / get_<base>_mapper

**Files:**
- Modify: `scripts/generate_csv_functions.py` (extend `HEADER` imports + docstring, `FUNCS` template, `render` name list)
- Regenerate: `src/combocurve_api_helper/econ_models/_csv_generated.py` (artifact — produced by the script, do not hand-edit)
- Modify: `tests/econ_models/test_csv_generated.py` (coverage/delegation tests for the new names)

**Interfaces:**
- Consumes: `EconModelMapper.to_csv`/`from_csv` from Task 1; `config.ECON_MODELS` (`methodBase`, `econModelType`); `registry.MAPPERS`.
- Produces (for callers / README in Task 3): free functions `<base>_to_csv(models, context=None) -> str`,
  `<base>_from_csv(source) -> List[Dict[str, Any]]`, `get_<base>_mapper() -> EconModelMapper`, for every
  mapper-backed type, exported via `_csv_generated.__all__`.

- [ ] **Step 1: Update the coverage/delegation tests first (failing)**

In `tests/econ_models/test_csv_generated.py`, add the imports `import io`, `pathlib` (already present),
and `read_csv_rows`/`FIXTURES_DIR` (already imported). Replace the two coverage tests and extend the
delegation test:

```python
def test_every_mapper_has_all_convenience_functions() -> None:
    for econ_model_type in MAPPERS:
        base = _BASE_BY_TYPE[econ_model_type]
        for suffix in ('to_csv_rows', 'from_csv_rows', 'to_csv', 'from_csv'):
            assert hasattr(_csv_generated, f'{base}_{suffix}'), (econ_model_type, suffix)
        assert hasattr(_csv_generated, f'get_{base}_mapper'), econ_model_type


def test_all_lists_exactly_five_names_per_mapper() -> None:
    assert len(_csv_generated.__all__) == 5 * len(MAPPERS)
    for name in _csv_generated.__all__:
        assert name.endswith(('_to_csv_rows', '_from_csv_rows', '_to_csv', '_from_csv')) or (
            name.startswith('get_') and name.endswith('_mapper')
        )
        assert callable(getattr(_csv_generated, name))
```

Extend `test_convenience_functions_delegate_to_mapper` — after the existing row-level asserts inside the
`for filename` loop, add file-level delegation:

```python
        text = (pathlib.Path(FIXTURES_DIR) / filename).read_text(encoding='utf-8')
        to_csv = getattr(_csv_generated, f'{base}_to_csv')
        from_csv = getattr(_csv_generated, f'{base}_from_csv')
        get_the_mapper = getattr(_csv_generated, f'get_{base}_mapper')
        assert get_the_mapper() is mapper
        assert from_csv(text) == mapper.from_csv(text)
        assert to_csv(mapper.from_csv(text)) == mapper.to_csv(mapper.from_csv(text))
```

(Delete the now-renamed `test_every_mapper_has_both_convenience_functions` and
`test_all_lists_exactly_two_callables_per_mapper`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/econ_models/test_csv_generated.py -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'expenses_to_csv'` (the generated module still holds only the row-level pair) and the freshness test still passes (file matches the current generator).

- [ ] **Step 3: Extend the generator's `HEADER`**

In `scripts/generate_csv_functions.py`, replace the `HEADER` string's docstring + import section so it
documents all five per-type names and imports what the new functions need:

```python
HEADER = '''\
# DO NOT EDIT -- generated by scripts/generate_csv_functions.py from econModels.json + the mapper registry.
# Re-run that script after adding/removing a mapper or changing econModels.json.
"""Per-type CSV convenience functions (generated).

Thin, explicit wrappers over `registry.get_mapper(...)` so each econ-model type has named
`<type>_to_csv_rows`/`<type>_from_csv_rows` (row level), `<type>_to_csv`/`<type>_from_csv`
(whole multi-model file, string in/out), and a `get_<type>_mapper()` accessor -- matching the
per-type function convention used elsewhere in the package rather than requiring callers to reach
for the generic `get_mapper`.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TextIO, Union

from .base import Context, EconModelMapper
from .registry import get_mapper
'''
```

- [ ] **Step 4: Extend the generator's `FUNCS` template**

Append the three new functions to the `FUNCS` template (keep the existing two):

```python
FUNCS = '''

def {method_base}_to_csv_rows(model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
    """Convert one `{econ_model_type}` econ-model API dict to CSV rows (model-level export shape)."""
    return get_mapper('{econ_model_type}').to_csv_rows(model, context)


def {method_base}_from_csv_rows(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """Reconstruct a `{econ_model_type}` econ-model API dict from its CSV rows."""
    return get_mapper('{econ_model_type}').from_csv_rows(rows)


def {method_base}_to_csv(models: List[Dict[str, Any]], context: Optional[Context] = None) -> str:
    """Serialize a list of `{econ_model_type}` econ-model API dicts to a multi-model CSV string."""
    return get_mapper('{econ_model_type}').to_csv(models, context)


def {method_base}_from_csv(source: Union[str, TextIO]) -> List[Dict[str, Any]]:
    """Parse a `{econ_model_type}` CSV (string or file-like) into a list of econ-model API dicts."""
    return get_mapper('{econ_model_type}').from_csv(source)


def get_{method_base}_mapper() -> EconModelMapper:
    """Return the singleton mapper for `{econ_model_type}`."""
    return get_mapper('{econ_model_type}')
'''
```

- [ ] **Step 5: Extend the `render` name list**

In `render()`, replace the `names.extend((...))` line with all five generated names:

```python
        names.extend((
            f'{method_base}_to_csv_rows',
            f'{method_base}_from_csv_rows',
            f'{method_base}_to_csv',
            f'{method_base}_from_csv',
            f'get_{method_base}_mapper',
        ))
```

- [ ] **Step 6: Regenerate the artifact**

Run: `python scripts/generate_csv_functions.py`
Expected: `wrote .../econ_models/_csv_generated.py`

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python -m pytest tests/econ_models/test_csv_generated.py -v`
Expected: PASS — freshness test still green (file matches the extended generator), coverage now 5/mapper, delegation includes the file-level functions.

- [ ] **Step 8: Full suite + mypy**

Run: `python -m pytest tests/econ_models -v`
Expected: PASS.

Run: `mypy --package combocurve_api_helper`
Expected: no errors (the generated module's new signatures type-check).

- [ ] **Step 9: Commit**

```bash
git add scripts/generate_csv_functions.py \
        src/combocurve_api_helper/econ_models/_csv_generated.py \
        tests/econ_models/test_csv_generated.py
git commit -m "feat(econ-models): generate per-type to_csv/from_csv + get_<base>_mapper

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: README one-call example

**Files:**
- Modify: `README.md` (the "Econ models to / from CSV" section, currently lines ~114-142)

**Interfaces:**
- Consumes: the generated `expenses_to_csv`/`expenses_from_csv`/`get_expenses_mapper` and the base
  `read_csv`/`write_csv` from Tasks 1-2.

- [ ] **Step 1: Replace the manual DictWriter/DictReader example**

In `README.md`, replace the code block under "### Econ models to / from CSV" (the `import csv` ...
`api.post_expenses_models(...)` block) with the one-call form, and adjust the surrounding prose so it no
longer says the caller assembles the writer/reader:

```markdown
### Econ models to / from CSV

Each econ-model type has an invertible mapper looked up by its PascalCase `econModelType`.
The library exposes per-type convenience functions that convert a whole **multi-model** CSV
(the shape ComboCurve exports) directly to and from lists of API dicts, so no `csv` boilerplate
is needed. `to_csv`/`from_csv` work on strings; `read_csv`/`write_csv` (on the mapper) work on
file paths.

```python
from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.econ_models import (
    expenses_to_csv,
    expenses_from_csv,
    get_expenses_mapper,
)

api = ComboCurveAPI()

# --- ComboCurve -> CSV file ---
models = [api.get_expenses_model_by_id(project_id, model_id)]
get_expenses_mapper().write_csv("expenses.csv", models)

# --- CSV file -> ComboCurve ---
payloads = get_expenses_mapper().read_csv("expenses.csv")   # list[dict], one per model
api.post_expenses_models(project_id, payloads)              # or put_expenses_models(...)

# --- In-memory string round trip ---
csv_text = expenses_to_csv(models)
same_models = expenses_from_csv(csv_text)
```
\```
```

(Preserve the outer triple-backtick fencing already in the README; the inner `\`\`\`` above denotes the
existing fenced Python block that this text replaces.)

- [ ] **Step 2: Verify the README example imports resolve**

Run: `python -c "from combocurve_api_helper.econ_models import expenses_to_csv, expenses_from_csv, get_expenses_mapper; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(econ-models): README one-call CSV example

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- Base ABC + 4 methods + grouping → Task 1. ✅
- 11 mappers inherit → Task 1 Step 4. ✅
- Multi-model file granularity (`list[dict]` both ways) → `to_csv`/`from_csv` signatures + `group_rows_by_model_name`. ✅
- String/file-like core + `read_csv`/`write_csv` path convenience → Task 1 methods + tests. ✅
- Empty list → header-only → `to_csv` (`writeheader` unconditional) + `test_to_csv_empty_is_header_only`. ✅
- Grouping by `Model Name`, first-seen; no-`Model Name`-column `ValueError` → `from_csv` + tests. ✅
- Generated `<base>_to_csv`/`<base>_from_csv`/`get_<base>_mapper`; `read_csv`/`write_csv` methods only → Task 2. ✅
- `__all__` = 5/mapper; freshness/coverage/delegation tests → Task 2. ✅
- README migration → Task 3. ✅
- Out-of-scope items (no API calls, no to_json/from_json, no type auto-detect, no Dates rename) → nothing in the plan adds them. ✅

**Placeholder scan:** No TBD/TODO; every code step shows full code; commands have expected output. ✅

**Type consistency:** `to_csv(models, context=None) -> str`, `from_csv(source: Union[str, TextIO]) -> List[Dict[str, Any]]`, `read_csv(path: Union[str, os.PathLike[str]])`, `write_csv(path, models, context=None) -> None`, `group_rows_by_model_name(rows) -> List[List[Dict[str, str]]]`, `get_<base>_mapper() -> EconModelMapper` — identical in base.py (Task 1), the generator template (Task 2), and the tests. ✅
