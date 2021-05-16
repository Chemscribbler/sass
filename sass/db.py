import datetime
from re import T
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from configparser import ConfigParser

import click
from flask import current_app, g
from flask.cli import with_appcontext
from sqlalchemy.sql.expression import distinct, insert, select, table, text, update
from sqlalchemy.sql.schema import MetaData, Table
from sqlalchemy import func

from werkzeug.exceptions import abort

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


def init_db():
    db = get_db()
    with current_app.open_resource("postgres.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
@with_appcontext
def init_db_command():
    """ Clear the exisiting data and create new tables."""
    init_db()
    click.echo("initialized the database")


def init_app(app):
    app.cli.add_command(init_db_command)


def get_tournaments():
    return get_db().execute("SELECT * FROM tournament ORDER BY id DESC")


def get_tournament(tid):
    db = get_db()
    tourney = metadata.tables["tournament"]
    t = db.execute(select(tourney).where(tourney.c.id == tid)).fetchone()

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
    player = metadata.tables["player"]
    with db.begin() as conn:
        conn.execute(
            insert(player).values(
                p_name=name, tid=tid, corp_id=corp_id, runner_id=runner_id
            )
        )
    return name


def get_player(pid):
    return (
        get_db()
        .execute(text("SELECT * FROM player WHERE id = :pid"), {"pid": pid})
        .fetchone()
    )


def get_players(tid):
    db = get_db()
    player = metadata.tables["player"]
    return db.execute(
        select(player)
        .where(player.c.tid == tid)
        .order_by(player.c.score.desc(), player.c.sos.desc(), player.c.esos.desc())
    ).fetchall()


def get_active_players(tid):
    return (
        get_db()
        .execute(
            text(
                "SELECT * FROM player WHERE tid = :tid AND active = 1 ORDER BY score DESC, sos DESC, esos DESC"
            ),
            {"tid": tid},
        )
        .fetchall()
    )


def db_drop_player(pid):
    with get_db().begin() as conn:
        conn.execute(text("UPDATE player SET active = 0 WHERE id = :pid"), {"pid": pid})


def db_undrop_player(pid):
    with get_db().begin() as conn:
        conn.execute(text("UPDATE player SET active = 1 WHERE id = :pid"), {"pid": pid})


def remove_player(pid):
    db = get_db()
    with db.begin() as conn:
        conn.execute(text("DELETE FROM player WHERE id = :pid"), {"pid": pid})


def get_matches(tid, rnd):
    """
    tid: Tournament ID
    round: Round to get matches from
    """
    return (
        get_db()
        .connect()
        .execute(
            text(
                """SELECT match.id, match.corp_id, match.runner_id, match.corp_score,
            match.runner_score, match.match_num,
            corp_plr.p_name as corp_player, runner_plr.p_name as runner_player
            FROM match
            LEFT JOIN player corp_plr
            ON match.corp_id = corp_plr.id
            LEFT JOIN player runner_plr
            ON match.runner_id = runner_plr.id
            WHERE match.tid = :tid AND match.rnd = :rnd
            ORDER BY match.match_num"""
            ),
            {
                "tid": tid,
                "rnd": rnd,
            },
        )
        .fetchall()
    )


def get_match(mid):
    db = get_db()
    match = metadata.tables["match"]
    return db.connect().execute(select(match).where(match.c.id == mid)).fetchone()


def get_rnd_list(tid):
    return (
        get_db()
        .connect()
        .execute(
            text("SELECT DISTINCT(rnd) as rnds FROM match WHERE tid=:tid"),
            {"tid": tid},
        )
        .fetchall()
    )


def get_last_rnd(tid):
    q = (
        get_db()
        .connect()
        .execute(
            func.max(metadata.tables["match"].c.rnd).where(
                metadata.tables["match"].c.tid == tid
            )
        )
        .execute("SELECT MAX(rnd) as rnd FROM match WHERE tid=?", (tid,))
        .fetchone()
    )
    return q["rnd"]


def rnd_one_start(tid):
    with get_db().begin() as conn:
        tourn = metadata.tables["tournament"]
        conn.execute(update(tourn).where(tourn.c.id == tid).values(current_rnd=1))


def delete_pairings(tid, rnd):
    db = get_db()
    with db.begin() as conn:
        conn.execute(
            text("DELETE FROM match WHERE tid=:tid AND rnd = :rnd"),
            {"tid": tid, "rnd": rnd},
        )
        conn.execute(
            text("DELETE FROM player WHERE is_bye = 1 AND tid = ?"), {"tid": tid}
        )


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