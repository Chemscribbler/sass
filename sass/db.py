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


def get_last_rnd(tid):
    q = (
        get_db()
        .execute("SELECT MAX(rnd) as rnd FROM match WHERE tid=?", (tid,))
        .fetchone()
    )
    return q["rnd"]


def get_json(tid):
    t = get_tournament(tid)
    p = get_players(tid)
    t_json = {
        "name": t["title"],
        "date": t["t_date"],
        "cutToTop": 0,
        "preliminaryRounds": get_last_rnd(tid),
        "players": [],
        "rounds": [],
        "uploadedFrom": "AesopsTables",
        "links": [
            {
                "rel": "schemaderivedfrom",
                "href": "http://steffens.org/nrtm/nrtm-schema.json",
            },
            {"rel": "uploadedfrom", "href": "https://github.com/Chemscribbler/sass"},
        ],
    }
    for i, player in enumerate(p):
        t_json["players"].append(
            {
                "id": player["id"],
                "name": player["p_name"],
                "rank": i + 1,
                "corpIdentity": player["corp_id"],
                "runnerIdentity": player["runner_id"],
                "matchPoints": player["score"],
                "strengthOfSchedule": player["sos"],
                "extendedStrengthOfSchedule": player["esos"],
                "sideBalance": player["bias"],
            }
        )
    for i in range(get_last_rnd(tid)):
        matches = []
        for match in get_matches(tid, i + 1):
            matches.append(
                {
                    "table": match["match_num"],
                    "corp": {"id": match["corp_id"], "score": match["corp_score"]},
                    "runner": {
                        "id": match["runner_id"],
                        "score": match["runner_score"],
                    },
                }
            )
        t_json["rounds"].append(matches)

    return t_json