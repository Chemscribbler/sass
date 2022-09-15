from flask import g
from sqlalchemy.sql.schema import MetaData
from configparser import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import os
metadata = MetaData()
basedir = basedir = os.path.abspath(os.path.dirname(__file__))


def get_db():
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    g.db = create_engine(SQLALCHEMY_DATABASE_URI)
    # print(g)
    metadata.reflect(bind=g.db)
    return g.db
    # return db
