from abc import ABC, abstractmethod


class DatabaseModel(ABC):
    @abstractmethod
    def query_db():
        raise NotImplementedError(
            "Implement method query_db() for querying data"
        )

    @abstractmethod
    def insert_many():
        raise NotImplementedError(
            "Implement method insert_many() to insert data into database"
        )

    @abstractmethod
    def startup_database_connection():
        raise NotImplementedError(
            """
            Implement method startup_database_connection()
            to start connection
            """
        )
