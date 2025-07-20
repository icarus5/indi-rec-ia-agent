import os
from sqlalchemy.engine import URL

class SQLServerConfig:
    def __init__(self):
        self.connection_url = URL.create(
            "mssql+pyodbc",
            username=os.getenv("AZR_DB_USERNAME"),
            password=os.getenv("AZR_DB_PASSWORD"),
            host=os.getenv("AZR_DB_HOSTNAME"),
            database=os.getenv("AZR_DB_DATABASE"),
            port=os.getenv("AZR_DB_PORT"),
            query={
                "driver": "ODBC Driver 18 for SQL Server",
                "TrustServerCertificate": "yes",
                "charset": "utf8",
            },
        )

    def get_connection_url(self):
        return self.connection_url