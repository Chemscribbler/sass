import os

from flask import Flask
from google.cloud import storage


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    DB_PATH = os.path.join(app.instance_path, "sass.sqlite")
    try:
        from shutil import copyfile

        DB_PATH = "/tmp/sass.sqlite"
        copyfile(os.path.join(app.instance_path, "sass.sqlite"), DB_PATH)
    except:
        pass
    app.config.from_mapping(
        SECRET_KEY="jeff_is_great",
        DATABASE=DB_PATH,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db

    db.init_app(app)

    from . import manager

    app.register_blueprint(manager.bp)

    return app
