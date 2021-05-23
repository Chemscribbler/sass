from markdown import markdown

from flask import Blueprint, render_template

bp = Blueprint("docs", __name__)


@bp.route("/howto")
def how_to():
    with open("sass/docs/howto.md", "r") as f:
        text = f.read()
        html = markdown(text)
    return render_template("markdown_page.html", markdown_content=markdown(html))


@bp.route("/about")
def about():
    with open("sass/docs/about.md", "r") as f:
        text = f.read()
        html = markdown(text)
    return render_template("markdown_page.html", markdown_content=markdown(html))