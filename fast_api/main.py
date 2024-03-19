from typing import List, Dict
import pandas as pd
from fastapi import FastAPI, Response
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from github import GithubAPI, add_new_records
from mongo_db import MongoDB
from analytics import CreateAnalytics

app = FastAPI()

CONNECTION_STRING = "mongodb+srv://statbayesopt:fp3uuC0iadCh5cT6@cluster0.nplmv0i.mongodb.net/"  # from prague
db_client = MongoDB(CONNECTION_STRING)
db_client.startup_database_connection()
github_api_client = GithubAPI()


class OwnerRepoJSON(BaseModel):
    owners: List[str]
    repos: List[str]


def refresh_db_data(db_client, api_client, owner, repository_name):
    """
    Updates or loads data to database
    Parameters:
    -----------
    db_client: MongoDB(DatabaseModel) - database client
    api_client: GithubAPI - api client
    owner: str - owner name
    repository_name: str - name of repository
    """
    database, collection = db_client._setup_database()
    unique_repositories = [repo for repo in collection.find().distinct("repo")]
    if repository_name in unique_repositories:
        # update only new records to the database
        return add_new_records(
            db_client,
            api_client,
            owner,
            repository_name
        )
    else:
        all_records = api_client.get_all_records(owner, repository_name)
        return db_client.insert_many(all_records)


@app.post("/get_repo_activity/")
async def get_analytics(
    owner_repo_json: OwnerRepoJSON
    ) -> Dict[str, Dict[str, str]]:

    """
    Gets analytics for repositories
    Parameters:
    -----------
    owner_repo_json: Dict[str, List[str]] - {
        'owners': ['mongodb', 'Nixtla', 'opencv']
        'repos': ['mongo', 'statsforecast', 'opencv']
    }
    Returns:
    --------
    Dict[str: Dict[str, str or float]] - Repo events analytics
    """

    owners = owner_repo_json.owners
    repos = owner_repo_json.repos
    print(owners, repos)

    if len(owners) > 5:  # task description max config repos
        raise ValueError("Too many repos. Maximum of 5 can be configured")

    for owner, repo in zip(owners, repos):  # Updates data
        refresh_db_data(
            db_client,
            github_api_client,
            owner,
            repo
        )
    analytics = CreateAnalytics(db_client)
    stats = analytics.create_analytics(repos)
    return JSONResponse(content=stats)
