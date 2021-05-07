import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

from werkzeug.exceptions import abort


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    click.echo("loaded db")
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
@with_appcontext
def init_db_command():
    """ Clear the exisiting data and create new tables."""
    init_db()
    click.echo("initialized the database")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def get_tournament(tid):
    t = get_db().execute("SELECT * FROM tournament WHERE id = ?", (tid,)).fetchone()

    if t is None:
        abort(404, f"Tournament id {tid} does not exist")

    return t


def get_player(pid):
    return get_db().execute("SELECT * FROM player WHERE id = ?", (pid,)).fetchone()


def get_players(tid):
    return (
        get_db()
        .execute(
            "SELECT * FROM player WHERE tid = ?"
            "ORDER BY score DESC, sos DESC, esos DESC",
            (tid,),
        )
        .fetchall()
    )


def get_active_players(tid):
    return (
        get_db()
        .execute(
            "SELECT * FROM player WHERE tid = ? AND active = 1 ORDER BY score DESC, sos DESC, esos DESC",
            (tid,),
        )
        .fetchall()
    )


def get_matches(tid, rnd):
    """
    tid: Tournament ID
    round: Round to get matches from
    """
    return (
        get_db()
        .execute(
            """SELECT match.id, match.corp_id, match.runner_id, match.corp_score,
            match.runner_score, match.match_num,
            corp_plr.p_name as corp_player, runner_plr.p_name as runner_player
            FROM match
            LEFT JOIN player corp_plr
            ON match.corp_id = corp_plr.id
            LEFT JOIN player runner_plr
            ON match.runner_id = runner_plr.id
            WHERE match.tid = ? AND match.rnd = ?""",
            (
                tid,
                rnd,
            ),
        )
        .fetchall()
    )


def get_rnd_list(tid):
    return (
        get_db()
        .execute(
            """
            SELECT DISTINCT(rnd) as rnds FROM match WHERE tid=?
            """,
            (tid,),
        )
        .fetchall()
    )