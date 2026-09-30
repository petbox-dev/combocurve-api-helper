# Docstring freshness check tolerates unsourced markers

Severity: low
Opened: 2026-09-30

## What happens now

`scripts/generate_docstrings.py --check` prints a marker with no collection example as "left as-is"
and still exits 0. A slug renamed in the collection therefore drops that block out of the check with
no failure. Also:

- `urlopen` has no timeout; `test_docstrings_current` bounds it at 120 s and skips.
- A collection whose `item` entries are not objects raises a traceback and exits 1, which the
  freshness test reads as "stale", not "skip".
- An array whose elements differ only at re-drawn positions collapses to one element, so a change in
  its length is not detected (CLAUDE.md says a length change is).

Fixed on 2026-09-30: a collection with no examples at all now exits 2.

## What would unblock it

An allowlist of markers known to have no example, and exit 1 for any other unsourced marker.

## Files

- `scripts/generate_docstrings.py`: `load_collection`, `build_examples`, `fill`, `main`
- `tests/test_docstrings_current.py`
