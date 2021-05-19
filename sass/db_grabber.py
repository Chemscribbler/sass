from flask import g
from sqlalchemy.sql.schema import MetaData
from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

metadata = MetaData()


def get_db():
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