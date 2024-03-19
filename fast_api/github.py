import time
from typing import Optional, Dict, List, Set
import datetime
import requests
from requests.models import Response
from mongo_db import MongoDB


class GithubAPI:
    """ Github api communication """
    def __init__(
            self,
            headers: Optional[Dict[str, str]] = {
                'X-GitHub-Api-Version': '2022-11-28',
                'Accept': 'application/json',
            },
            token: Optional[str] = "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",
            base_url: Optional[str] = "https://api.github.com/repos"
            ) -> None:

        """
        Parameters:
        -----------
        headers: Optional[Dict[str, str]] = {
            "X-GitHub-Api-Version": "2022-11-28},
            'Accept': 'application/json'
            }
        token: Optional[str] = "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"
        base_url: Optional[str] = "https://api.github.com/repos"
        """       
        self.headers = headers.update({'Authorization': f'Bearer {token}'})
        self.base_url = base_url

    def _get_max_page(self, response: Response) -> int:
        """
        Returns the last page of events API
        Parameters:
        -----------
        response: Response - API response

        Returns:
        --------
        max_page: int - number of the last page in API request
        """
        try:
            links = response.headers['Link'].split(",")
            for link in links:
                if 'rel="last"' in link:
                    url = link.split(">")[0][2:]
                    max_page = url.split("page=")[-1]
                    return int(max_page)
        except (KeyError, TypeError):
            return 1  # there is only one page

    def _get_num_reqeusts_left(self, response: Response) -> int:
        """
        Gets num rate limit_requests left
        Returns:
        -----------
        int: requests.models.Response -
            number of API calls that app has left before being rate limited,
        """
        return int(response.headers['X-RateLimit-Remaining'])


    def _get_rate_limit_date_renewed(
            self,
            response: Response
            ) -> datetime.datetime:
        """
        Gets time when app will be eligible to send requests again
        Returns:
        -----------
        datetime.datetime: when will the app's number of
        API requests be reset to original.
        """
        return datetime.datetime.fromtimestamp(
                float(response.headers['X-RateLimit-Reset'])
            )

    def _flatten_list(
            self,
            list_responses: List[List[Dict[str, str]]]
            ) -> List[Dict[str, str]]:
        """
        Flattens API responses to List[Dict[str, str]]
        list_responses: List[List[Dict[str, str]]] - list of responses from API
        """
        return [
            response
            for responses in list_responses
            for response in responses
        ]

    def _pause_when_ratelimited(self, response: Response) -> None:
        """
        If being rate limited, this will stop app from communicating with user
        until requests are again available
        """
        time_requests_renewed = self._get_rate_limit_date_renewed(response)
        time_diff = (datetime.datetime.now() - time_requests_renewed).seconds
        print(f"\n Rate limited for another: {time_diff} seconds \n")
        return time.sleep(time_diff)

    def _get_repo_activity(
            self,
            owner: str,
            repository: str,
            num_page: int = 1
            ) -> Response:
        """
        Gets response from Github API about activity
        in repository given its owner and repository name
        Parameters:
        -----------
        owner: str - name of repository owner
        repository: str - name of the repository
        num_page: int = 1 - number of page_requested
        """

        url = f"{self.base_url}/{owner}/{repository}/events?per_page=500&page={num_page}"
        response = requests.get(url=url, headers=self.headers)
        num_requests_left = self._get_num_reqeusts_left(response)
        if num_requests_left == 0:
            return self._pause_when_ratelimited(response)
        return response

    def _get_all_records(self, owner: str,  repository_name: str) -> Response:
        """
        Gets response from Github API about activity 
        in repository given its owner and repository name
        Parameters:
        -----------
        owner: str - name of repository owner
        repository: str - name of the repository
        num_page: int = 1 - number of page_requested
        """
        first_request = self._get_repo_activity(owner, repository_name)
        num_pages = self._get_max_page(first_request)
        all_responses = [
            self._get_repo_activity(owner, repository_name, num_page=i).json()
            for i in range(2, num_pages + 1)
        ]
        return self._flatten_list(all_responses)

    def get_all_records(
            self,
            owner: str,
            repository_name: str
            ) -> List[Dict[str, str|datetime.datetime]]:
        """
        Prepares data for MongoDB
        Parameters:
        -----------
        responses: requests.models.Response - responses from API call
        """

        responses = self._get_all_records(owner, repository_name)
        return [
                    {
                        "id": response.get("id"),
                        "type": response.get("type"),
                        "created_at": datetime.datetime.fromisoformat(
                            response.get("created_at")[:-1]
                            ),
                        "repo": response['repo']['url'].split("/")[-1]
                    }
                    for response in responses
            ]


def filter_new_entries(
        api_data_set,
        api_data,
        db_data_set
        ) -> List[Dict[str, str]]:
    """
    Filters out new entries by comparing database entries
    and new ones from API. Then it filters out
    Parameters:
    -----------
    api_data_set: Set[int] - unique event ids from API
    api_data: List[Dict[str, str]] - data from API
    db_data_set: Set[int]
    """
    new_records = api_data_set.difference(db_data_set)
    return [i for i in api_data if i.get("id") in new_records]


def create_set(lst: List[Dict[str, int]]) -> Set[int]:
    """
    Creates set of unique records from API response
    Parameters:
    -----------
    lst: List[Dict[str, int]] - response from API
    """
    return set([record.get("id") for record in lst])


def add_new_records(
        db_client: MongoDB,
        api_client: GithubAPI,
        owner: str,
        repository_name: str
        ):
    """
    Adds only new records from API to database by
    comparing existing records and new ones from API.
    Parameters:
    -----------
    db_client: MongoDB - MongoDB database collection
    api_client: GithubAPI - github API client
    repository_name: str - name fo github repository
    """

    api_data = api_client._get_repo_activity(owner, repository_name).json()
    db_data = list(db_client.query_db({"repo": repository_name}))
    db_data_as_set = create_set(db_data)
    api_data_as_set = create_set(api_data)
    to_be_fetched_data = filter_new_entries(
        api_data_as_set, api_data,  db_data_as_set
        )
    if to_be_fetched_data:
        return db_client.insert_many(to_be_fetched_data)
