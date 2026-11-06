# v1 type-curve normalizations are not written to v2

Severity: low
Opened: 2026-11-05

## What happens now

The deprecated write wrappers (`put_type_curves`, and `post_type_curves` with v1 fields) drop the v1
`normalizations` field. A record that carries only `normalizations` takes the deprecated path and
writes no normalization. The caller must use `put_type_curve_normalization`.

## What is known

The migration mapping is known for two v1 shapes only: `1_to_1` and no normalization.

## What is unverified

How ComboCurve migrated the v1 normalization types `linear`, `power_law_fit` and `eur_and_q_peak`.
No migrated example of these was seen. A mapping written without an example would be a guess.

## What would unblock it

A tenant with a migrated type curve of each type. Read it with `get_type_curve_normalization`, compare
it with the v1 definition, then add the mapping to `type_curve_conversions.py` and write it from the wrappers.

## Files

`src/combocurve_api_helper/type_curves_v1_compatibility.py`, `src/combocurve_api_helper/type_curve_conversions.py`
