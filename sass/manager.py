import sqlite3
from datetime import date
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

from werkzeug.exceptions import abort

from sass.db import get_db, get_players, get_matches, get_tournament
from sass.tournament import pair_round

bp = Blueprint("manager", __name__)


@bp.route("/")
def hello():
    return "Hello, World!"


@bp.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        t_name = request.form["title"]
        t_date = request.form["date"]
        if t_date is None:
            t_date = date.today().strftime("%Y-%m-%d")
        db = get_db()
        error = None

        if t_name is None:
            error = "No tournament name"

        if error is None:
            db.execute(
                "INSERT INTO tournament (title, t_date) VALUES (?, ?)",
                (
                    t_name,
                    t_date,
                ),
            )
            db.commit()
            tournaments = db.execute(
                "SELECT * FROM tournament WHERE title = ? AND t_date = ?",
                (
                    t_name,
                    t_date,
                ),
            ).fetchall()
            selector = 0
            for t in tournaments:
                selector = t["id"]
            return redirect(url_for("manager.main", tid=selector))

        flash(error)

    return render_template("create.html")


@bp.route("/<int:tid>")
@bp.route("/<int:tid>/standings")
def main(tid):
    t = get_tournament(tid)
    plrs = get_players(tid)
    return render_template("t_index.html", data={"t": t, "players": plrs})


@bp.route("/<int:tid>/register", methods=["GET", "POST"])
def register(tid):
    t = get_tournament(tid)
    if request.method == "POST":
        name = request.form["name"]
        corp_id = request.form["corp_id"]
        runner_id = request.form["runner_id"]

        db = get_db()
        db.execute(
            "INSERT INTO player (p_name, tid, corp_id, runner_id)"
            "VALUES (?, ?, ?, ?)",
            (name, tid, corp_id, runner_id),
        )
        db.commit()

    corp_ids = ["HB", "Jinteki", "Weyland", "NBN"]
    runner_ids = ["Kate", "Noise", "Gabe"]

    return render_template(
        "t_register.html",
        data={"t": t, "ids": {"corps": corp_ids, "runners": runner_ids}},
    )


@bp.route("/<int:tid>/admin", methods=["GET", "POST", "PUT"])
def admin(tid):
    # Add post method for starting the tournament
    t = get_tournament(tid)
    plrs = get_players(tid)
    return render_template("t_admin.html", data={"t": t, "players": plrs})


@bp.route("/<int:tid>/admin/<int:pid>/drop", methods=["GET", "PUT"])
def drop_player(tid, pid):
    db = get_db()
    db.execute("UPDATE player SET active = 0 WHERE id = ?", (pid,))
    db.commit()
    return redirect(url_for("manager.admin", tid=tid), code=303)


@bp.route("/<int:tid>/admin/<int:pid>/undrop", methods=["GET", "PUT"])
def undrop_player(tid, pid):
    db = get_db()
    db.execute("UPDATE player SET active = 1 WHERE id = ?", (pid,))
    db.commit()
    return redirect(url_for("manager.admin", tid=tid), code=303)


@bp.route("/<int:tid>/admin/<int:pid>/remove", methods=["POST"])
def remove_player(tid, pid):
    print(pid)
    db = get_db()
    db.execute("DELETE FROM player WHERE id = ?", (pid,))
    db.commit()
    return redirect(url_for("manager.admin", tid=tid))


@bp.route("/<int:tid>/admin/pair", methods=["GET", "POST"])
def make_pairings(tid):
    t = get_tournament(tid)
    pair_round(t["id"], t["current_rnd"] + 1)
    return redirect(url_for("manager.pairings", tid=t["id"], rnd=t["current_rnd"] + 1))


@bp.route("/<int:tid>/<int:rnd>", methods=["GET", "POST"])
def pairings(tid, rnd):
    t = get_tournament(tid)
    plrs = get_players(tid)
    matches = get_matches(tid, rnd)
    if len(matches) == 0:
        abort(404, f"The tournament {t['title']} does not have a Round {rnd}")
    return render_template(
        "t_pairings.html",
        data={"t": t, "players": plrs, "matches": matches, "rnd": rnd},
    )


@bp.route("/<int:tid>/<int:rnd>/admin", methods=["GET", "POST"])
def admin_pairings(tid, rnd):
    # Add post method for closing the round
    t = get_tournament(tid)
    plrs = get_players(tid)
    matches = get_matches(tid, rnd)
    return render_template(
        "t_admin_pairings.html", data={"t": t, "players": plrs, "matches": matches}
    )


@bp.route("/reporting/<int:mid>", methods=["POST", "GET"])
def report_result(mid):
    if request.form["result"] == "c_win":
        c_score = 3
        r_score = 0
    elif request.form["result"] == "r_win":
        c_score = 0
        r_score = 3
    else:
        c_score = 1
        r_score = 1
    db = get_db()
    db.execute(
        """ UPDATE match SET corp_score = ?, runner_score = ?
        WHERE id = ?

        """,
        (
            c_score,
            r_score,
            mid,
        ),
    )
    db.commit()
    match = db.execute("SELECT * FROM match WHERE id = ?", (mid,)).fetchone()

    return redirect(url_for("manager.pairings", tid=match["tid"], rnd=match["rnd"]))