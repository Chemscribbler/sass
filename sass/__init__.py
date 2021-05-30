import os

from flask import Flask
from json import load


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
    from . import docs
    from . import auth

    app.register_blueprint(manager.bp)
    app.register_blueprint(docs.bp)
    app.register_blueprint(auth.bp)

    app.jinja_env.globals.update(get_id=get_id)
    app.jinja_env.globals.update(clean_bias=clean_bias)
    return app


def get_id(id_name):
    with open("ids.json", "r") as f:
        ids = load(f)
        for id in ids:
            if id["name"] == id_name:
                return {"name": id["name"], "faction": id["faction"]}


def clean_bias(bias_value):
    if bias_value > 0:
        return f"Corp +{bias_value}"
    if bias_value < 0:
        return f"Runner +{abs(bias_value)}"
    else:
        return "None"