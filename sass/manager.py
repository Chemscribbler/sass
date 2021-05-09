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

from sass.db import (
    get_db,
    get_players,
    get_matches,
    get_tournament,
    get_rnd_list,
    get_json,
)
from sass.tournament import (
    pair_round,
    close_round,
    record_result,
    get_ids,
    all_reported,
)

from sass.exceptions import AdminException, PairingException

bp = Blueprint("manager", __name__)


def make_data_package(tid, rnd=None):
    if rnd is None:
        matches = None
    else:
        matches = get_matches(tid, rnd)
    return {
        "t": get_tournament(tid),
        "players": get_players(tid),
        "matches": matches,
        "rnd_list": get_rnd_list(tid),
        "rnd": rnd,
    }


@bp.route("/")
def home():
    tournaments = (
        get_db().execute("SELECT * FROM tournament ORDER BY id DESC").fetchall()
    )
    return render_template("home.html", tournaments=tournaments)


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
    return render_template("t_index.html", data=make_data_package(tid))


@bp.route("/<int:tid>/register", methods=["GET", "POST"])
def register(tid):
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
    ids = get_ids()
    corp_ids = {card["name"]: card["faction"] for card in ids if card["side"] == "corp"}
    runner_ids = {
        card["name"]: card["faction"] for card in ids if card["side"] == "runner"
    }
    corp_order = sorted(corp_ids)
    runner_order = sorted(runner_ids)

    return render_template(
        "t_register.html",
        data=make_data_package(tid),
        ids={"corps": corp_order, "runners": runner_order},
    )


@bp.route("/<int:tid>/<int:rnd>", methods=["GET", "POST"])
def pairings(tid, rnd):
    t = get_tournament(tid)
    matches = get_matches(tid, rnd)
    if len(matches) == 0:
        abort(404, f"The tournament {t['title']} does not have a Round {rnd}")
    return render_template(
        "t_pairings.html",
        data=make_data_package(tid, rnd=rnd),
    )


@bp.route("/<int:tid>/admin", methods=["GET", "POST", "PUT"])
def admin(tid):
    return render_template("t_admin.html", data=make_data_package(tid))


@bp.route("/<int:tid>/<int:rnd>/admin", methods=["GET", "POST"])
def admin_pairings(tid, rnd):
    return render_template(
        "t_admin_pairings.html",
        data=make_data_package(tid, rnd=rnd),
    )


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
    if not all_reported(tid, t["current_rnd"] - 1):
        flash("Previous round not complete")
        return redirect(
            url_for("manager.admin_pairings", tid=tid, rnd=t["current_rnd"] - 1)
        )
    if not all_reported(tid, t["current_rnd"]):
        flash("Pairing for this round already exists")
        return redirect(
            url_for("manager.admin_pairings", tid=tid, rnd=t["current_rnd"])
        )
    pair_round(t["id"], t["current_rnd"])
    return redirect(url_for("manager.pairings", tid=t["id"], rnd=t["current_rnd"]))


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
    record_result(mid, c_score, r_score)
    match = get_db().execute("SELECT * FROM match WHERE id = ?", (mid,)).fetchone()
    return redirect(url_for("manager.pairings", tid=match["tid"], rnd=match["rnd"]))


@bp.route("/<int:tid>/<int:rnd>/close", methods=["POST"])
def finish_round(tid, rnd):
    try:
        close_round(tid, rnd)
        return redirect(url_for("manager.admin", tid=tid), code=303)
    except PairingException as e:
        print(e)
        flash("Not all matches have results")
        return redirect(
            url_for(
                "manager.admin_pairings",
                tid=tid,
                rnd=rnd,
            ),
        )


@bp.route("/<int:tid>/admin/start", methods=["POST"])
def start_tournament(tid):
    t = get_tournament(tid)
    if t["current_rnd"] != 0:
        return redirect(url_for("manager.admin", tid=tid))
    db = get_db()
    db.execute("UPDATE tournament SET current_rnd = 1 WHERE id = ?", (tid,))
    db.commit()
    pair_round(tid, 1)
    return redirect(url_for("manager.admin_pairings", tid=tid, rnd=1))


@bp.route("/<int:tid>.json", methods=["GET"])
def report_json(tid):
    return get_json(tid)


@bp.route("/<int:tid>/<int:rnd>/delete", methods=["POST"])
def delete_rnd(tid, rnd):
    pass