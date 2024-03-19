from typing import Optional, Dict, List, Tuple
import datetime
import pymongo
from models import DatabaseModel


class MongoDB(DatabaseModel):
    """ Handles communication with MongoDB """
    def __init__(
            self,
            connection_string: str, 
            db_name: Optional[str] = "github_activity_monitoring",
            collection_name: Optional[str] = "repo_activity"
            ):
        """
        Parameters:
        -----------
        client = Mongo DB client
        """
        self.connection_string = connection_string
        self.db_name = db_name
        self.collection_name = collection_name

    def _get_database(self):
        """ 
        creates database is it does not exists
        or connects to the existing database
        """
        # CREATE DATABASE IF NOT EXIST ELSE GET DATABASE
        if self.db_name not in self.client.list_database_names():
            return self.client[self.db_name]
        else:
            return self.client.get_database(self.db_name)

    def _get_collection(self):
        # CREATE TABLE IF NOT EXISTS ELSE GET TABLE
        """ 
        creates collection is it does not exists
        or connects to the existing collection
        """
        if self.collection_name not in self.database.list_collection_names():
            return self.database[self.collection_name]
        else:
            return self.database.get_collection(self.collection_name)

    def _setup_database(
            self
            ) -> Tuple[
                pymongo.database.Database,
                pymongo.collection.Collection
                ]:
        """ Creates database if not exists """
        self.database = self._get_database()
        self.collection = self._get_collection()
        return self.database, self.collection

    def startup_database_connection(self) -> pymongo.mongo_client.MongoClient:
        """ startups database connection """
        self.client = pymongo.MongoClient(self.connection_string)
        print("Connection started....")
        return self.client

    def query_db(
            self,
            query: Dict[str, str], 
            other: Optional[Dict[str, str]] = None
            ) -> pymongo.collection.Cursor:
        """
        Queries mongo database collection
        Parameters:
        -----------
        query: Dict[str, str] - query to the database
        other: Optional[Dict[str, str]] -   data for which column 
                                            it should be queried
        """
        if other is not None:
            return self.collection.find(query, other)
        else:
            return self.collection.find(query)

    def _close_database_connection(self) -> pymongo.database.NoReturn:
        """ closes database connection """
        self.client.close()
        print("Connection closed....")

    def insert_many(
            self,
            data: List[Dict[str, str | datetime.datetime]]
            ) -> pymongo.collection.InsertManyResult:
        """
        Inserts multiple records to the database
        Parameters:
        ------------
        dataL List[Dict[str, str|datetime.datetime]] - should be inserted as:
        [
            {
                "id": 123,
                "created_at": datetime.datetime(2023, 1, 1),
                "repo": "repo_name",
                "type": "activity type"
            },
            {
                "id": 123,
                "created_at": datetime.datetime(2023, 1, 1),
                "repo": "repo_name",
                "type": "activity type"
            },
            {
                "id": 123,
                "created_at": datetime.datetime(2023, 1, 1),
                "repo": "repo_name",
                "type": "activity type"
            }
        ]
        """
        return self.collection.insert_many(data)
