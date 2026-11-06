# Type-curve v1 wrappers outlive the v1 API

Severity: low
Opened: 2026-11-05

## What happens now

ComboCurve stopped the v1 type-curve routes on 2026-11-07. `type_curves_v1_compatibility.py`
(`TypeCurvesV1Compatibility`) keeps the v1-shaped methods working on the v2 routes, each with a
`DeprecationWarning`. The warning text promises removal in a 3.x release, not before 2027-01-31.

## What is committed

The module stays until at least 2027-01-31. After that date the module is dead weight and the
promise in the warning text is the only reason it remains.

## To remove

1. Delete `src/combocurve_api_helper/type_curves_v1_compatibility.py` and `tests/type_curves/test_v1_compatibility.py`.
2. In `__init__.py`, list `TypeCurves` in the `ComboCurveAPI` bases instead of `TypeCurvesV1Compatibility`.
3. Drop the re-exports in `__init__.py` that only the wrappers need (`fits_from_v1`, `fits_to_v1`,
   `type_curve_to_v1`, `volumes_to_v1`, `lookup_table_from_v1`, `lookup_table_to_v1`,
   `lookup_table_id_from_v1`, `representative_well_from_v2`), and the conversions nothing else uses.
4. Add a CHANGELOG "Removed" entry. Update the README "Type curves (v2)" section and the CLAUDE.md paragraph.

## Files

`src/combocurve_api_helper/type_curves_v1_compatibility.py`, `src/combocurve_api_helper/type_curve_conversions.py`
