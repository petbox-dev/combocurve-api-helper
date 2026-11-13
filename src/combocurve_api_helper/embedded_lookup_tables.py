from typing import Optional, cast

from requests.structures import CaseInsensitiveDict

from .base import LIST_SORT_ORDER, APIBase, Item, ItemList, WriteResponse

GET_LIMIT = 200  # the maximum of `take` on both embedded-lookup-table routes (verified live 2026-11-12)


class EmbeddedLookupTables(APIBase):
    """
    Embedded lookup tables: the lookup tables that an econ model (capex, expenses, stream
    properties, differentials, production taxes, risking, operations) links to. A table is
    either project-scoped (`/projects/{projectId}/embedded-lookup-tables`) or company-scoped
    (`/embedded-lookup-tables`). Each document carries `type`, `name`, `caseInsensitiveMatching`,
    `rows` and `rules`.

    `filters` take `name`, `type`, `createdAt` and `updatedAt` (the dates take the `[lt]`, `[le]`,
    `[gt]` and `[ge]` operators). `type` is one of `capex`, `expenses`, `stream_properties`,
    `differentials`, `production_taxes`, `risking`, `operations`; any other value answers 400.
    Without `type` the list has every type the tenant can use.

    A name is unique across all types, per project (project tables) or per company (company
    tables). A PUT replaces a table by name: it replaces all rows, rules and options, keeps
    `createdBy`, `copiedFrom` and `tags`, and cannot change the type. The POST result carries the
    new `id`.

    A row is one line of the econ model. The cell that the rules fill holds the string
    `"lookup_by"`: `value` for expenses, differentials, stream properties and production taxes
    (a list with one entry per `period` entry), or `intangible` / `tangible` for capex (one
    number). Each rule has a `filter` on well headers (`custom_string_7`, `chosenID`, `state`, ...)
    and one `values` entry per row, keyed by `rowNumber` and the filled cell's name. The server
    fills row options left out of a write (`shrinkageCondition`, `escalationModel`,
    `affectEconLimit`, ...). Verified live 2026-11-13.

    Example table (expenses; capex rows use `"intangible": "lookup_by"` and rule values
    `{"rowNumber": 1, "intangible": 2940}`):
        {
            "type": "expenses",
            "name": "Sample Expenses Table",
            "caseInsensitiveMatching": true,
            "rows": [
                {
                    "rowNumber": 1,
                    "key": "oil",
                    "category": "processing",
                    "criteria": "offset_to_fpd",
                    "unit": "dollar_per_bbl",
                    "calculation": "nri",
                    "period": [12, 96, 600],
                    "value": "lookup_by"
                }
            ],
            "rules": [
                {
                    "filter": [{"key": "custom_string_1", "operator": "equal", "value": "OPERATOR A"}],
                    "values": [{"rowNumber": 1, "value": [2.0, 5.0, 8.25]}]
                }
            ]
        }
    """

    ######
    # URLs
    ######

    def get_embedded_lookup_tables_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for the embedded lookup tables of a specific project.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/embedded-lookup-tables'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_embedded_lookup_table_by_id_url(self, project_id: str, embedded_lookup_table_id: str) -> str:
        """
        Returns the API url for a specific project embedded lookup table from its id.
        """
        base_url = self.get_embedded_lookup_tables_url(project_id)
        return f'{base_url}/{embedded_lookup_table_id}'

    def get_company_embedded_lookup_tables_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for the company embedded lookup tables.
        """
        url = f'{self.API_BASE_URL}/embedded-lookup-tables'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_company_embedded_lookup_table_by_id_url(self, embedded_lookup_table_id: str) -> str:
        """
        Returns the API url for a specific company embedded lookup table from its id.
        """
        base_url = self.get_company_embedded_lookup_tables_url()
        return f'{base_url}/{embedded_lookup_table_id}'

    ###########
    # API calls
    ###########

    # Project embedded lookup tables

    def get_embedded_lookup_tables(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the embedded lookup tables of a specific project.

        https://docs.api.combocurve.com/api/get-embedded-lookup-tables

        Example response:
        [
            {
                "type": "capex",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "project": "string",
                "caseInsensitiveMatching": true,
                "createdBy": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z",
                "copiedFrom": "string",
                "tags": [
                    "string"
                ]
            }
        ]
        """
        url = self.get_embedded_lookup_tables_url(project_id, filters)
        params = {'take': GET_LIMIT}
        embedded_lookup_tables = self._get_items(url, params=params)

        return self._keysort(embedded_lookup_tables, LIST_SORT_ORDER)

    def count_embedded_lookup_tables(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of embedded lookup tables of a specific project matching `filters`,
        from the `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-embedded-lookup-tables
        """
        return self._count_items(self.get_embedded_lookup_tables_url(project_id, filters))

    def get_embedded_lookup_table_by_id(self, project_id: str, embedded_lookup_table_id: str) -> Item:
        """
        Returns a specific project embedded lookup table from its id.

        https://docs.api.combocurve.com/api/get-embedded-lookup-table-by-id

        Example response:
        {
            "type": "capex",
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "project": "string",
            "caseInsensitiveMatching": true,
            "createdBy": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z",
            "copiedFrom": "string",
            "tags": [
                "string"
            ]
        }
        """
        url = self.get_embedded_lookup_table_by_id_url(project_id, embedded_lookup_table_id)
        return self._get_items(url)[0]

    def post_embedded_lookup_tables(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates embedded lookup tables in a specific project.

        https://docs.api.combocurve.com/api/post-embedded-lookup-tables

        Example data:
        [
            {
                "type": "capex",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "project": "string",
                "caseInsensitiveMatching": true,
                "createdBy": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z",
                "copiedFrom": "string",
                "tags": [
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
        url = self.get_embedded_lookup_tables_url(project_id)
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_embedded_lookup_tables(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Replaces (by name) or creates embedded lookup tables in a specific project.

        https://docs.api.combocurve.com/api/put-embedded-lookup-tables

        Example data:
        [
            {
                "type": "capex",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "project": "string",
                "caseInsensitiveMatching": true,
                "createdBy": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z",
                "copiedFrom": "string",
                "tags": [
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
        url = self.get_embedded_lookup_tables_url(project_id)
        return cast('list[WriteResponse]', self._put_items(url, data))

    def delete_embedded_lookup_table_by_id(
        self, project_id: str, embedded_lookup_table_id: str
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific project embedded lookup table from its id. ComboCurve also removes the
        links to it from the econ models.

        https://docs.api.combocurve.com/api/delete-embedded-lookup-table-by-id

        Returns the headers from the delete response.
        """
        url = self.get_embedded_lookup_table_by_id_url(project_id, embedded_lookup_table_id)
        responses = self._delete_responses(url, data=[])
        return responses[0].headers

    # Company embedded lookup tables

    def get_company_embedded_lookup_tables(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns the company embedded lookup tables.

        https://docs.api.combocurve.com/api/get-company-embedded-lookup-tables

        Example response:
        [
            {
                "type": "capex",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "project": "string",
                "caseInsensitiveMatching": true,
                "createdBy": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z",
                "copiedFrom": "string",
                "tags": [
                    "string"
                ]
            }
        ]
        """
        url = self.get_company_embedded_lookup_tables_url(filters)
        params = {'take': GET_LIMIT}
        embedded_lookup_tables = self._get_items(url, params=params)

        return self._keysort(embedded_lookup_tables, LIST_SORT_ORDER)

    def count_company_embedded_lookup_tables(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of company embedded lookup tables matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-company-embedded-lookup-tables
        """
        return self._count_items(self.get_company_embedded_lookup_tables_url(filters))

    def get_company_embedded_lookup_table_by_id(self, embedded_lookup_table_id: str) -> Item:
        """
        Returns a specific company embedded lookup table from its id.

        https://docs.api.combocurve.com/api/get-company-embedded-lookup-table-by-id

        Example response:
        {
            "type": "capex",
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "project": "string",
            "caseInsensitiveMatching": true,
            "createdBy": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z",
            "copiedFrom": "string",
            "tags": [
                "string"
            ]
        }
        """
        url = self.get_company_embedded_lookup_table_by_id_url(embedded_lookup_table_id)
        return self._get_items(url)[0]

    def post_company_embedded_lookup_tables(self, data: ItemList) -> list[WriteResponse]:
        """
        Creates company embedded lookup tables.

        https://docs.api.combocurve.com/api/post-company-embedded-lookup-tables

        Example data:
        [
            {
                "type": "capex",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "project": "string",
                "caseInsensitiveMatching": true,
                "createdBy": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z",
                "copiedFrom": "string",
                "tags": [
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
        url = self.get_company_embedded_lookup_tables_url()
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_company_embedded_lookup_tables(self, data: ItemList) -> list[WriteResponse]:
        """
        Replaces (by name) or creates company embedded lookup tables.

        https://docs.api.combocurve.com/api/put-company-embedded-lookup-tables

        Example data:
        [
            {
                "type": "capex",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "project": "string",
                "caseInsensitiveMatching": true,
                "createdBy": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z",
                "copiedFrom": "string",
                "tags": [
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
        url = self.get_company_embedded_lookup_tables_url()
        return cast('list[WriteResponse]', self._put_items(url, data))

    def delete_company_embedded_lookup_table_by_id(self, embedded_lookup_table_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific company embedded lookup table from its id. ComboCurve also removes the
        links to it from the econ models.

        https://docs.api.combocurve.com/api/delete-company-embedded-lookup-table-by-id

        Returns the headers from the delete response.
        """
        url = self.get_company_embedded_lookup_table_by_id_url(embedded_lookup_table_id)
        responses = self._delete_responses(url, data=[])
        return responses[0].headers
