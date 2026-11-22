from typing import Optional, Union, cast

from requests.structures import CaseInsensitiveDict

from .base import LIST_SORT_ORDER, APIBase, Item, ItemList, QueryFilters, WriteResponse

GET_LIMIT = 200  # the maximum of `take` on the econ-settings and econ-report-settings GET routes

# The two company-shared resources. Both have the same seven routes; only the path differs.
ECON_SETTINGS = 'econ-settings'
ECON_REPORT_SETTINGS = 'econ-report-settings'


class EconSettings(APIBase):
    """
    Company econ settings and econ report settings. Both are named documents shared by the whole
    company: reads return every document regardless of who created it, and a `name` is unique on
    external-API writes. Each resource has the same routes, so the public methods delegate to the
    shared `_..._documents` helpers below and differ only in the resource path.
    """

    ######
    # URLs
    ######

    def _company_url(self, resource: str, filters: Optional[QueryFilters] = None) -> str:
        """
        Returns the company collection url of `resource`, with `filters` as its query string.
        """
        url = f'{self.API_BASE_URL}/{resource}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def _company_document_url(self, resource: str, document_id: str) -> str:
        """
        Returns the url of one document of the company collection `resource`, from its id.
        """
        return f'{self.API_BASE_URL}/{resource}/{document_id}'

    def get_econ_settings_url(self, filters: Optional[QueryFilters] = None) -> str:
        """
        Returns the API url of the company econ settings.
        """
        return self._company_url(ECON_SETTINGS, filters)

    def get_econ_setting_by_id_url(self, econ_setting_id: str) -> str:
        """
        Returns the API url of one company econ setting, from its id.
        """
        return self._company_document_url(ECON_SETTINGS, econ_setting_id)

    def get_econ_report_settings_url(self, filters: Optional[QueryFilters] = None) -> str:
        """
        Returns the API url of the company econ report settings.
        """
        return self._company_url(ECON_REPORT_SETTINGS, filters)

    def get_econ_report_setting_by_id_url(self, econ_report_setting_id: str) -> str:
        """
        Returns the API url of one company econ report setting, from its id.
        """
        return self._company_document_url(ECON_REPORT_SETTINGS, econ_report_setting_id)

    ###########
    # Shared helpers
    ###########

    def _get_documents(self, resource: str, filters: Optional[QueryFilters] = None) -> ItemList:
        """Returns the documents of the company collection `resource`, with the shared list ordering."""
        url = self._company_url(resource, filters)
        return self._keysort(self._get_items(url, params={'take': GET_LIMIT}), LIST_SORT_ORDER)

    def _count_documents(self, resource: str, filters: Optional[QueryFilters] = None) -> int:
        """Returns the number of documents matching `filters`, from the `X-Query-Count` header of a HEAD."""
        return self._count_items(self._company_url(resource, filters))

    def _get_document_by_id(self, resource: str, document_id: str) -> Item:
        """Returns one document of the company collection `resource`, from its id."""
        return self._get_items(self._company_document_url(resource, document_id))[0]

    def _post_documents(self, resource: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """Creates documents in the company collection `resource`."""
        records = self._records_from(data, 'document')
        return cast('list[WriteResponse]', self._post_items(self._company_url(resource), records))

    def _put_documents(self, resource: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """Upserts documents of the company collection `resource`, by `name`."""
        records = self._records_from(data, 'document')
        return cast('list[WriteResponse]', self._put_items(self._company_url(resource), records))

    def _patch_documents(self, resource: str, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """Partially updates documents of the company collection `resource`, by `name`."""
        records = self._records_from(data, 'document')
        return cast('list[WriteResponse]', self._patch_items(self._company_url(resource), records))

    def _delete_document(self, resource: str, document_id: str) -> CaseInsensitiveDict[str]:
        """Deletes one document of the company collection `resource`, from its id."""
        return self._delete_headers(self._company_document_url(resource, document_id))

    ###########
    # API calls
    ###########

    # Econ settings

    def get_econ_settings(self, filters: Optional[QueryFilters] = None) -> ItemList:
        """
        Returns the company econ settings. `filters` take `name`, `createdAt`, `updatedAt`, `skip`,
        `take` and `cursor`. `skip` and `take` may be given as `int` or `str`.

        https://docs.api.combocurve.com/api/get-econ-settings

        Example response:
        [
            {
                "categories": [
                    {
                        "category": "string",
                        "columns": [
                            {
                                "key": "string",
                                "selected": [
                                    "aggregate"
                                ]
                            }
                        ]
                    }
                ],
                "createdAt": "2020-01-01",
                "createdBy": "string",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "updatedAt": "2020-01-01"
            }
        ]
        """
        return self._get_documents(ECON_SETTINGS, filters)

    def count_econ_settings(self, filters: Optional[QueryFilters] = None) -> int:
        """
        Returns the number of company econ settings matching `filters`, from the `X-Query-Count` header
        of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-econ-settings
        """
        return self._count_documents(ECON_SETTINGS, filters)

    def get_econ_setting_by_id(self, econ_setting_id: str) -> Item:
        """
        Returns one company econ setting from its id.

        https://docs.api.combocurve.com/api/get-econ-settings-by-id

        Example response:
        {
            "categories": [
                {
                    "category": "string",
                    "columns": [
                        {
                            "key": "string",
                            "selected": [
                                "oneLiner"
                            ]
                        }
                    ]
                }
            ],
            "createdAt": "2020-01-01",
            "createdBy": "string",
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "updatedAt": "2020-01-01"
        }
        """
        return self._get_document_by_id(ECON_SETTINGS, econ_setting_id)

    def post_econ_settings(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Creates company econ settings. `data` is one setting or a list of them. The names must be unique
        in the company: a name that already exists, or one repeated in `data`, is a per-record collision
        error. The response is always 207 Multi-Status.

        Sends `data` in one request; the API states no record cap. One document (a dict) is sent as a
        one-item list. An empty `data` raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/post-econ-settings

        Example data:
        [
            {
                "name": "Example",
                "categories": [
                    {
                        "category": "string",
                        "columns": [
                            {
                                "key": "string",
                                "selected": [
                                    "monthly"
                                ]
                            }
                        ]
                    }
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
        return self._post_documents(ECON_SETTINGS, data)

    def put_econ_settings(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Upserts company econ settings by `name`. A setting with a matching name is replaced in full (an
        absent `categories` clears the selection); otherwise a new setting is created. A name that matches
        more than one existing setting, or that repeats within `data`, is a per-record collision error.

        Sends `data` in one request; the API states no record cap. One document (a dict) is sent as a
        one-item list. An empty `data` raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/put-econ-settings

        Example data:
        [
            {
                "name": "Example",
                "categories": [
                    {
                        "category": "string",
                        "columns": [
                            {
                                "key": "string",
                                "selected": [
                                    "monthly"
                                ]
                            }
                        ]
                    }
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
        return self._put_documents(ECON_SETTINGS, data)

    def patch_econ_settings(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Partially updates company econ settings by `name`. It never inserts: a name that matches no setting
        is a per-record 404. Omitting `categories` leaves the stored selection unchanged; a provided
        `categories` replaces the whole selection.

        Sends `data` in one request; the API states no record cap. One document (a dict) is sent as a
        one-item list. An empty `data` raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/patch-econ-settings

        Example data:
        [
            {
                "name": "Example",
                "categories": [
                    {
                        "category": "string",
                        "columns": [
                            {
                                "key": "string",
                                "selected": [
                                    "monthly"
                                ]
                            }
                        ]
                    }
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
        return self._patch_documents(ECON_SETTINGS, data)

    def delete_econ_setting_by_id(self, econ_setting_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one company econ setting from its id.

        https://docs.api.combocurve.com/api/delete-econ-settings-by-id

        Returns the headers from the delete response.
        """
        return self._delete_document(ECON_SETTINGS, econ_setting_id)

    # Econ report settings

    def get_econ_report_settings(self, filters: Optional[QueryFilters] = None) -> ItemList:
        """
        Returns the company econ report settings. An absent `allWellsAgg` is returned as `true`, and an
        absent `rollUpEachLevel` as `false`. `filters` take `name`, `createdAt`, `updatedAt`, `skip`,
        `take` and `cursor`. `skip` and `take` may be given as `int` or `str`.

        https://docs.api.combocurve.com/api/get-econ-report-settings

        Example response:
        [
            {
                "allWellsAgg": true,
                "createdAt": "2020-01-01",
                "createdBy": "string",
                "headers": [
                    "string"
                ],
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "rollUpEachLevel": true,
                "updatedAt": "2020-01-01"
            }
        ]
        """
        return self._get_documents(ECON_REPORT_SETTINGS, filters)

    def count_econ_report_settings(self, filters: Optional[QueryFilters] = None) -> int:
        """
        Returns the number of company econ report settings matching `filters`, from the `X-Query-Count`
        header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-econ-report-settings
        """
        return self._count_documents(ECON_REPORT_SETTINGS, filters)

    def get_econ_report_setting_by_id(self, econ_report_setting_id: str) -> Item:
        """
        Returns one company econ report setting from its id.

        https://docs.api.combocurve.com/api/get-econ-report-settings-by-id

        Example response:
        {
            "allWellsAgg": true,
            "createdAt": "2020-01-01",
            "createdBy": "string",
            "headers": [
                "string"
            ],
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "rollUpEachLevel": true,
            "updatedAt": "2020-01-01"
        }
        """
        return self._get_document_by_id(ECON_REPORT_SETTINGS, econ_report_setting_id)

    def post_econ_report_settings(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Creates company econ report settings. `data` is one setting or a list of them; the response is
        always 207 Multi-Status. Names must be unique on external writes. `headers` is ordered, holds at
        most five entries, and each must be a member of the header list. An omitted `headers` becomes an
        empty list; omitted aggregation booleans are not stored and take their read defaults.

        Sends `data` in one request; the API states no record cap. One document (a dict) is sent as a
        one-item list. An empty `data` raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/post-econ-report-settings

        Example data:
        [
            {
                "name": "Example",
                "headers": [
                    "string"
                ],
                "allWellsAgg": true,
                "rollUpEachLevel": true
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
        return self._post_documents(ECON_REPORT_SETTINGS, data)

    def put_econ_report_settings(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Upserts company econ report settings by `name`. A single match is replaced in full, no match is
        inserted, and multiple matches are a per-record collision error. Duplicate names in one request
        are rejected. An omitted `headers` becomes an empty list; omitted aggregation booleans are removed
        so their read defaults apply.

        Sends `data` in one request; the API states no record cap. One document (a dict) is sent as a
        one-item list. An empty `data` raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/put-econ-report-settings

        Example data:
        [
            {
                "name": "Example",
                "headers": [
                    "string"
                ],
                "allWellsAgg": true,
                "rollUpEachLevel": true
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
        return self._put_documents(ECON_REPORT_SETTINGS, data)

    def patch_econ_report_settings(self, data: Union[Item, ItemList]) -> list[WriteResponse]:
        """
        Partially updates company econ report settings by `name`. It never inserts: a name with no match
        is a per-record 404. Omitted `headers`, `allWellsAgg` and `rollUpEachLevel` are unchanged; a
        provided `headers` replaces the whole ordered list.

        Sends `data` in one request; the API states no record cap. One document (a dict) is sent as a
        one-item list. An empty `data` raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/patch-econ-report-settings

        Example data:
        [
            {
                "name": "Example",
                "headers": [
                    "string"
                ],
                "allWellsAgg": true,
                "rollUpEachLevel": true
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
        return self._patch_documents(ECON_REPORT_SETTINGS, data)

    def delete_econ_report_setting_by_id(self, econ_report_setting_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one company econ report setting from its id.

        https://docs.api.combocurve.com/api/delete-econ-report-settings-by-id

        Returns the headers from the delete response.
        """
        return self._delete_document(ECON_REPORT_SETTINGS, econ_report_setting_id)
