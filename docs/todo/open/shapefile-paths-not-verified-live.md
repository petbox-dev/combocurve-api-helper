# Some shapefile paths are not verified live

Severity: low
Opened: 2026-11-21

## What happens now

`shapefiles.py` wraps all 21 shapefile operations. A live dev round trip passed at both scopes on
2026-11-21-22: project-scope zip upload (three steps), job wait, read-back, PATCH, GeoJSON create, and
deletes through both delete routes. Not exercised live:

- the company-route zip upload and import;
- a PATCH of `scope` or `projectIds`;
- a project-route DELETE of a layer shared with another project (documented to answer 200 and unlink);
  dev has one project to test with;
- the shape of a failed job (no failure was seen).

## What would unblock it

A second dev project for the unlink case, and a fixture zip the server rejects for the failed-job shape.
Extend `tests/test_shapefiles_live.py`.

## Files

`src/combocurve_api_helper/shapefiles.py`, `tests/test_shapefiles_live.py`
