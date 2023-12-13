from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class Projects(APIBase):
    ######
    # URLs
    ######

    def get_projects_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for projects.
        """
        url = f'{self.API_BASE_URL}/projects'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_by_id_url(self, project_id: str) -> str:
        """
        Returns the API url for a specific project from its project id.
        """
        base_url = self.get_projects_url()
        return f'{base_url}/{project_id}'


    ###########
    # API calls
    ###########


    def get_projects(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of projects.

        https://docs.api.combocurve.com/#25b8ab6b-5c03-49bc-ba57-06f063b31a97

        Example response:
        [
            {
                "createdAt": "2020-01-21T16:58:08.986Z",
                "id": "5e5981b9e23dae0012624d72",
                "name": "Test project",
                "updatedAt": "2020-01-21T17:58:08.986Z"
            }
        ]
        """
        url = self.get_projects_url(filters)
        params = {'take': GET_LIMIT}
        projects = self._get_items(url, params=params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(projects, order)


    def post_projects(self, data: ItemList) -> ItemList:
        """
        Creates a new project.

        https://docs.api.combocurve.com/#a89937e7-92ed-4184-a4c0-9009732cd4e8

        Example request:
        [
            {
                "name": "Test project"
            }
        ]

        Example response:
        [
            {
                "generalErrors": [
                    {
                        "name": "ValidationError",
                        "message": "The field 'id' is required.",
                        "location": "In body of request at position [0]"
                    },
                    {
                        "name": "ValidationError",
                        "message": "The field 'dataSource' is required.",
                        "location": "In body of request at position [2]"
                    }
                ],
                "results": [
                    {
                        "status": "Success",
                        "code": 200,
                        "name": "Acme Royalties 2021-10-28",
                        "id": "61698aa08eca904d9cc5b622"
                    },
                    {
                        "status": "Success",
                        "code": 200,
                        "name": "Acme Royalties 2021-10-28",
                        "id": "61698aa08eca904d9cc5b623"
                    }
                ],
                "failedCount": 2,
                "successCount": 2
            }
        ]
        """
        url = self.get_projects_url()
        projects = self._post_items(url, data)

        return projects


    def get_project_by_id(self, id: str) -> Item:
        """
        Returns a specific project from its project id.

        https://docs.api.combocurve.com/#3d58f1b6-41f5-4bf0-9d79-613f14d08bed

        Example response:
        {
            "createdAt": "2020-01-21T16:58:08.986Z",
            "id": "5e5981b9e23dae0012624d72",
            "name": "Test project",
            "updatedAt": "2020-01-21T17:58:08.986Z"
        }
        """
        url = self.get_project_by_id_url(id)
        projects = self._get_items(url)

        return projects[0]
