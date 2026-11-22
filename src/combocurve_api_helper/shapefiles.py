import io
import zipfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Optional, Union, cast
from urllib.parse import urlsplit

from ._transport import _send_to_external_url
from .base import APIBase, Item, ItemList, WriteResponse

GET_LIMIT = 200  # the maximum of `take` on the shapefile list and features routes (verified live 2026-11-22)

# The documented upper bound of an upload zip (260 MB). The step-1 ticket carries the same bound as
# `maxBytes` (272629760 bytes, verified live 2026-11-22); the ticket's value wins when it is present.
MAX_UPLOAD_BYTES = 260 * 1024 * 1024

# The `contentType` values step 1 accepts; anything else answers 400 (verified live 2026-11-22).
UPLOAD_CONTENT_TYPES = ('application/zip', 'application/x-zip-compressed')

# The status of a finished good job (`base.RUNNING_JOB_STATUSES` are the unfinished ones). Seen live
# 2026-11-22: an upload job goes `running` -> `successful`, a delete job `pending` -> `running` -> `successful`.
SUCCESSFUL_JOB_STATUS = 'successful'

# A layer record has no `createdAt` / `updatedAt`, so the shared `LIST_SORT_ORDER` would pad those keys
# into every record. Layers are ordered by name, then id.
SHAPEFILE_LIST_SORT_ORDER: Mapping[str, int] = MappingProxyType({'name': 0, 'id': 1})

# Body keys the project routes refuse: the route sets the scope (400 `FieldNameError`, verified live).
_PROJECT_ROUTE_REFUSED_KEYS = ('scope', 'projectIds')


class Shapefiles(APIBase):
    """
    Map layers ("shapefiles"), at company scope (`/shapefiles`) and project scope
    (`/projects/{projectId}/shapefiles`). A layer record carries `id`, `name`, `description`, `color`,
    `scope` (`company` or `project`), `projectIds`, `shapeType` (`POINT`, `POLYGON`, ...), `bbox` and the
    attribute `fields`. Its features are read separately, as GeoJSON in WGS84.

    The company list holds the company layers and every project's layers; a project list holds that
    project's layers only. A layer can be created two ways, both asynchronous (a job to poll):

    - from a GeoJSON FeatureCollection: `post_company_shapefiles` / `post_project_shapefiles`;
    - from a shapefile zip, in three steps: `post_..._shapefile_upload` (a signed upload url),
      `put_shapefile_upload_file` (the zip to that url), `post_..._shapefile_upload_import` (the import).
      `upload_company_shapefile` / `upload_project_shapefile` run all three and wait for the job.

    Every shapefile route is the same at both scopes except PATCH, which is company only. The public
    methods delegate to the private `_...` helpers, which take `project_id=None` for company scope.

    Behavior verified live 2026-11-22 that the API docs do not state: a `name` filter is an exact,
    case-sensitive match; the `jobId` of an import equaled its `uploadId` (the docs say not to rely on
    it, and nothing here does); a polygon ring is stored in the opposite winding order to the one
    sent; layers that came into a project with a project copy read back zero features through the API.
    """

    ######
    # URLs
    ######

    def _shapefiles_url(self, project_id: Optional[str], filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the shapefiles collection url of the company (`project_id` None) or of a project, with
        `filters` as its query string.
        """
        if project_id is None:
            url = f'{self.API_BASE_URL}/shapefiles'
        else:
            url = f'{self.API_BASE_URL}/projects/{project_id}/shapefiles'
        return url + self._build_params_string(filters)

    def _shapefile_url(self, project_id: Optional[str], *segments: str) -> str:
        """Returns the url of `segments` under the shapefiles collection of the company or of a project."""
        return '/'.join([self._shapefiles_url(project_id), *segments])

    def get_company_shapefiles_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the company map layers.
        """
        return self._shapefiles_url(None, filters)

    def get_project_shapefiles_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of a project's map layers.
        """
        return self._shapefiles_url(project_id, filters)

    def get_company_shapefiles_head_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the company `head` sub-route (a GET that answers like a HEAD).
        """
        return self._shapefile_url(None, 'head') + self._build_params_string(filters)

    def get_project_shapefiles_head_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of a project's `head` sub-route (a GET that answers like a HEAD).
        """
        return self._shapefile_url(project_id, 'head') + self._build_params_string(filters)

    def get_company_shapefile_by_id_url(self, shapefile_id: str) -> str:
        """
        Returns the API url of one company-route map layer, from its id.
        """
        return self._shapefile_url(None, shapefile_id)

    def get_project_shapefile_by_id_url(self, project_id: str, shapefile_id: str) -> str:
        """
        Returns the API url of one of a project's map layers, from its id.
        """
        return self._shapefile_url(project_id, shapefile_id)

    def get_company_shapefile_features_url(self, shapefile_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of a map layer's features, on the company route.
        """
        return self._shapefile_url(None, shapefile_id, 'features') + self._build_params_string(filters)

    def get_project_shapefile_features_url(
        self, project_id: str, shapefile_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url of one of a project's map layer features.
        """
        return self._shapefile_url(project_id, shapefile_id, 'features') + self._build_params_string(filters)

    def get_company_shapefile_job_url(self, job_id: str) -> str:
        """
        Returns the API url of a shapefile upload or delete job, on the company route.
        """
        return self._shapefile_url(None, 'jobs', job_id)

    def get_project_shapefile_job_url(self, project_id: str, job_id: str) -> str:
        """
        Returns the API url of a shapefile upload or delete job that touched a project.
        """
        return self._shapefile_url(project_id, 'jobs', job_id)

    def get_company_shapefile_upload_url(self) -> str:
        """
        Returns the API url that starts a company-route shapefile zip upload (step 1).
        """
        return self._shapefile_url(None, 'uploads')

    def get_project_shapefile_upload_url(self, project_id: str) -> str:
        """
        Returns the API url that starts a shapefile zip upload into a project (step 1).
        """
        return self._shapefile_url(project_id, 'uploads')

    def get_company_shapefile_upload_import_url(self, upload_id: str) -> str:
        """
        Returns the API url that imports an uploaded zip on the company route (step 3).
        """
        return self._shapefile_url(None, 'uploads', upload_id)

    def get_project_shapefile_upload_import_url(self, project_id: str, upload_id: str) -> str:
        """
        Returns the API url that imports an uploaded zip into a project (step 3).
        """
        return self._shapefile_url(project_id, 'uploads', upload_id)

    ################
    # Shared helpers
    ################

    @staticmethod
    def _refuse_project_route_keys(data: Item) -> None:
        """Refuse `scope` and `projectIds` on a project route before sending: the route sets them."""
        refused = [key for key in _PROJECT_ROUTE_REFUSED_KEYS if key in data]
        if refused:
            raise ValueError(f'a project route sets the scope; remove {refused} or use the company route')

    def _get_shapefiles(self, project_id: Optional[str], filters: Optional[dict[str, str]]) -> ItemList:
        """Returns every layer of the company or of a project, all pages, ordered by name then id."""
        layers = self._get_items(self._shapefiles_url(project_id, filters), params={'take': GET_LIMIT})
        return self._keysort(layers, SHAPEFILE_LIST_SORT_ORDER)

    def _get_shapefile_features(
        self, project_id: Optional[str], shapefile_id: str, filters: Optional[dict[str, str]]
    ) -> ItemList:
        """Returns a layer's features, all pages, in their stored order."""
        url = self._shapefile_url(project_id, shapefile_id, 'features') + self._build_params_string(filters)
        return self._get_items(url, params={'take': GET_LIMIT})

    def _post_shapefile(self, project_id: Optional[str], data: Item) -> Item:
        """Creates a layer from a GeoJSON FeatureCollection; returns the job (`jobId`)."""
        if project_id is not None:
            self._refuse_project_route_keys(data)
        return self._send_for_item('post', self._shapefiles_url(project_id), data)

    def _post_shapefile_upload(self, project_id: Optional[str], content_type: str) -> Item:
        """Step 1: reserves an upload; returns the ticket (`uploadId`, `uploadUrl`, `method`, `headers`, ...)."""
        if content_type not in UPLOAD_CONTENT_TYPES:
            raise ValueError(f'content_type must be one of {UPLOAD_CONTENT_TYPES}, not {content_type!r}')
        url = self._shapefile_url(project_id, 'uploads')
        return self._send_for_item('post', url, {'contentType': content_type})

    def _post_shapefile_upload_import(self, project_id: Optional[str], upload_id: str, data: Item) -> Item:
        """Step 3: imports an uploaded zip as a layer; returns the job (`jobId`)."""
        if not upload_id:
            raise ValueError('upload_id must be a non-empty upload id')
        if project_id is not None:
            self._refuse_project_route_keys(data)
        return self._send_for_item('post', self._shapefile_url(project_id, 'uploads', upload_id), data)

    def _wait_for_shapefile_job(
        self, project_id: Optional[str], job_id: str, timeout_seconds: float, poll_seconds: float
    ) -> Item:
        """Polls a job until its status is no longer `pending` or `running`; returns the last job read."""
        job_url = self._shapefile_url(project_id, 'jobs', job_id)
        return self._wait_for_job(
            lambda: self._get_items(job_url)[0], timeout_seconds, poll_seconds, f'shapefile job {job_id}'
        )

    def _upload_shapefile(
        self,
        project_id: Optional[str],
        zip_file: Union[str, Path, bytes],
        data: Item,
        timeout_seconds: float,
        poll_seconds: float,
    ) -> Item:
        """Runs the three upload steps, waits for the import job and returns the new layer."""
        content = _read_upload_zip(zip_file)
        if project_id is not None:
            self._refuse_project_route_keys(data)
        ticket = self._post_shapefile_upload(project_id, UPLOAD_CONTENT_TYPES[0])
        self._send_upload_zip(ticket, content)
        job = self._post_shapefile_upload_import(project_id, str(ticket['uploadId']), data)
        finished = self._wait_for_shapefile_job(project_id, str(job['jobId']), timeout_seconds, poll_seconds)
        result = finished.get('result')
        if finished.get('status') != SUCCESSFUL_JOB_STATUS or not isinstance(result, Mapping):
            raise RuntimeError(f'shapefile upload job {job["jobId"]} did not succeed: {finished}')
        shapefile_id = str(result['shapefileId'])
        return self._get_items(self._shapefile_url(project_id, shapefile_id))[0]

    ###########
    # API calls
    ###########

    # Company routes

    def get_company_shapefiles(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the company's map layers: the company layers and every project's layers (heatmap layers
        are not included). Each record lists every project the layer belongs to.

        `filters` take `scope` (`company` or `project`; `project` without `projectId` matches every
        project layer), `projectId` (cannot be combined with `scope=company`: 400), `name` (an exact,
        case-sensitive match), `skip` and `take`. Pages of 200 (the route's maximum `take`) are followed
        to the end. The layers are ordered by name, then id.

        https://docs.api.combocurve.com/api/get-shapefiles

        Example response:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "description": "string",
                "color": "string",
                "scope": "string",
                "projectIds": [
                    "string"
                ],
                "shapeType": "string",
                "bbox": [
                    123.45
                ],
                "fields": [
                    {
                        "name": "Example",
                        "fieldType": "string"
                    }
                ]
            }
        ]
        """
        return self._get_shapefiles(None, filters)

    def count_company_shapefiles(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of company map layers (company layers and every project's) matching `filters`,
        from the `X-Query-Count` header of a HEAD request. Takes the same filters as
        `get_company_shapefiles`.

        https://docs.api.combocurve.com/api/head-shapefiles
        """
        return self._count_items(self.get_company_shapefiles_url(filters))

    def count_company_shapefiles_with_get(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Same as `count_company_shapefiles`, through the `GET /v1/shapefiles/head` sub-route, for a client
        that cannot send HEAD. The count is the `X-Query-Count` header; the response has no body.

        https://docs.api.combocurve.com/api/get-head-shapefiles
        """
        return self._count_items(self.get_company_shapefiles_head_url(filters), method='get')

    def get_company_shapefile_by_id(self, shapefile_id: str) -> Item:
        """
        Returns a map layer's metadata from its id, whatever its scope. An unknown id answers 404
        (`ShapefileNotFoundError`).

        https://docs.api.combocurve.com/api/get-shapefile-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "description": "string",
            "color": "string",
            "scope": "string",
            "projectIds": [
                "string"
            ],
            "shapeType": "string",
            "bbox": [
                123.45
            ],
            "fields": [
                {
                    "name": "Example",
                    "fieldType": "string"
                }
            ]
        }
        """
        return self._get_items(self.get_company_shapefile_by_id_url(shapefile_id))[0]

    def get_company_shapefile_features(self, shapefile_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a layer's features as GeoJSON Features (WGS84), in their original order. A zip upload reads
        back as reprojected GeoJSON, not the original files. Pages of 200 (the route's maximum `take`) are
        followed to the end; pass `skip` / `take` in `filters` to start later or page differently.

        A polygon ring reads back in the opposite winding order to the one written. A layer that came into
        a project with a project copy reads back no features (verified live 2026-11-22).

        https://docs.api.combocurve.com/api/get-shapefile-features

        Example response:
        [
            {
                "type": "string",
                "geometry": {},
                "properties": {}
            }
        ]
        """
        return self._get_shapefile_features(None, shapefile_id, filters)

    def get_company_shapefile_job(self, job_id: str) -> Item:
        """
        Returns the status of a shapefile upload or delete job, at either scope. `status` is `pending`,
        `running` or `successful` (seen live); a successful upload's `result` has the new layer's
        `shapefileId`, and a failed job has `error`. An unknown id answers 404.

        https://docs.api.combocurve.com/api/get-shapefiles-job

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691",
            "type": "string",
            "status": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "completedAt": "2020-01-01T00:00:00.000Z",
            "result": {
                "shapefileId": "5e272d38b78910dd2a1bd691"
            },
            "error": "string"
        }
        """
        return self._get_items(self.get_company_shapefile_job_url(job_id))[0]

    def wait_for_company_shapefile_job(
        self, job_id: str, timeout_seconds: float = 600.0, poll_seconds: float = 2.0
    ) -> Item:
        """
        Polls `get_company_shapefile_job` every `poll_seconds` until the job is no longer `pending` or
        `running`, and returns it; check its `status`. Raises `TimeoutError` when it has not finished
        within `timeout_seconds`. An upload of a small layer took about 20 seconds (live 2026-11-22).
        Not an API route: it calls the job route repeatedly.
        """
        return self._wait_for_shapefile_job(None, job_id, timeout_seconds, poll_seconds)

    def delete_company_shapefile_by_id(self, shapefile_id: str) -> Item:
        """
        Deletes a map layer everywhere, whatever its scope or projects, asynchronously. Users' map settings
        drop the layer; inventory plans that use it as a DSU keep a reference to it. Returns the job
        (`jobId`); poll it with `get_company_shapefile_job` or `wait_for_company_shapefile_job`.

        https://docs.api.combocurve.com/api/delete-shapefile-by-id

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._send_for_item('delete', self.get_company_shapefile_by_id_url(shapefile_id))

    def patch_company_shapefiles(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Updates layer metadata: `name`, `description`, `color`, `scope` and `projectIds`, by `id`. This is
        how a layer is shared with more projects or removed from some; it exists on the company route only.
        `data` is one record or a list of them, sent in one request; the response is 207 Multi-Status with
        a result per record.

        Every record must carry an `id`, and an id may appear once: the API rejects a later record for a
        layer already in the request (a per-record 400, verified live), so a repeated id raises
        `ValueError` here before anything is sent.

        https://docs.api.combocurve.com/api/patch-shapefiles

        Example data:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "description": "string",
                "color": "string",
                "scope": "string",
                "projectIds": [
                    "string"
                ]
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "id": "5e272d38b78910dd2a1bd691",
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
        """
        records = self._records_from(data, 'layer record')
        ids = [record.get('id') for record in records]
        if not all(ids):
            raise ValueError('every layer record must carry an `id`')
        repeated = sorted(str(layer_id) for layer_id, count in Counter(map(str, ids)).items() if count > 1)
        if repeated:
            raise ValueError(f'send one record per layer; repeated ids: {repeated}')
        return cast('list[WriteResponse]', self._patch_items(self.get_company_shapefiles_url(), records))

    def post_company_shapefiles(self, data: Item) -> Item:
        """
        Creates a map layer from a GeoJSON FeatureCollection (`name`, `type`, `features`, optional
        `description`, `color`, `scope`, `projectIds`), asynchronously: the features are converted to a
        shapefile and imported like an uploaded zip. Returns the job (`jobId`); poll it with
        `get_company_shapefile_job` or `wait_for_company_shapefile_job`.

        A name already in use where the layer would appear answers 409 with the existing layer's id as
        `conflictingId` in the error details; a clash with a heatmap layer answers 409 without it.

        https://docs.api.combocurve.com/api/post-shapefiles

        Example data:
        {
            "name": "Example",
            "type": "string",
            "features": [
                {
                    "type": "string",
                    "geometry": {},
                    "properties": {}
                }
            ],
            "description": "string",
            "color": "string",
            "scope": "string",
            "projectIds": [
                "string"
            ]
        }

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._post_shapefile(None, data)

    def post_company_shapefile_upload(self, content_type: str = 'application/zip') -> Item:
        """
        Step 1 of uploading a shapefile zip: returns the ticket, with `uploadId`, the signed `uploadUrl`
        (on Google Cloud Storage, not api.combocurve.com) and the `method` and `headers` to send the zip
        with (step 2, `put_shapefile_upload_file`), `expiresAt` (30 minutes) and `maxBytes` (260 MB). Import
        the upload within 24 hours (step 3, `post_company_shapefile_upload_import`); an upload never
        imported is deleted. An upload reserved here can be imported only through the company route.

        `content_type` is `application/zip` or `application/x-zip-compressed`; any other value raises
        `ValueError` before sending (the API answers 400).

        https://docs.api.combocurve.com/api/post-shapefiles-upload

        Example data:
        {
            "contentType": "string"
        }

        Example response:
        {
            "uploadId": "5e272d38b78910dd2a1bd691",
            "uploadUrl": "string",
            "method": "string",
            "headers": {},
            "expiresAt": "2020-01-01T00:00:00.000Z",
            "maxBytes": 123
        }
        """
        return self._post_shapefile_upload(None, content_type)

    def post_company_shapefile_upload_import(self, upload_id: str, data: Item) -> Item:
        """
        Step 3: imports an uploaded zip as a map layer, asynchronously. `data` takes `name`, `description`,
        `color`, `scope` and `projectIds`. The zip is checked first (400 if it is not a shapefile zip).
        Returns the job (`jobId`); poll that id, not the upload id.

        An upload is imported once: a repeat answers 409 with the original `jobId` in the error details. An
        upload reserved through a project route answers 404 here (verified live).

        https://docs.api.combocurve.com/api/post-shapefiles-upload-import

        Example data:
        {
            "name": "Example",
            "description": "string",
            "color": "string",
            "scope": "string",
            "projectIds": [
                "string"
            ]
        }

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._post_shapefile_upload_import(None, upload_id, data)

    def upload_company_shapefile(
        self,
        zip_file: Union[str, Path, bytes],
        data: Item,
        timeout_seconds: float = 600.0,
        poll_seconds: float = 2.0,
    ) -> Item:
        """
        Uploads a shapefile zip as a map layer on the company route and returns the new layer's metadata.
        `zip_file` is the zip's path or its bytes; `data` is the step-3 body (`name`, `description`,
        `color`, `scope`, `projectIds`).

        Runs `post_company_shapefile_upload`, `put_shapefile_upload_file`,
        `post_company_shapefile_upload_import` and `wait_for_company_shapefile_job`, then reads the layer.
        The zip is checked (one `.shp` with its `.shx` and `.dbf`, at most 260 MB) before anything is
        sent. Raises `RuntimeError` when the job ends in any status but `successful`, and `TimeoutError`
        when it has not ended within `timeout_seconds`.
        """
        return self._upload_shapefile(None, zip_file, data, timeout_seconds, poll_seconds)

    # Signed upload (either scope)

    def put_shapefile_upload_file(self, upload: Item, zip_file: Union[str, Path, bytes]) -> None:
        """
        Step 2 of a shapefile zip upload: sends the zip to the signed `uploadUrl` of a step-1 ticket
        (`post_company_shapefile_upload` or `post_project_shapefile_upload`), with the ticket's `method`
        and `headers`. `zip_file` is the zip's path or its bytes.

        The signed url is on Google Cloud Storage, not api.combocurve.com, so the request carries only
        the ticket's headers: never the ComboCurve API key or bearer token. A url that is not https raises
        `ValueError`. The zip is checked before it is sent: it must be a zip holding exactly one `.shp`,
        with the `.shx` and `.dbf` of the same name, and be at most the ticket's `maxBytes` (260 MB);
        otherwise `ValueError`.

        The request has the package's timeout and connection-failure policy: it is sent again only when it
        never reached the storage host (connect timeout, refused connection, DNS failure); a PUT whose
        connection failed after it was sent raises, because the zip may have been stored. No status is
        retried: an error status raises `requests.HTTPError`.
        """
        self._send_upload_zip(upload, _read_upload_zip(zip_file))

    @staticmethod
    def _send_upload_zip(upload: Item, content: bytes) -> None:
        """Sends `content`, a zip already checked by `_read_upload_zip`, to the ticket's signed url (the
        body of `put_shapefile_upload_file`, which documents it). Refuses a url that is not https and a zip
        larger than the ticket's `maxBytes`."""
        upload_url = str(upload.get('uploadUrl') or '')
        if urlsplit(upload_url).scheme != 'https':
            raise ValueError('the upload ticket must carry an https `uploadUrl`')
        max_bytes = upload.get('maxBytes')
        limit = max_bytes if isinstance(max_bytes, int) and not isinstance(max_bytes, bool) else MAX_UPLOAD_BYTES
        if len(content) > limit:
            raise ValueError(f'the zip is {len(content)} bytes; the upload takes at most {limit}')
        ticket_headers = upload.get('headers')
        headers = (
            {str(key): str(value) for key, value in ticket_headers.items()}
            if isinstance(ticket_headers, Mapping)
            else {'Content-Type': UPLOAD_CONTENT_TYPES[0]}
        )
        method = str(upload.get('method') or 'PUT')
        response = _send_to_external_url(method, upload_url, headers, content)
        response.raise_for_status()

    # Project routes

    def get_project_shapefiles(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a project's map layers, including layers shared with other projects. Company layers are not
        included; read them with `get_company_shapefiles({'scope': 'company'})`.

        `filters` take `name` (an exact, case-sensitive match), `skip` and `take`. Pages of 200 (the route's
        maximum `take`) are followed to the end. The layers are ordered by name, then id.

        https://docs.api.combocurve.com/api/get-project-shapefiles

        Example response:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "description": "string",
                "color": "string",
                "scope": "string",
                "projectIds": [
                    "string"
                ],
                "shapeType": "string",
                "bbox": [
                    123.45
                ],
                "fields": [
                    {
                        "name": "Example",
                        "fieldType": "string"
                    }
                ]
            }
        ]
        """
        return self._get_shapefiles(project_id, filters)

    def count_project_shapefiles(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of a project's map layers matching `filters`, from the `X-Query-Count` header of
        a HEAD request.

        https://docs.api.combocurve.com/api/head-project-shapefiles
        """
        return self._count_items(self.get_project_shapefiles_url(project_id, filters))

    def count_project_shapefiles_with_get(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Same as `count_project_shapefiles`, through the `GET .../shapefiles/head` sub-route, for a client
        that cannot send HEAD. The count is the `X-Query-Count` header; the response has no body.

        https://docs.api.combocurve.com/api/get-head-project-shapefiles
        """
        return self._count_items(self.get_project_shapefiles_head_url(project_id, filters), method='get')

    def get_project_shapefile_by_id(self, project_id: str, shapefile_id: str) -> Item:
        """
        Returns one of a project's map layers from its id. An unknown id answers 404.

        https://docs.api.combocurve.com/api/get-project-shapefile-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "description": "string",
            "color": "string",
            "scope": "string",
            "projectIds": [
                "string"
            ],
            "shapeType": "string",
            "bbox": [
                123.45
            ],
            "fields": [
                {
                    "name": "Example",
                    "fieldType": "string"
                }
            ]
        }
        """
        return self._get_items(self.get_project_shapefile_by_id_url(project_id, shapefile_id))[0]

    def get_project_shapefile_features(
        self, project_id: str, shapefile_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns one of a project's layer features as GeoJSON Features (WGS84), in their original order.
        Pages of 200 (the route's maximum `take`) are followed to the end; see
        `get_company_shapefile_features` for the behaviors seen live.

        https://docs.api.combocurve.com/api/get-project-shapefile-features

        Example response:
        [
            {
                "type": "string",
                "geometry": {},
                "properties": {}
            }
        ]
        """
        return self._get_shapefile_features(project_id, shapefile_id, filters)

    def get_project_shapefile_job(self, project_id: str, job_id: str) -> Item:
        """
        Returns the status of a shapefile upload or delete job that touched this project. See
        `get_company_shapefile_job` for the statuses.

        https://docs.api.combocurve.com/api/get-project-shapefiles-job

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691",
            "type": "string",
            "status": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "completedAt": "2020-01-01T00:00:00.000Z",
            "result": {
                "shapefileId": "5e272d38b78910dd2a1bd691"
            },
            "error": "string"
        }
        """
        return self._get_items(self.get_project_shapefile_job_url(project_id, job_id))[0]

    def wait_for_project_shapefile_job(
        self, project_id: str, job_id: str, timeout_seconds: float = 600.0, poll_seconds: float = 2.0
    ) -> Item:
        """
        Polls `get_project_shapefile_job` every `poll_seconds` until the job is no longer `pending` or
        `running`, and returns it; check its `status`. Raises `TimeoutError` when it has not finished
        within `timeout_seconds`. Not an API route: it calls the job route repeatedly.
        """
        return self._wait_for_shapefile_job(project_id, job_id, timeout_seconds, poll_seconds)

    def delete_project_shapefile_by_id(self, project_id: str, shapefile_id: str) -> Item:
        """
        Removes a layer from this project. A layer other projects also use is only unlinked from this one:
        the response (200) has `id`, `result` and `remainingProjectIds`. A layer whose last project is this
        one is deleted asynchronously: the response (202) has `jobId`; poll it with
        `get_project_shapefile_job` or `wait_for_project_shapefile_job`.

        https://docs.api.combocurve.com/api/delete-project-shapefile-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "result": "string",
            "remainingProjectIds": [
                "string"
            ]
        }
        """
        return self._send_for_item('delete', self.get_project_shapefile_by_id_url(project_id, shapefile_id))

    def post_project_shapefiles(self, project_id: str, data: Item) -> Item:
        """
        Creates a map layer in this project from a GeoJSON FeatureCollection (`name`, `type`, `features`,
        optional `description` and `color`), asynchronously. Returns the job (`jobId`). Same as
        `post_company_shapefiles`, without `scope` or `projectIds`: either key raises `ValueError` before
        sending. A name already used in this project or by a company layer answers 409.

        https://docs.api.combocurve.com/api/post-project-shapefiles

        Example data:
        {
            "name": "Example",
            "type": "string",
            "features": [
                {
                    "type": "string",
                    "geometry": {},
                    "properties": {}
                }
            ],
            "description": "string",
            "color": "string",
            "scope": "string",
            "projectIds": [
                "string"
            ]
        }

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._post_shapefile(project_id, data)

    def post_project_shapefile_upload(self, project_id: str, content_type: str = 'application/zip') -> Item:
        """
        Step 1 of uploading a shapefile zip into this project. Same as `post_company_shapefile_upload`,
        except that the upload can be imported only through this project's route.

        https://docs.api.combocurve.com/api/post-project-shapefiles-upload

        Example data:
        {
            "contentType": "string"
        }

        Example response:
        {
            "uploadId": "5e272d38b78910dd2a1bd691",
            "uploadUrl": "string",
            "method": "string",
            "headers": {},
            "expiresAt": "2020-01-01T00:00:00.000Z",
            "maxBytes": 123
        }
        """
        return self._post_shapefile_upload(project_id, content_type)

    def post_project_shapefile_upload_import(self, project_id: str, upload_id: str, data: Item) -> Item:
        """
        Step 3, into this project. Same as `post_company_shapefile_upload_import`; `data` takes `name`,
        `description` and `color`. `scope` or `projectIds` raises `ValueError` before sending (the API
        answers 400 `FieldNameError`, verified live).

        https://docs.api.combocurve.com/api/post-project-shapefiles-upload-import

        Example data:
        {
            "name": "Example",
            "description": "string",
            "color": "string",
            "scope": "string",
            "projectIds": [
                "string"
            ]
        }

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._post_shapefile_upload_import(project_id, upload_id, data)

    def upload_project_shapefile(
        self,
        project_id: str,
        zip_file: Union[str, Path, bytes],
        data: Item,
        timeout_seconds: float = 600.0,
        poll_seconds: float = 2.0,
    ) -> Item:
        """
        Uploads a shapefile zip as a map layer in this project and returns the new layer's metadata.
        `data` is the step-3 body (`name`, `description`, `color`; `scope` or `projectIds` raises
        `ValueError`). Same steps and checks as `upload_company_shapefile`, on the project routes.
        """
        return self._upload_shapefile(project_id, zip_file, data, timeout_seconds, poll_seconds)


def _read_upload_zip(zip_file: Union[str, Path, bytes]) -> bytes:
    """Returns the zip's bytes (read from a path, or as given), after checking that it holds one shapefile.

    The upload route takes a zip of exactly one shapefile: `.shp`, `.shx` and `.dbf` with one name
    (optionally `.prj` and other sidecars). Checked here so that a bad zip is refused before a ticket is
    reserved or anything is uploaded.

    macOS metadata is ignored in the count and the check: members under `__MACOSX/` and members whose
    name starts with `._` (AppleDouble resource forks, which Finder's "Compress" adds, such as
    `__MACOSX/._layer.shp`). They stay in the bytes sent. Whether the server accepts a zip that holds
    them is not verified.
    """
    content = zip_file if isinstance(zip_file, bytes) else Path(zip_file).read_bytes()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f'the zip is {len(content)} bytes; the upload takes at most {MAX_UPLOAD_BYTES}')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            members = [
                PurePosixPath(name)
                for name in archive.namelist()
                if not name.endswith('/') and not _is_macos_metadata(PurePosixPath(name))
            ]
    except zipfile.BadZipFile as error:
        raise ValueError('zip_file is not a zip archive') from error
    shapes = [member for member in members if member.suffix.lower() == '.shp']
    if len(shapes) != 1:
        raise ValueError(f'the zip must hold exactly one .shp file; it holds {len(shapes)}')
    stem = shapes[0].with_suffix('')
    present = {(member.parent, member.stem.lower(), member.suffix.lower()) for member in members}
    missing = [suffix for suffix in ('.shx', '.dbf') if (stem.parent, stem.name.lower(), suffix) not in present]
    if missing:
        raise ValueError(f'the zip is missing {missing} for {shapes[0]}')
    return content


def _is_macos_metadata(member: PurePosixPath) -> bool:
    """True for a member that macOS adds to a zip: under a `__MACOSX` folder, or an AppleDouble `._` file."""
    return member.parts[0] == '__MACOSX' or member.name.startswith('._')
