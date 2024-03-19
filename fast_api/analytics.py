from typing import Optional, Dict, List, Tuple
import json
import pandas as pd
from mongo_db import MongoDB


class CreateAnalytics:
    """ Creates analytics for API """
    def __init__(self, db_client: MongoDB):
        self.db_client = db_client

    def _create_rolling_stat(
            self,
            df: pd.DataFrame,
            new_col_name: str,
            group_by: List[str]
            ) -> pd.DataFrame:
        """
        Creates rolling statistics
        Parameters:
        ------------
        df: pd.DataFrame - DataFrame from MongoDB
        new_col_name: str - name of new column with rolling data
        group_by: List[str] - features for analytics
        """
        cutoff = pd.to_datetime("today") - pd.Timedelta(days=7)
        analytic_df = (
            df[df['created_at'] >= cutoff]
            .sort_values(by=['created_at'], ascending=True)
            .reset_index(drop=True)
            .tail(500)
            # can take max 500 records its sorted from oldest, needs to be tail
        )
        analytic_df[new_col_name] = (
            analytic_df
            .groupby(group_by)['created_at']
            .diff()
            .fillna(pd.Timedelta(days=0))
            .reset_index(drop=True)
        )  # creates rolling stats
        analytic_df[new_col_name] = (
            analytic_df[new_col_name].apply(lambda x: x.seconds)
        )  # converts to seconds for API formatting
        return (
            analytic_df
            .groupby(group_by, as_index=False)[new_col_name]
            .mean()
        )  # returns mean wit respect to taxonomy

    def _query_db_data(self, repos: List[str]) -> pd.DataFrame:
        """
        Queries data from database
        Parameters:
        -----------
        repos: List[str] - list of repos for analytics
        """
        query = {"repo": {"$in": repos}}
        cursor = self.db_client.query_db(query=query)
        return pd.DataFrame(list(cursor))

    def create_analytics(
            self,
            repos: List[str]
            ) -> Tuple[Dict[str, float], pd.DataFrame]:
        """
        Creates rolling analytics
        repos: List[str] - list of repos for analytics
        """

        df = self._query_db_data(repos)
        mean_repo_type = self._create_rolling_stat(
            df,
            "time_between_events_by_repo_type", 
            group_by=['repo', 'type']
            )
        mean_repo = self._create_rolling_stat(
            df,
            "time_between_events_by_repo", 
            group_by=['repo']
            )
        mean_type = self._create_rolling_stat(
            df,
            "time_between_events_by_type", 
            group_by=['type']
            )
        
        return {
            "mean_repo": mean_repo.to_json(orient="index"),
            "mean_type": mean_type.to_json(orient="index"),
            "mean_repo_type": mean_repo_type.to_json(orient="index"),
        }
