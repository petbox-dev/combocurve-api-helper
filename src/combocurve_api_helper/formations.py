from typing import Optional, Union, cast

from requests.structures import CaseInsensitiveDict

from .base import JOB_POLL_SECONDS, JOB_WAIT_TIMEOUT_SECONDS, LIST_SORT_ORDER, APIBase, Item, ItemList, WriteResponse

GET_LIMIT = 200  # the maximum of `take` on the formations list routes (verified live 2026-11-21)
POINTS_GET_LIMIT = 10000  # the maximum of `take` on the formation points routes (verified live 2026-11-21)

OVERLAP_HANDLING_VALUES = ('trim', 'keep')


class Formations(APIBase):
    """
    Formations: named geological surfaces, each a set of points (`latitude`, `longitude`, `topTvd`
    and an optional `baseTvd`, in feet true vertical depth). A formation is company-scoped
    (`/formations`) or project-scoped (`/projects/{projectId}/formations`). Its summary carries `id`,
    `name`, `color`, `enabled`, `scope`, `projectId` (`null` for a company formation), `maxDepth`,
    `maxThickness`, `bbox` (`[minLongitude, minLatitude, maxLongitude, maxLatitude]`), `pointCount`,
    `createdAt` and `updatedAt`. The points are read separately (`get_*_formation_points`).

    A formation is created or replaced by name with an asynchronous import: `put_*_formations`
    returns `{"jobId": ...}` at once (202), and the import runs after. Poll
    `get_company_formations_job` / `get_project_formations_job` with that id until `status` leaves
    `pending` and `running` (`wait_for_company_formations_job` / `wait_for_project_formations_job` do
    that); the final status of a good import is `successful`, a few seconds after the PUT (verified
    live 2026-11-21). There is no POST. A replace keeps the
    formation's `id`, `enabled`, `maxDepth` and `maxThickness`; the PUT cannot set those three, so set
    them with `patch_*_formations` (by `id`) once the job has succeeded.

    The two scopes are not symmetric (verified live 2026-11-21):

    - The company list and count (`get_company_formations`, `count_company_formations`) cover every
      formation in the company, company and project scope alike; pass `{'scope': 'company'}` for the
      company ones only. The project routes cover only that project's formations.
    - `get_company_formation_by_id`, `get_company_formation_points`, `patch_company_formations` and
      `get_company_formations_job` also reach project formations and project import jobs.
    - `delete_company_formation_by_id` deletes only a company formation: a project formation's id
      answers 404 there. The project routes answer 404 (per record, for PATCH) for a company formation.

    Both scopes share one set of private helpers below, keyed by `project_id` (`None` for the company
    routes).
    """

    ######
    # URLs
    ######

    def _formations_base_url(self, project_id: Optional[str]) -> str:
        """Returns the formations collection url of the company (`project_id` None) or of a project."""
        if project_id is None:
            return f'{self.API_BASE_URL}/formations'
        return f'{self.API_BASE_URL}/projects/{project_id}/formations'

    def _formations_url(
        self, project_id: Optional[str], suffix: str = '', filters: Optional[dict[str, str]] = None
    ) -> str:
        """Returns the formations url of a scope with `suffix` (`/head`, `/{id}`, ...) and `filters` as its
        query string."""
        url = self._formations_base_url(project_id) + suffix
        if filters is None:
            return url
        return url + self._build_params_string(filters)

    def get_company_formations_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the company formations (the company list holds every formation).
        """
        return self._formations_url(None, filters=filters)

    def get_company_formations_head_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the GET twin of the company formations HEAD route (`/formations/head`).
        """
        return self._formations_url(None, '/head', filters)

    def get_company_formations_job_url(self, job_id: str) -> str:
        """
        Returns the API url of a company formations import job, from its job id.
        """
        return self._formations_url(None, f'/jobs/{job_id}')

    def get_company_formation_by_id_url(self, formation_id: str) -> str:
        """
        Returns the API url of one formation, from its id.
        """
        return self._formations_url(None, f'/{formation_id}')

    def get_company_formation_points_url(self, formation_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the points of one formation, from its id.
        """
        return self._formations_url(None, f'/{formation_id}/points', filters)

    def get_project_formations_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the formations of a project.
        """
        return self._formations_url(project_id, filters=filters)

    def get_project_formations_head_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the GET twin of the project formations HEAD route
        (`/projects/{projectId}/formations/head`).
        """
        return self._formations_url(project_id, '/head', filters)

    def get_project_formations_job_url(self, project_id: str, job_id: str) -> str:
        """
        Returns the API url of a project formations import job, from its job id.
        """
        return self._formations_url(project_id, f'/jobs/{job_id}')

    def get_project_formation_by_id_url(self, project_id: str, formation_id: str) -> str:
        """
        Returns the API url of one formation of a project, from its id.
        """
        return self._formations_url(project_id, f'/{formation_id}')

    def get_project_formation_points_url(
        self, project_id: str, formation_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url of the points of one formation of a project, from its id.
        """
        return self._formations_url(project_id, f'/{formation_id}/points', filters)

    ###########
    # Shared helpers
    ###########

    def _get_formations(self, project_id: Optional[str], filters: Optional[dict[str, str]]) -> ItemList:
        """Returns the formation summaries of a scope, every page, with the shared list ordering."""
        url = self._formations_url(project_id, filters=filters)
        return self._keysort(self._get_items(url, params={'take': GET_LIMIT}), LIST_SORT_ORDER)

    def _get_formation_points(
        self, project_id: Optional[str], formation_id: str, filters: Optional[dict[str, str]]
    ) -> ItemList:
        """Returns every point of one formation, in stored order (not sorted), following every page."""
        url = self._formations_url(project_id, f'/{formation_id}/points', filters)
        return self._get_items(url, params={'take': POINTS_GET_LIMIT})

    def _put_formations(
        self, project_id: Optional[str], data: Union[Item, ItemList], overlap_handling: Optional[str]
    ) -> Item:
        """Starts one import of `data` into a scope and returns `{"jobId": ...}`. The whole list goes in one
        request (one job): it is not split into chunks."""
        if overlap_handling is not None and overlap_handling not in OVERLAP_HANDLING_VALUES:
            raise ValueError(f'overlap_handling must be one of {OVERLAP_HANDLING_VALUES}, not {overlap_handling!r}')
        records = self._records_from(data, 'formation')
        url = self._formations_url(
            project_id, filters=None if overlap_handling is None else {'overlapHandling': overlap_handling}
        )
        return self._put_items(url, records)[0]

    def _patch_formations(self, project_id: Optional[str], data: Union[Item, ItemList]) -> list[WriteResponse]:
        """Updates formation metadata of a scope by `id`; returns the 207 envelope."""
        records = self._records_from(data, 'formation')
        return cast('list[WriteResponse]', self._patch_items(self._formations_url(project_id), records))

    ###########
    # API calls
    ###########

    # Company formations

    def get_company_formations(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the formation summaries of the whole company: the company formations and every project's.
        Each summary carries `scope` and `projectId`. `filters` take `scope` (`company` or `project`),
        `projectId` (not with `scope=company`: 400), `name` (exact match), `skip` and `take`. Points are not
        included. Pages of 200 (the route's maximum `take`; its default is 25) are followed to the end and
        sorted by name.

        https://docs.api.combocurve.com/api/get-formations

        Example response:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "color": "string",
                "enabled": true,
                "scope": "string",
                "projectId": "5e272d38b78910dd2a1bd691",
                "maxDepth": 123.45,
                "maxThickness": 123.45,
                "bbox": [
                    123.45
                ],
                "pointCount": 123,
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z"
            }
        ]
        """
        return self._get_formations(None, filters)

    def count_company_formations(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of formations in the company (company and project scope) matching `filters`, from
        the `X-Query-Count` header of a HEAD request (no summaries are fetched). Same filters as
        `get_company_formations`.

        https://docs.api.combocurve.com/api/head-formations
        """
        return self._count_items(self.get_company_formations_url(filters))

    def count_company_formations_with_get(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Same count as `count_company_formations`, through `GET /formations/head`, the route ComboCurve
        publishes for clients that cannot send HEAD. The response has no body; the count is its
        `X-Query-Count` header, and a response without the header raises `ValueError`.

        https://docs.api.combocurve.com/api/get-head-formations
        """
        return self._count_items(self.get_company_formations_head_url(filters), method='get')

    def get_company_formation_by_id(self, formation_id: str) -> Item:
        """
        Returns one formation's summary from its id. This route also returns a project formation.

        https://docs.api.combocurve.com/api/get-formation-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "color": "string",
            "enabled": true,
            "scope": "string",
            "projectId": "5e272d38b78910dd2a1bd691",
            "maxDepth": 123.45,
            "maxThickness": 123.45,
            "bbox": [
                123.45
            ],
            "pointCount": 123,
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z"
        }
        """
        return self._get_items(self.get_company_formation_by_id_url(formation_id))[0]

    def get_company_formation_points(self, formation_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns every point of one formation (company or project scope), in stored order, in the shape the
        PUT accepts. Pages of 10000 points (the route's maximum `take`) are followed to the end; `filters`
        take `skip` and `take`. A formation imported without `baseTvd` reads back `baseTvd: 50000` with
        `baseIsPlaceholder: true`; a point with a supplied base has no `baseIsPlaceholder` key. A formation
        re-imported while the pages are read can mix old and new points: compare `updatedAt` and
        `pointCount` of `get_company_formation_by_id` after the read.

        https://docs.api.combocurve.com/api/get-formation-points

        Example response:
        [
            {
                "latitude": 123.45,
                "longitude": 123.45,
                "topTvd": 123.45,
                "baseTvd": 123.45,
                "baseIsPlaceholder": true
            }
        ]
        """
        return self._get_formation_points(None, formation_id, filters)

    def get_company_formations_job(self, job_id: str) -> Item:
        """
        Returns the status and result of a formations import started with `put_company_formations` (this
        route also returns a project import job). `status` goes `pending`, `running`, then `successful`
        for a good import; poll until it leaves `pending` and `running`. `result` lists the formations
        imported (`points`, `hasBase`), what was `written` (`created`, `replaced`, `adjusted`), the
        `overlaps` found, and the `skippedRows` / `rowErrors`, located in the original request. An unknown
        id answers 404 (`FormationJobNotFoundError`).

        https://docs.api.combocurve.com/api/get-formations-job

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691",
            "status": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "completedAt": "2020-01-01T00:00:00.000Z",
            "error": "string",
            "result": {
                "formations": [
                    {
                        "name": "Example",
                        "points": 123,
                        "hasBase": true
                    }
                ],
                "written": {
                    "created": 123,
                    "replaced": 123,
                    "adjusted": 123
                },
                "overlaps": [
                    {
                        "above": "string",
                        "below": "string",
                        "conflictingPoints": 123,
                        "comparedPoints": 123,
                        "maxOverlapFt": 123.45
                    }
                ],
                "skippedRows": 123,
                "rowErrors": [
                    {
                        "location": "string",
                        "field": "string",
                        "message": "string"
                    }
                ]
            }
        }
        """
        return self._get_items(self.get_company_formations_job_url(job_id))[0]

    def wait_for_company_formations_job(
        self, job_id: str, timeout_seconds: float = JOB_WAIT_TIMEOUT_SECONDS, poll_seconds: float = JOB_POLL_SECONDS
    ) -> Item:
        """
        Polls `get_company_formations_job` every `poll_seconds` until the job is no longer `pending` or
        `running`, and returns it; check its `status` (`successful` for a good import, seen live
        2026-11-21) and its `result`. Raises `TimeoutError` when it has not finished within
        `timeout_seconds`. A small import finished a few seconds after the PUT (live 2026-11-21). Not an
        API route: it calls the job route repeatedly. The company job route also reads a project import
        job.
        """
        return self._wait_for_job(
            lambda: self.get_company_formations_job(job_id), timeout_seconds, poll_seconds, f'formations job {job_id}'
        )

    def put_company_formations(self, data: Union[Item, ItemList], overlap_handling: Optional[str] = None) -> Item:
        """
        Creates or replaces company formations by name, asynchronously, and returns `{"jobId": ...}`; poll
        `get_company_formations_job` with it, or wait with `wait_for_company_formations_job`. `data` is one
        formation or a list of them, each with `name`,
        `points` (at least 3, each `latitude`, `longitude`, `topTvd` and an optional `baseTvd`) and an
        optional `color` (the server picks one when it is left out). A name that exists in the company scope
        has its surfaces replaced (same `id`); other formations stay, although the import may raise the
        placeholder bottoms of formations above the new ones (`written.adjusted` on the job).

        `overlap_handling` is `trim` (shorten a base that reaches below the top of the formation under it)
        or `keep`; it matters only for formations with `baseTvd`. Left as None, no value is sent and the
        server applies its default.

        The whole request is validated before anything is imported: a problem answers 400 with its
        location, and nothing is written. The list goes in ONE request (one job); it is not split into
        chunks. Refused locally before sending: an empty `data`, and an `overlap_handling` other than
        `trim` / `keep`. The PUT does not set `enabled`, `maxDepth` or `maxThickness`: a new formation
        starts with `enabled: true` and no depth constraints, and a replaced one keeps its values. Set them
        with `patch_company_formations` after the job succeeds.

        https://docs.api.combocurve.com/api/put-formations

        Example data:
        [
            {
                "name": "Example",
                "points": [
                    {
                        "latitude": 123.45,
                        "longitude": 123.45,
                        "topTvd": 123.45,
                        "baseTvd": 123.45
                    }
                ],
                "color": "#6B011a"
            }
        ]

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._put_formations(None, data, overlap_handling)

    def patch_company_formations(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Updates formation metadata by `id`: `name`, `color`, `enabled`, `maxDepth` and `maxThickness`; only
        the fields present change, and the scope cannot change. Any formation in the company can be patched
        here, project formations included. `data` is one record or a list. The response is 207 with one
        result per record: a record without `id` is a per-record 400 and an unknown id a per-record 404, not
        an exception. An empty `data` is refused locally (the server answers 400). All of `data` is sent in
        one request: the documentation states no record limit.

        https://docs.api.combocurve.com/api/patch-formations

        Example data:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "color": "#fdcD67",
                "enabled": true,
                "maxDepth": 123.45,
                "maxThickness": 123.45
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
        return self._patch_formations(None, data)

    def delete_company_formation_by_id(self, formation_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one company formation from its id; a project formation's id answers 404 here (delete it
        with `delete_project_formation_by_id`). Does not cascade: inventory plan landing zones that
        reference the formation keep their reference. Returns the headers of the 204 response.

        https://docs.api.combocurve.com/api/delete-formation-by-id
        """
        return self._delete_headers(self.get_company_formation_by_id_url(formation_id))

    # Project formations

    def get_project_formations(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the formation summaries of one project; company formations are not included (read them
        with `get_company_formations({'scope': 'company'})`). `filters` take `name` (exact match), `skip` and
        `take`. Pages of 200 (the route's maximum `take`; its default is 25) are followed to the end and
        sorted by name.

        https://docs.api.combocurve.com/api/get-project-formations

        Example response:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "color": "string",
                "enabled": true,
                "scope": "string",
                "projectId": "5e272d38b78910dd2a1bd691",
                "maxDepth": 123.45,
                "maxThickness": 123.45,
                "bbox": [
                    123.45
                ],
                "pointCount": 123,
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z"
            }
        ]
        """
        return self._get_formations(project_id, filters)

    def count_project_formations(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of one project's formations matching `filters`, from the `X-Query-Count` header
        of a HEAD request (no summaries are fetched).

        https://docs.api.combocurve.com/api/head-project-formations
        """
        return self._count_items(self.get_project_formations_url(project_id, filters))

    def count_project_formations_with_get(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Same count as `count_project_formations`, through `GET /projects/{projectId}/formations/head`, the
        route ComboCurve publishes for clients that cannot send HEAD. The count is the response's
        `X-Query-Count` header; a response without it raises `ValueError`.

        https://docs.api.combocurve.com/api/get-head-project-formations
        """
        return self._count_items(self.get_project_formations_head_url(project_id, filters), method='get')

    def get_project_formation_by_id(self, project_id: str, formation_id: str) -> Item:
        """
        Returns one of the project's formations from its id; a company formation's id answers 404 here.

        https://docs.api.combocurve.com/api/get-project-formation-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "color": "string",
            "enabled": true,
            "scope": "string",
            "projectId": "5e272d38b78910dd2a1bd691",
            "maxDepth": 123.45,
            "maxThickness": 123.45,
            "bbox": [
                123.45
            ],
            "pointCount": 123,
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z"
        }
        """
        return self._get_items(self.get_project_formation_by_id_url(project_id, formation_id))[0]

    def get_project_formation_points(
        self, project_id: str, formation_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns every point of one of the project's formations, in stored order. Same paging (10000 points
        a page, followed to the end), filters and placeholder-base behavior as
        `get_company_formation_points`.

        https://docs.api.combocurve.com/api/get-project-formation-points

        Example response:
        [
            {
                "latitude": 123.45,
                "longitude": 123.45,
                "topTvd": 123.45,
                "baseTvd": 123.45,
                "baseIsPlaceholder": true
            }
        ]
        """
        return self._get_formation_points(project_id, formation_id, filters)

    def get_project_formations_job(self, project_id: str, job_id: str) -> Item:
        """
        Returns the status and result of a formations import into the project, started with
        `put_project_formations`. Same shape and statuses as `get_company_formations_job`.

        https://docs.api.combocurve.com/api/get-project-formations-job

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691",
            "status": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "completedAt": "2020-01-01T00:00:00.000Z",
            "error": "string",
            "result": {
                "formations": [
                    {
                        "name": "Example",
                        "points": 123,
                        "hasBase": true
                    }
                ],
                "written": {
                    "created": 123,
                    "replaced": 123,
                    "adjusted": 123
                },
                "overlaps": [
                    {
                        "above": "string",
                        "below": "string",
                        "conflictingPoints": 123,
                        "comparedPoints": 123,
                        "maxOverlapFt": 123.45
                    }
                ],
                "skippedRows": 123,
                "rowErrors": [
                    {
                        "location": "string",
                        "field": "string",
                        "message": "string"
                    }
                ]
            }
        }
        """
        return self._get_items(self.get_project_formations_job_url(project_id, job_id))[0]

    def wait_for_project_formations_job(
        self,
        project_id: str,
        job_id: str,
        timeout_seconds: float = JOB_WAIT_TIMEOUT_SECONDS,
        poll_seconds: float = JOB_POLL_SECONDS,
    ) -> Item:
        """
        Polls `get_project_formations_job` every `poll_seconds` until the job is no longer `pending` or
        `running`, and returns it; check its `status` and `result` (see `wait_for_company_formations_job`).
        Raises `TimeoutError` when it has not finished within `timeout_seconds`. Not an API route: it calls
        the job route repeatedly.
        """
        return self._wait_for_job(
            lambda: self.get_project_formations_job(project_id, job_id),
            timeout_seconds,
            poll_seconds,
            f'formations job {job_id}',
        )

    def put_project_formations(
        self, project_id: str, data: Union[Item, ItemList], overlap_handling: Optional[str] = None
    ) -> Item:
        """
        Creates or replaces the project's formations by name, asynchronously, and returns `{"jobId": ...}`;
        poll `get_project_formations_job` with it, or wait with `wait_for_project_formations_job`. Same body,
        `overlap_handling`, validation, single request
        and local refusals as `put_company_formations`, in the project's scope: names and overlaps are
        resolved against this project's formations only, not company ones.

        https://docs.api.combocurve.com/api/put-project-formations

        Example data:
        [
            {
                "name": "Example",
                "points": [
                    {
                        "latitude": 123.45,
                        "longitude": 123.45,
                        "topTvd": 123.45,
                        "baseTvd": 123.45
                    }
                ],
                "color": "#6B011a"
            }
        ]

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        return self._put_formations(project_id, data, overlap_handling)

    def patch_project_formations(self, project_id: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Updates the metadata of the project's formations by `id`. Same fields and rules as
        `patch_company_formations`; a formation outside the project (a company formation included) is a
        per-record 404 in the 207 result. All of `data` is sent in one request: the documentation states no
        record limit.

        https://docs.api.combocurve.com/api/patch-project-formations

        Example data:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "color": "#fdcD67",
                "enabled": true,
                "maxDepth": 123.45,
                "maxThickness": 123.45
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
        return self._patch_formations(project_id, data)

    def delete_project_formation_by_id(self, project_id: str, formation_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one of the project's formations from its id. Does not cascade. Returns the headers of the
        204 response.

        https://docs.api.combocurve.com/api/delete-project-formation-by-id
        """
        return self._delete_headers(self.get_project_formation_by_id_url(project_id, formation_id))
