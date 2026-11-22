from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal, Optional, Union, cast

from requests.structures import CaseInsensitiveDict

from .base import APIBase, Item, ItemList, WriteResponse

# The page size of the production-comment list routes. NOT verified live: the dev tenant answers 404
# `ProductionCommentsDisabledError` on every production-comment route (2026-11-21), so this is the 200 that the
# sibling v1 list routes take, not a measured maximum.
GET_LIMIT = 200

# Production comments have no `name`; a comment is read per well, in date order.
_PRODUCTION_COMMENT_SORT_ORDER: Mapping[str, int] = MappingProxyType({'well': 0, 'startDate': 1, 'id': 2})


class ProductionComments(APIBase):
    """
    Production comments: a note with a comment type on a date range of one well's production. A comment is
    either company-scoped (`/production-comments`) or project-scoped (`/projects/{projectId}/production-comments`);
    both scopes have the same eight routes, so the public methods delegate to the shared helpers below
    (`_comments_url`, `_get_comments`, `_write_comments`) and differ only in the scope. The comment types
    (`prod_comment_type_0` to `prod_comment_type_14`) are a company-level configuration of a label and a color
    per key.

    Production comments are a per-tenant feature. On a tenant where it is off, every production-comment route
    (list, HEAD, by id, in both scopes) answers 404 with the body `{"name": "ProductionCommentsDisabledError",
    "message": "Production comments are not enabled for this tenant"}`, and these methods raise
    `requests.HTTPError`; a HEAD has no body, so `count_*` shows only the 404. The comment-type routes answer
    on such a tenant. Verified live 2026-11-21 on the dev tenant, where the feature is off, so the comment
    routes themselves (page size, write and delete behavior) are not verified live: the method docstrings
    restate the documentation.
    """

    ######
    # URLs
    ######

    def _comments_url(self, project_id: Optional[str], filters: Optional[dict[str, str]] = None) -> str:
        """The production-comment collection url of a project, or of the company when `project_id` is None."""
        scope = '' if project_id is None else f'/projects/{project_id}'
        return f'{self.API_BASE_URL}{scope}/production-comments' + self._build_params_string(filters)

    def get_company_production_comments_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the company production comments.
        """
        return self._comments_url(None, filters)

    def get_company_production_comment_by_id_url(self, production_comment_id: str) -> str:
        """
        Returns the API url of one company production comment, from its id.
        """
        return f'{self.get_company_production_comments_url()}/{production_comment_id}'

    def get_project_production_comments_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of the production comments of a specific project.
        """
        return self._comments_url(project_id, filters)

    def get_project_production_comment_by_id_url(self, project_id: str, production_comment_id: str) -> str:
        """
        Returns the API url of one production comment of a specific project, from its id.
        """
        return f'{self.get_project_production_comments_url(project_id)}/{production_comment_id}'

    def get_production_comment_types_url(self) -> str:
        """
        Returns the API url of the company production comment type configuration.
        """
        return f'{self.API_BASE_URL}/production-comment-types'

    ###########
    # Shared helpers
    ###########

    def _get_comments(self, url: str) -> ItemList:
        """Returns every production comment at `url` (all pages), ordered by well, start date and id."""
        return self._keysort(self._get_items(url, params={'take': GET_LIMIT}), _PRODUCTION_COMMENT_SORT_ORDER)

    def _write_comments(
        self, verb: Literal['post', 'put', 'patch'], project_id: Optional[str], data: Union[Item, ItemList]
    ) -> list[WriteResponse]:
        """POST, PUT or PATCH `data` (one comment or a list, refused when empty) to the company collection, or
        the project's when `project_id` is given; one 207 envelope per batch."""
        records = self._records_from(data, 'production comment')
        write = {'post': self._post_items, 'put': self._put_items, 'patch': self._patch_items}[verb]
        return cast('list[WriteResponse]', write(self._comments_url(project_id), records))

    @staticmethod
    def _comment_delete_filters(
        production_comment_id: Optional[str],
        well_id: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> dict[str, str]:
        """
        Build the query of a filtered production-comment DELETE, refusing any filter set that does not name
        a comment id or a well.

        The route takes either `id`, or `well` with `startDate` and `endDate`. A DELETE with no filter is
        refused here because the documentation names no behavior for it, and the plausible one is deleting
        every comment in scope. A date range without `well` is refused for the same reason: it would apply
        to every well in scope. `id` and `well` together are refused too: the documentation describes them
        as alternatives and names no behavior for the pair.
        """
        if production_comment_id and well_id:
            raise ValueError('pass production_comment_id or well_id, not both')
        filters = APIBase._require_any_filter(
            {'id': production_comment_id, 'well': well_id}, 'production_comment_id or well_id'
        )
        if not well_id and (start_date or end_date):
            raise ValueError('start_date and end_date filter a delete by well; pass well_id with them')
        if start_date:
            filters['startDate'] = start_date
        if end_date:
            filters['endDate'] = end_date
        return filters

    ###########
    # API calls
    ###########

    # Company production comments

    def get_company_production_comments(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the company production comments, every page, ordered locally by `well`, `startDate` and `id` (so a
        `sort` filter does not change the order returned). `filters` take `well`, `commentType` (a key such as
        `prod_comment_type_0`), `startDate`, `endDate`, `updatedAt` (with the `[lt]`, `[le]`, `[gt]` and `[ge]`
        operators), `chosenID` with `dataSource` (each requires the other), `skip`, `take`, `sort` and `cursor`.
        Pages are requested with `take=200`; that page size is not verified live (see the class docstring).

        https://docs.api.combocurve.com/api/get-production-comments

        Example response:
        [
            {
                "chosenID": "string",
                "commentType": "prod_comment_type_14",
                "createdAt": "2020-01-01",
                "createdBy": "string",
                "dataSource": "string",
                "endDate": "2020-01-01",
                "id": "5e272d38b78910dd2a1bd691",
                "note": "string",
                "project": "string",
                "startDate": "2020-01-01",
                "updatedAt": "2020-01-01",
                "well": "string"
            }
        ]
        """
        return self._get_comments(self.get_company_production_comments_url(filters))

    def count_company_production_comments(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of company production comments matching `filters`, from the `X-Query-Count` header of a HEAD
        request (no documents are fetched). `filters` are those of `get_company_production_comments`.

        https://docs.api.combocurve.com/api/head-production-comments
        """
        return self._count_items(self.get_company_production_comments_url(filters))

    def get_company_production_comment_by_id(self, production_comment_id: str) -> Item:
        """
        Returns one company production comment from its id.

        https://docs.api.combocurve.com/api/get-production-comment-by-id

        Example response:
        {
            "chosenID": "string",
            "commentType": "prod_comment_type_13",
            "createdAt": "2020-01-01",
            "createdBy": "string",
            "dataSource": "string",
            "endDate": "2020-01-01",
            "id": "5e272d38b78910dd2a1bd691",
            "note": "string",
            "project": "string",
            "startDate": "2020-01-01",
            "updatedAt": "2020-01-01",
            "well": "string"
        }
        """
        return self._get_items(self.get_company_production_comment_by_id_url(production_comment_id))[0]

    def post_company_production_comments(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Creates company production comments. `data` is one comment or a list of them; each names its well by
        `well` (the well id) or by `chosenID` with `dataSource`, and carries `commentType`, `startDate`, `endDate`
        and `note`. The response is 207 Multi-Status: a record the server refuses is reported in `results`, not
        raised. An empty list raises `ValueError` before anything is sent.
        All of `data` is sent in one request: the documentation states no record limit, and none is verified
        live (the dev tenant has production comments off).

        https://docs.api.combocurve.com/api/post-production-comments

        Example data:
        [
            {
                "commentType": "prod_comment_type_3",
                "startDate": "2020-01-01T00:00:00.000Z",
                "endDate": "2020-01-01T00:00:00.000Z",
                "well": "string",
                "chosenID": "string",
                "dataSource": "string",
                "note": "string"
            }
        ]

        Example response:
        {
            "results": [
                {
                    "status": "string",
                    "code": 123.45,
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
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "successCount": 123.45,
            "failedCount": 123.45
        }
        """
        return self._write_comments('post', None, data)

    def put_company_production_comments(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Upserts company production comments. A record with an `id` replaces that comment, or is inserted when no
        comment has that id; a record without an `id` creates a new comment. The well is named as in
        `post_company_production_comments`. The response is 207 Multi-Status: a record the server refuses is
        reported in `results`, not raised. An empty list raises `ValueError` before anything is sent.
        All of `data` is sent in one request: the documentation states no record limit, and none is verified
        live (the dev tenant has production comments off).

        https://docs.api.combocurve.com/api/put-production-comments

        Example data:
        [
            {
                "commentType": "prod_comment_type_14",
                "startDate": "2020-01-01T00:00:00.000Z",
                "endDate": "2020-01-01T00:00:00.000Z",
                "well": "string",
                "chosenID": "string",
                "dataSource": "string",
                "note": "string",
                "id": "5e272d38b78910dd2a1bd691"
            }
        ]

        Example response:
        {
            "results": [
                {
                    "status": "string",
                    "code": 123.45,
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
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "successCount": 123.45,
            "failedCount": 123.45
        }
        """
        return self._write_comments('put', None, data)

    def patch_company_production_comments(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Partially updates company production comments. Each record needs its `id` and at least one field to
        change; fields left out are kept. The response is 207 Multi-Status: a record the server refuses is
        reported in `results`, not raised. An empty list raises `ValueError` before anything is sent.
        All of `data` is sent in one request: the documentation states no record limit, and none is verified
        live (the dev tenant has production comments off).

        https://docs.api.combocurve.com/api/patch-production-comments

        Example data:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "well": "string",
                "chosenID": "string",
                "dataSource": "string",
                "commentType": "prod_comment_type_4",
                "note": "string",
                "startDate": "2020-01-01T00:00:00.000Z",
                "endDate": "2020-01-01T00:00:00.000Z"
            }
        ]

        Example response:
        {
            "results": [
                {
                    "status": "string",
                    "code": 123.45,
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
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "successCount": 123.45,
            "failedCount": 123.45
        }
        """
        return self._write_comments('patch', None, data)

    def delete_company_production_comments(
        self,
        *,
        production_comment_id: Optional[str] = None,
        well_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes company production comments by query filter: one comment by `production_comment_id`, or the comments of
        `well_id`, narrowed by `start_date` and `end_date`. The filters are keyword-only.

        Refused with `ValueError` before anything is sent: no `production_comment_id` and no `well_id`
        (the documentation names no behavior for an unfiltered delete, and the plausible one deletes every
        comment in scope), and a date without `well_id` (it would apply to every well in scope). Empty
        strings count as absent. `production_comment_id` and `well_id` together are refused as well: the
        documentation describes them as alternatives and names no behavior for the pair.

        https://docs.api.combocurve.com/api/delete-production-comments

        Returns the headers of the delete response.
        """
        filters = self._comment_delete_filters(production_comment_id, well_id, start_date, end_date)
        return self._delete_headers(self.get_company_production_comments_url(filters))

    def delete_company_production_comment_by_id(self, production_comment_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one company production comment from its id.

        https://docs.api.combocurve.com/api/delete-production-comment-by-id

        Returns the headers of the delete response.
        """
        return self._delete_headers(self.get_company_production_comment_by_id_url(production_comment_id))

    # Project production comments

    def get_project_production_comments(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the production comments of a specific project, every page, ordered locally by `well`, `startDate`
        and `id` (so a `sort` filter does not change the order returned). `filters` take `well`, `commentType` (a
        key such as `prod_comment_type_0`), `startDate`, `endDate`, `updatedAt` (with the `[lt]`, `[le]`, `[gt]`
        and `[ge]` operators), `chosenID` with `dataSource` (each requires the other), `skip`, `take`, `sort` and
        `cursor`. Pages are requested with `take=200`; that page size is not verified live (see the class docstring).

        https://docs.api.combocurve.com/api/get-project-production-comments

        Example response:
        [
            {
                "chosenID": "string",
                "commentType": "prod_comment_type_13",
                "createdAt": "2020-01-01",
                "createdBy": "string",
                "dataSource": "string",
                "endDate": "2020-01-01",
                "id": "5e272d38b78910dd2a1bd691",
                "note": "string",
                "project": "string",
                "startDate": "2020-01-01",
                "updatedAt": "2020-01-01",
                "well": "string"
            }
        ]
        """
        return self._get_comments(self.get_project_production_comments_url(project_id, filters))

    def count_project_production_comments(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of production comments of a specific project matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched). `filters` are those of
        `get_project_production_comments`.

        https://docs.api.combocurve.com/api/head-project-production-comments
        """
        return self._count_items(self.get_project_production_comments_url(project_id, filters))

    def get_project_production_comment_by_id(self, project_id: str, production_comment_id: str) -> Item:
        """
        Returns one production comment of a specific project from its id.

        https://docs.api.combocurve.com/api/get-project-production-comment-by-id

        Example response:
        {
            "chosenID": "string",
            "commentType": "prod_comment_type_14",
            "createdAt": "2020-01-01",
            "createdBy": "string",
            "dataSource": "string",
            "endDate": "2020-01-01",
            "id": "5e272d38b78910dd2a1bd691",
            "note": "string",
            "project": "string",
            "startDate": "2020-01-01",
            "updatedAt": "2020-01-01",
            "well": "string"
        }
        """
        return self._get_items(self.get_project_production_comment_by_id_url(project_id, production_comment_id))[0]

    def post_project_production_comments(self, project_id: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Creates production comments of a specific project. `data` is one comment or a list of them; each names its
        well by `well` (the well id) or by `chosenID` with `dataSource`, and carries `commentType`, `startDate`,
        `endDate` and `note`. The response is 207 Multi-Status: a record the server refuses is reported in
        `results`, not raised. An empty list raises `ValueError` before anything is sent.
        All of `data` is sent in one request: the documentation states no record limit, and none is verified
        live (the dev tenant has production comments off).

        https://docs.api.combocurve.com/api/post-project-production-comments

        Example data:
        [
            {
                "commentType": "prod_comment_type_9",
                "startDate": "2020-01-01T00:00:00.000Z",
                "endDate": "2020-01-01T00:00:00.000Z",
                "well": "string",
                "chosenID": "string",
                "dataSource": "string",
                "note": "string"
            }
        ]

        Example response:
        {
            "results": [
                {
                    "status": "string",
                    "code": 123.45,
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
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "successCount": 123.45,
            "failedCount": 123.45
        }
        """
        return self._write_comments('post', project_id, data)

    def put_project_production_comments(self, project_id: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Upserts production comments of a specific project. A record with an `id` replaces that comment, or is
        inserted when no comment has that id; a record without an `id` creates a new comment. The well is named as
        in `post_project_production_comments`. The response is 207 Multi-Status: a record the server refuses is
        reported in `results`, not raised. An empty list raises `ValueError` before anything is sent.
        All of `data` is sent in one request: the documentation states no record limit, and none is verified
        live (the dev tenant has production comments off).

        https://docs.api.combocurve.com/api/put-project-production-comments

        Example data:
        [
            {
                "commentType": "prod_comment_type_14",
                "startDate": "2020-01-01T00:00:00.000Z",
                "endDate": "2020-01-01T00:00:00.000Z",
                "well": "string",
                "chosenID": "string",
                "dataSource": "string",
                "note": "string",
                "id": "5e272d38b78910dd2a1bd691"
            }
        ]

        Example response:
        {
            "results": [
                {
                    "status": "string",
                    "code": 123.45,
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
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "successCount": 123.45,
            "failedCount": 123.45
        }
        """
        return self._write_comments('put', project_id, data)

    def patch_project_production_comments(self, project_id: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Partially updates production comments of a specific project. Each record needs its `id` and at least one
        field to change; fields left out are kept. The response is 207 Multi-Status: a record the server refuses
        is reported in `results`, not raised. An empty list raises `ValueError` before anything is sent.
        All of `data` is sent in one request: the documentation states no record limit, and none is verified
        live (the dev tenant has production comments off).

        https://docs.api.combocurve.com/api/patch-project-production-comments

        Example data:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "well": "string",
                "chosenID": "string",
                "dataSource": "string",
                "commentType": "prod_comment_type_8",
                "note": "string",
                "startDate": "2020-01-01T00:00:00.000Z",
                "endDate": "2020-01-01T00:00:00.000Z"
            }
        ]

        Example response:
        {
            "results": [
                {
                    "status": "string",
                    "code": 123.45,
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
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "successCount": 123.45,
            "failedCount": 123.45
        }
        """
        return self._write_comments('patch', project_id, data)

    def delete_project_production_comments(
        self,
        project_id: str,
        *,
        production_comment_id: Optional[str] = None,
        well_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes production comments of a specific project by query filter: one comment by `production_comment_id`,
        or the comments of `well_id`, narrowed by `start_date` and `end_date`. The filters are keyword-only.

        Refused with `ValueError` before anything is sent: no `production_comment_id` and no `well_id`
        (the documentation names no behavior for an unfiltered delete, and the plausible one deletes every
        comment in scope), and a date without `well_id` (it would apply to every well in scope). Empty
        strings count as absent. `production_comment_id` and `well_id` together are refused as well: the
        documentation describes them as alternatives and names no behavior for the pair.

        https://docs.api.combocurve.com/api/delete-project-production-comments

        Returns the headers of the delete response.
        """
        filters = self._comment_delete_filters(production_comment_id, well_id, start_date, end_date)
        return self._delete_headers(self.get_project_production_comments_url(project_id, filters))

    def delete_project_production_comment_by_id(
        self, project_id: str, production_comment_id: str
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes one production comment of a specific project from its id.

        https://docs.api.combocurve.com/api/delete-project-production-comment-by-id

        Returns the headers of the delete response.
        """
        return self._delete_headers(self.get_project_production_comment_by_id_url(project_id, production_comment_id))

    # Production comment types

    def get_production_comment_types(self) -> Item:
        """
        Returns the company production comment type configuration: `{"productionCommentTypes": [...]}`,
        one `key` / `label` / `color` entry for each of the 15 keys `prod_comment_type_0` to
        `prod_comment_type_14`, in key order. This route answers on a tenant where production comments are
        not enabled (verified live 2026-11-21 on dev).

        https://docs.api.combocurve.com/api/get-production-comment-types

        Example response:
        {
            "productionCommentTypes": [
                {
                    "key": "prod_comment_type_7",
                    "label": "string",
                    "color": "string"
                }
            ]
        }
        """
        return self._get_items(self.get_production_comment_types_url())[0]

    def patch_production_comment_types(self, comment_types: ItemList) -> Item:
        """
        Updates the label and color of the given production comment type keys, and returns the full
        configuration (all 15 keys), as `get_production_comment_types`. `comment_types` is the list of
        entries; this method wraps it in the `{"productionCommentTypes": [...]}` body the route takes.
        Keys left out are unchanged.

        Behavior verified live 2026-11-21 on dev, not stated in the documentation: each entry needs all of
        `key`, `label` and `color` (a missing one answers 400 `TypeError`); a key outside
        `prod_comment_type_0` to `prod_comment_type_14`, a repeated key, or any other field answers 400,
        and then nothing is applied. `color` is stored as given, not checked as a color. An empty list
        raises `ValueError` before anything is sent (the route answers 400 `RecordCountError`). A 4xx or
        5xx response raises `requests.HTTPError`.

        https://docs.api.combocurve.com/api/patch-production-comment-types

        Example data:
        {
            "productionCommentTypes": [
                {
                    "key": "prod_comment_type_6",
                    "label": "string",
                    "color": "string"
                }
            ]
        }

        Example response:
        {
            "productionCommentTypes": [
                {
                    "key": "prod_comment_type_7",
                    "label": "string",
                    "color": "string"
                }
            ]
        }
        """
        self._require_records(comment_types, 'production comment type')
        url = self.get_production_comment_types_url()
        return self._send_for_item('patch', url, {'productionCommentTypes': comment_types})
