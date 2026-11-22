# Docstring freshness check: collapsed arrays hide a length change

Closed: 2026-11-21 -- settled by: `--check` exits 1 for an unsourced marker not in `ALLOWED_UNSOURCED_MARKERS` (and for a stale allowlist entry), the fetch has a 60 s timeout, and malformed collection shapes exit 2; the remaining gap (a collapsed array cannot show a length change) is accepted and documented in CLAUDE.md (maintainer decision, 2026-11-21)
If this was wrong, you will see: a renamed slug or unsourced marker passing `--check` with exit 0, a hung fetch, or a traceback (exit 1) on a malformed collection

Severity: low
Opened: 2026-09-30

## What happens now

`scripts/generate_docstrings.py --check` no longer tolerates unsourced markers (fixed 2026-11-21):

- A marker with no collection example exits 1 and is named, unless it is in
  `ALLOWED_UNSOURCED_MARKERS` (`<file>.py:<method or constant> [<marker line>]`). The list is empty:
  on 2026-11-21 every marker in `src/` had an example. An entry whose marker gets an example, or no
  longer exists, also exits 1, so the list cannot go stale.
- The fetch has a 60 s timeout (`FETCH_TIMEOUT_SECONDS`); a timeout exits 2.
- A collection whose `item` tree, an operation's `request`, or its saved `response` list holds a
  non-object exits 2 (`CollectionUnavailable`), not a traceback.
- Tests: `tests/test_generate_docstrings_check.py`.

Still open: an array whose elements differ only at re-drawn (enum or faker) positions collapses to
one element, so a change in its length is not detected. CLAUDE.md says a length change makes the
block stale; that holds only for arrays that do not collapse (elements that differ in shape or
placeholder values keep their length).

## Why it is not fixed

The collapse exists because Postman doubles example array items, and a re-draw gives each copy a
different literal. The committed docstring shows one element. The docstring cannot record how many
copies the collection had, so `[x, x']` and `[x, x', x'']` render to the same text. Telling them apart
needs either (a) rendering every copy, which makes the doubling noise part of the docstring, or (b) a
side file that stores the collapsed length, which `--check` would compare. Neither is cheap, and
(a) reverses the decision behind the collapse.

## What would unblock it

Decide whether a length change in a duplicated array matters enough for option (b), or correct the
CLAUDE.md sentence to say that collapsed arrays are exempt from the length check.

## Files

- `scripts/generate_docstrings.py`: `fill` (the collapse), `matches_ignoring_enums`
- `tests/test_docstrings_current.py`
