# v1 type-curve normalizations are not written to v2

Closed: 2026-11-21 -- settled by: won't do (maintainer decision 2026-11-21): the v1 routes are retired, so a v1 definition can no longer be read to pair with its migrated v2 normalization; a read-only scan of all 526 production type curves found 12 (2.3%) with migrated `linear`, `power_law_fit` or `eur_and_peak` normalizations and no v1 record of them anywhere; the v1 write wrappers keep dropping `normalizations`, as their docstrings say, and callers use `put_type_curve_normalization`
If this was wrong, you will see: a caller relying on the deprecated v1 wrappers to write a `linear`, `power_law_fit` or `eur_and_q_peak` normalization and finding none written

Severity: low
Opened: 2026-11-05
Updated: 2026-11-21 (read-only production scan)

## What happens now

The deprecated write wrappers (`put_type_curves`, and `post_type_curves` with v1 fields) drop the v1
`normalizations` field. A record that carries only `normalizations` takes the deprecated path and
writes no normalization. The caller must use `put_type_curve_normalization`.

## What is known

The migration mapping is known for two v1 shapes only: `1_to_1` and no normalization.

The v1 record (from the retired v1 schema) was per phase:
`{normalizationType: 'eur' | 'eur_and_q_peak', perfLateralLength, eur: {type, slope, intercept,
coefficient, exponent, base, selectedNumericalTarget, target: {...}}, ...}`, with `type` one of
`no_normalization`, `1_to_1`, `linear`, `power_law_fit`.

### Migrated v2 normalizations in production (read 2026-11-21)

All 526 type curves in 215 projects were read with `get_type_curve_normalization` (GET only). Every
segment has `xStart: 0`, and every phase has exactly zero or one segment per factor.

Per type curve (phase combination):

| Count | v2 segments present (any phase) | `yAxis` | Other |
|---|---|---|---|
| 412 | `eur` `1_to_1` | `eur` | |
| 67 | `eur` `1_to_1` | `eur` | `linkedTo` on some phases |
| 32 | none | `eur` | |
| 2 | none | `eur` | `linkedTo` |
| 5 | `eur` `linear` | `eur` | |
| 1 | `eur` `linear` | `eur` | `linkedTo` |
| 3 | `eur` `power_law_fit` | `eur` | |
| 1 | `eur` `linear` and `eur` `power_law_fit` (different phases) | `eur` | |
| 1 | `eur` `1_to_1` / `linear`, `peak` `linear` | `eur_and_peak` (all phases) | |
| 1 | `eur` `1_to_1` | `eur` | `customBasisKey` (`xAxis` is a ratio, e.g. proppant / lateral length) |
| 1 | empty body `{}` (no phase keys) | | |

Per segment: `eur` `1_to_1` 1,065; `eur` `linear` 14; `eur` `power_law_fit` 11; `peak` `linear` 3.

Shapes of the non-`1_to_1` segments:

- `linear`: `{xStart, fitType: 'linear', aValue, bValue}`. On `eur`, `aValue` ranges about -78 to
  2,830 (most 27 to 330, a per-foot magnitude) and `bValue` about -6.9e6 to 3.9e6 (an offset); one is
  `aValue 1, bValue 0`. On `peak`, `aValue` 0.11 to 0.17 and `bValue` 18 to 1,907. This reads as
  `y = aValue * x + bValue`, i.e. v1 `slope` -> `aValue`, `intercept` -> `bValue`: an interpretation from
  magnitudes, not a verified pair.
- `power_law_fit`: `{xStart, fitType: 'power_law_fit', aValue, bValue}`. `bValue` is 0.34 to 1.75 and
  `aValue` 0.4 to 36,000 on 8 of the 11 (reads as `y = aValue * x ** bValue`, v1 `coefficient` ->
  `aValue`, `exponent` -> `bValue`); 3 of the 11 are `aValue 1, bValue 0`, which may be a default the
  migration wrote when v1 had no fitted coefficients (unverified).
- v1 `eur_and_q_peak` appears as `yAxis: 'eur_and_peak'` on every phase, with a `peak` block of
  segments next to `eur`. One type curve only.
- `targets` is `[{key: 'perf_lateral_length', value}]` (or the `customBasisKey` ratio key) when a
  segment exists, `[]` when none.

Also observed: `1_to_1` segments came back as `{xStart, fitType}` only (0 of 1,065 carried
`aValue`/`bValue`). The 2026-11-05 note that GET returns `aValue 1, bValue 0` on `1_to_1` no longer
holds for this tenant; `normalization_for_put` still removes them if present.

## What is unverified

How ComboCurve mapped each v1 field to v2 for `linear`, `power_law_fit` and `eur_and_q_peak`: which
v1 coefficient became `aValue` and which `bValue`, whether any unit or base conversion was applied
(v1 `base` values such as `eur_pll` or a `fluid/pll` composite versus v2 `xAxis` / `yAxis` /
`customBasisKey`), and what `selectedNumericalTarget` / `target` became. The v1 definitions of these
type curves can no longer be read from the API, and no local copy of a v1 normalization with real
values was found (searched `~/Projects` and session transcripts for `power_law_fit` and
`eur_and_q_peak`: only spoofed docstring examples). Without a v1/v2 pair per type, a mapping would be a
guess.

## What would unblock it

A v1 definition (a pre-migration export, backup or log of a `GET /type-curves` body) of any type curve
that now has a `linear`, `power_law_fit` or `eur_and_peak` normalization, compared with its v2
`get_type_curve_normalization`. Or a statement of the mapping from ComboCurve. Then add the mapping to
`type_curve_conversions.py` and write it from the wrappers.

Alternative: since v1 write routes are retired and v1 writers must already change, close this as
"won't do" and keep the wrappers documented as dropping `normalizations`.

## Files

`src/combocurve_api_helper/type_curves_v1_compatibility.py`, `src/combocurve_api_helper/type_curve_conversions.py`
