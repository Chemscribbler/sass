from flask import g
from sqlalchemy.sql.schema import MetaData
from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import os

metadata = MetaData()


def get_db():
    if True:
        if "db" not in g:
            config = ConfigParser()
            config.read("config.ini")
            g.db = create_engine(
                URL.create(
                    drivername="postgresql+pg8000",
                    username=config["localdev"]["user"],
                    password=config["localdev"]["password"],
                    database=config["localdev"]["database"],
                    port=config["localdev"]["port"],
                    host=config["localdev"]["host"],
                )
            )
        metadata.reflect(bind=g.db)
        return g.db

    else:
        if "db" not in g:
            db_user = os.environ["DB_USER"]
            db_pass = os.environ["DB_PASS"]
            db_name = os.environ["DB_NAME"]
            db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
            cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]
            g.db = create_engine(
                URL.create(
                    drivername="postgresql+pg8000",
                    username=db_user,
                    password=db_pass,
                    database=db_name,
                    query={
                        "unix_sock": "{}/{}/.s.PGSQL.5432".format(
                            db_socket_dir, cloud_sql_connection_name
                        )
                    },
                )
            )
        metadata.reflect(bind=g.db)
        return g.db