import datetime
import operator
from re import T
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import os
from sass.db_grabber import get_db, metadata
import click
from flask import current_app, g
from flask.cli import with_appcontext
from sqlalchemy.sql.expression import distinct, insert, select, table, text, update
from sqlalchemy.sql.schema import MetaData, Table
from sqlalchemy import func
import sqlparse
from sass import db_ops
from werkzeug.exceptions import abort


def init_db():
    db = get_db()
    with current_app.open_resource("postgres.sql", "r") as f:
        for statement in sqlparse.split(f):
            db.connect().execute(text(statement))


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
        text(
            """
            INSERT INTO tournament (title, t_date)
            VALUES (:title, :date)
            """
        ),{"title":title, "date":date}
    )
    return db.execute(
        text(
        """
        SELECT * from tournament
        WHERE title = :title
        """
        ),{"title":title}
    ).fetchone()
    
    # db = get_db()
    # tournament_table = metadata.tables["tournament"]
    # with db.begin() as conn:
    #     stmt = (
    #         insert(tournament_table)
    #         .values(title=title, t_date=date)
    #         .returning(tournament_table)
    #     )
    #     return conn.execute(stmt).fetchone()


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
    # player = metadata.tables["player"]
    # return db.execute(
    #     select(player)
    #     .where(player.c.tid == tid)
    #     .where(player.c.is_bye == False)
    #     .order_by(player.c.score.desc(), player.c.sos.desc(), player.c.esos.desc())
    # ).fetchall()

    return db.execute(
        text(
            """
            SELECT id, tid, name, corp_id, runner_id, score, sos, esos, bias, active,
            sum(coalesce(corp_points,0)) AS corp_points,
            sum(coalesce(runner_points,0)) AS runner_points
            from(
                select p.id as id, p.tid as tid, p.p_name as name, p.corp_id as corp_id, p.runner_id as runner_id,
                p.score as score, p.sos as sos, p.esos as esos, p.bias as bias, p.active as active,
                sum(m.corp_score) AS corp_points, 0 AS runner_points
                FROM player p
                LEFT JOIN match m on p.id = m.corp_id
                WHERE p.tid = :tid and p.is_bye = false
                group by p.id
                UNION
                SELECT p.id as id, p.tid as tid, p.p_name as name, p.corp_id as corp_id, p.runner_id as runner_id,
                p.score as score, p.sos as sos, p.esos as esos, p.bias as bias, p.active as active,
                0 AS corp_points, sum(m.runner_score) AS runner_points
                FROM player p
                LEFT JOIN match m on p.id = m.runner_id
                WHERE p.tid = :tid and p.is_bye=false
                group by p.id
            ) as t
            group by t.id, t.name, t.tid, t.corp_id, t.runner_id, t.score, t.sos, t.esos, t.bias, t.active
            order by t.score DESC, t.sos DESC, t.esos DESC 
            """
        ),
        {"tid": tid},
    ).fetchall()


def get_active_players(tid):
    return (
        get_db()
        .execute(
            text(
                "SELECT * FROM player WHERE tid = :tid AND active = true ORDER BY score DESC, sos DESC, esos DESC"
            ),
            {"tid": tid},
        )
        .fetchall()
    )


def db_drop_player(pid):
    with get_db().begin() as conn:
        conn.execute(
            text("UPDATE player SET active = false WHERE id = :pid"), {"pid": pid}
        )


def db_undrop_player(pid):
    with get_db().begin() as conn:
        conn.execute(
            text("UPDATE player SET active = true WHERE id = :pid"), {"pid": pid}
        )


def remove_player(pid):
    db = get_db()
    with db.begin() as conn:
        conn.execute(text("DELETE FROM player WHERE id = :pid"), {"pid": pid})


def update_player(pid, name, corp_id, runner_id):
    db = get_db()
    plr = metadata.tables["player"]
    with db.begin() as conn:
        conn.execute(
            update(plr)
            .where(plr.c.id == pid)
            .values(p_name=name, corp_id=corp_id, runner_id=runner_id)
        )


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
            text("SELECT DISTINCT(rnd) as rnds FROM match WHERE tid=:tid ORDER BY rnd"),
            {"tid": tid},
        )
        .fetchall()
    )


def get_last_rnd(tid):
    q = (
        get_db()
        .connect()
        .execute(text("SELECT MAX(rnd) as rnd FROM match WHERE tid=:tid"), {"tid": tid})
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
            text("UPDATE player SET active = false WHERE is_bye = true AND tid = :tid"),
            {"tid": tid},
        )


def switch_tournament_activity(tid):
    db = get_db()
    tourn = metadata.tables["tournament"]
    with db.begin() as conn:
        t = conn.execute(select(tourn).where(tourn.c.id == tid)).fetchone()
        if t.active:
            setto = False
        else:
            setto = True
        conn.execute(update(tourn).where(tourn.c.id == tid).values(active=setto))


def get_json(tid):
    t = get_tournament(tid)
    p = get_players(tid)
    t_json = {
        "name": t["title"],
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
                "name": player["name"],
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


def get_stats(tid):
    db = get_db()
    with db.begin() as conn:
        match_table = conn.execute(
            text(
                """select match.id, match.corp_id, match.runner_id, match.corp_score, match.runner_score,
                corp_plr.p_name, corp_plr.corp_id, corp_plr.is_bye,
                runner_plr.p_name, runner_plr.runner_id, runner_plr.is_bye
                FROM match
                LEFT join player corp_plr
                ON match.corp_id = corp_plr.id
                LEFT JOIN player runner_plr
                ON match.runner_id = runner_plr.id
                WHERE corp_plr.is_bye = false AND runner_plr.is_bye = false AND match.tid = :tid""",
                {"tid": tid},
            ).fetchall()
        )
    return match_table
