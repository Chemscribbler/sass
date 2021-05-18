import datetime
<<<<<<< Updated upstream
import sqlite3
=======
from re import T
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import os
>>>>>>> Stashed changes

import click
from flask import current_app, g
from flask.cli import with_appcontext

from werkzeug.exceptions import abort


def get_db():
    if "db" not in g:
<<<<<<< Updated upstream
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
=======
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
>>>>>>> Stashed changes
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
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


def get_tournaments():
    return get_db().execute("SELECT * FROM tournament ORDER BY id DESC").fetchall()


def get_tournament(tid):
    t = get_db().execute("SELECT * FROM tournament WHERE id = ?", (tid,)).fetchone()

    if t is None:
        abort(404, f"Tournament id {tid} does not exist")

    return t


def create_tournament(title, date=datetime.date.today()):
    db = get_db()
    db.execute(
        "INSERT INTO tournament (title, date) VALUES (?, ?)",
        (
            title,
            date,
        ),
    )
    db.commit()
    tournaments = db.execute(
        "SELECT * FROM tournament WHERE title = ? AND date = ?",
        (
            title,
            date,
        ),
    ).fetchall()
    selector = 0
    for t in tournaments:
        selector = t["id"]
    return selector


def add_player(tid, name, corp_id, runner_id):
    db = get_db()
    db.execute(
        "INSERT INTO player (p_name, tid, corp_id, runner_id)" "VALUES (?, ?, ?, ?)",
        (name, tid, corp_id, runner_id),
    )
    db.commit()
    return name


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


def drop_player(pid):
    db = get_db()
    db.execute("UPDATE player SET active = 0 WHERE id = ?", (pid,))
    db.commit()


def undrop_player(pid):
    db = get_db()
    db.execute("UPDATE player SET active = 1 WHERE id = ?", (pid,))
    db.commit()


def remove_player(pid):
    db = get_db()
    db.execute("DELETE FROM player WHERE id = ?", (pid,))
    db.commit()


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


def get_match(mid):
    return get_db().execute("SELECT * FROM match WHERE id = ?", (mid,)).fetchone()


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


def rnd_one_start(tid):
    db = get_db()
    db.execute("UPDATE tournament SET current_rnd = 1 WHERE id = ?", (tid,))
    db.commit()


def delete_pairings(tid, rnd):
    db = get_db()
    db.execute(
        "DELETE FROM match WHERE tid=? AND rnd = ?",
        (
            tid,
            rnd,
        ),
    )
    db.commit()


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