import flask_login
from flask import (
    Flask,
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

bp = Blueprint("auth", __name__)


@bp.route("/login")
def login():
    pass


@bp.route("/signup")
def register():
    pass


@bp.route("/logout")
def logout():
    pass
