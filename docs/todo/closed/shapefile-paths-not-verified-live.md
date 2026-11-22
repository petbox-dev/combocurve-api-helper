# Some shapefile paths are not verified live

Closed: 2026-11-22 -- settled by: live dev probe 2026-11-22 of the company zip upload (`scope` required: now refused locally before step 1), the `scope`/`projectIds` PATCH (replaces the list; refusals are per-record 400s), the project-route DELETE of a shared layer (200 `unlinked`, then 202 job for the last project) and failed jobs (`status: failed` with `error`); documented in the docstrings; `tests/test_shapefiles_live.py` has self-cleaning cases, which passed on dev
If this was wrong, you will see: `test_company_upload_scope_patch_and_shared_project_delete` or `test_a_failed_upload_job_raises_with_the_job` failing under `CC_LIVE_TEST=1`, or a shared-layer project DELETE returning a `jobId` instead of `result: "unlinked"`

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

## 2026-11-22: all four paths verified live on dev

Probed by script on dev with `API Helper Fixture <hex>` layers, each deleted in a `finally`; nothing of the
prefix was left at company scope or in any project touched. The dev tenant has nine projects (the note above
that it has one was wrong). No code defect was found; the docstrings now state what follows.

- **Company-route zip upload.** Step 1 answers 201 with `uploadId`, `uploadUrl`, `method`, `headers`,
  `expiresAt`, `maxBytes`. Step 3 without `scope` answers 400 `RequiredFieldError` (`Missing required
  field: scope`); the GeoJSON company create (`POST /shapefiles`) answers the same. With `scope` it answers
  202 `{jobId}`; the job (type `upload`) read `running` nine times, then `successful` with `completedAt` and
  `result.shapefileId`, after about 18 s. The layer read back `scope: company`, `projectIds: []`,
  `description: ""`, `color: "#a0a0a0"`; it was not in the project list of the dev test project. With
  `scope: project` and two `projectIds`, `upload_company_shapefile` created one layer in both projects.
- **PATCH of `scope` / `projectIds`** (207 each; a refusal is a per-record 400 in the body, and the layer
  is unchanged):
  - `scope: project` with two `projectIds` on a company layer: success; readable on both projects'
    routes, 404 `ShapefileNotFoundError` on a third.
  - `projectIds` alone with one id: success; it replaces the list (the dropped project then answers 404).
  - `projectIds: []`: refused, "`projectIds` must be a non-empty array of project ids".
  - `scope: company` with `projectIds`: refused, "`projectIds` cannot be set when `scope` is `company`".
  - `scope: company` alone: success; `projectIds` reads back `[]`.
  - `scope: project` alone on a company layer: refused, "A project layer needs at least one project. To
    remove a layer completely, use DELETE."
- **Project-route DELETE of a shared layer.** Linked to two projects, a DELETE through one project's route
  answered 200 `{"result": "unlinked", "id": ..., "remainingProjectIds": [<the other>]}`. The layer then
  answered 404 on that project's route and 200 on the other's, with `projectIds` of the other only. A DELETE
  through the remaining project's route answered 202 `{jobId}`; the job (type `delete`) went `pending` (8
  reads) -> `running` -> `successful`, and the layer then answered 404 on the company route.
- **Failed job.** The import route accepted (202) every zip whose member names were right; only the job
  reads the files. Job shape: `{"jobId", "type": "upload", "status": "failed", "createdAt", "completedAt",
  "error": <string>}`, no `result`, after about 10 s, and no layer left behind. Errors seen: an all-zero
  `.shp` header and a garbage `.shp`/`.shx` -> `Error uploading to Mapbox: Unknown filetype`; a garbage
  `.prj` -> `Error uploading to Mapbox: Invalid shapefile: invalid projection file`. A `.dbf` whose header
  claims 3 records but holds 1 imported `successful`. `wait_for_company_shapefile_job` returned the
  `failed` job without raising, and `upload_company_shapefile` raised `RuntimeError` with the job (and so
  its `error`) in the message, as documented.

`tests/test_shapefiles_live.py` now has a self-cleaning test for the company upload, the `scope` /
`projectIds` PATCH and the shared-layer project DELETE, and one for the failed upload job (not yet run as
pytest; the probes above ran the same calls).

## Files

`src/combocurve_api_helper/shapefiles.py`, `tests/test_shapefiles_live.py`
