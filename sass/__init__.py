import os
from config import Config
from flask import Flask
from json import load
from flask_sqlalchemy import SQLAlchemy


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = "hahasosecurejustaphrase"
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    
    app.config.from_object(Config)
    
    from . import db_ops

    db_ops.init_app(app)

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