from copy import copy
from sqlalchemy.sql.expression import insert, text, select, update
from sass.db_ops import get_db, get_tournament, get_active_players, get_player, metadata
from networkx import Graph, max_weight_matching
from itertools import combinations
from random import random
from json import load, dump
import requests
import os.path
from sass.exceptions import PairingException
from sass.db_grabber import get_db, metadata
import decimal


def pair_round(tid, rnd):
    plrs = get_active_players(tid)
    if len(plrs) % 2 == 1:
        plrs = add_bye_player(tid)
    pairings = make_pairings(plrs)
    match_list = make_matches(pairings)
    db = get_db()
    table_match = metadata.tables["match"]
    with db.begin() as conn:
        for i, match in enumerate(match_list):
            conn.execute(
                insert(table_match).values(
                    corp_id=match[0],
                    runner_id=match[1],
                    tid=tid,
                    rnd=rnd,
                    match_num=i + 1,
                )
            )
    score_byes(tid, rnd)


def add_bye_player(tid):
    """
    Adds a bye player- the bye_number is future proofing for multiple 1st round byes
    """
    with get_db().begin() as conn:
        conn.execute(
            text(
                "INSERT INTO player (tid, p_name, is_bye, score) VALUES (:tid, 'Bye', true, -9)"
            ),
            {"tid": tid},
        )
    return get_active_players(tid)


def make_pairings(plrs):
    graph = Graph()
    plr_ids = [plr["id"] for plr in plrs]
    for pid in plr_ids:
        graph.add_node(pid)
    for pair in combinations(plr_ids, 2):
        p1 = get_player(pair[0])
        p2 = get_player(pair[1])
        corp_player_id, runner_player_id, side_bias_cost = get_side_tuple(p1, p2)
        if side_bias_cost is None:
            # print(f"{p1.p_name} v. {p2.p_name} cannot play")
            continue
        score_cost = calc_score_cost(p1["score"], p2["score"])
        # print(f"{p1.p_name} v. {p2.p_name}: {side_bias_cost+score_cost}")
        graph.add_edge(
            p1,
            p2,
            weight=1000 - (side_bias_cost + score_cost),
            corp_player=corp_player_id,
            runner_player=runner_player_id,
        )
    pairings = max_weight_matching(graph, maxcardinality=True)
    aug_pairings = {}
    for i, pair in enumerate(pairings):
        aug_pairings[i] = {
            "corp": graph[pair[0]][pair[1]]["corp_player"],
            "runner": graph[pair[0]][pair[1]]["runner_player"],
        }
    return aug_pairings


def get_side_tuple(p1, p2):
    """
    Returns the minimum weight edge between two players
    First it checks if either of them is the Bye and if either player is eligible for the bye
    Then calculates the cost of both players corping.
    Then it checks to see if the players have some forced matchup (because they've alreayd played)
    If there is a forced matchup it returns that value.
    Otherwise it takes the lower of two costs
    If the costs are the same it flips a coin using random.random()
    """
    if p1["is_bye"] or p2["is_bye"]:
        if p1["received_bye"] or p2["received_bye"]:
            return (None, None, None)
        return (p1["id"], p2["id"], 0)

    p1_corp_cost = calc_corp_cost(p1["bias"], p2["bias"])
    p2_corp_cost = calc_corp_cost(p2["bias"], p1["bias"])

    forced_corp = can_corp(p1, p2)

    if forced_corp is None:
        return (None, None, None)
    elif forced_corp == p1["id"]:
        return (p1["id"], p2["id"], p1_corp_cost)
    elif forced_corp == p2["id"]:
        return (p2["id"], p1["id"], p2_corp_cost)
    elif p1_corp_cost != p2_corp_cost:
        if p1_corp_cost < p2_corp_cost:
            return (p1["id"], p2["id"], p1_corp_cost)
        else:
            return (p2["id"], p1["id"], p2_corp_cost)
    elif random() > 0.5:
        return (p1["id"], p2["id"], p1_corp_cost)
    else:
        return (p2["id"], p1["id"], p2_corp_cost)


def calc_corp_cost(p1_side_bias, p2_side_bias):
    """
    calculates the max side bias of the two players before they play
    then calculates the max side bias after p1 corps.
    If the pairing has a lower max side bias this function will return 0
        (basically if player 1 has run more, and player 2 has corp'd more they
        should get paired)
    Otherwise figure out the max bias of the two after p1 corps
        And return 8**(max_bias)

    :p1_side_bias: side bias of player 1
    :p2_side_bias: side bias of player 2
    """
    init_max_bias = max(abs(p1_side_bias), abs(p2_side_bias))
    prime_max_bias = max(abs(p1_side_bias + 1), abs(p2_side_bias - 1))
    return 8 ** prime_max_bias * (prime_max_bias >= init_max_bias)


def calc_score_cost(p1_score, p2_score):
    return (p1_score - p2_score + 1) * (p1_score - p2_score) / 6


def can_corp(p1, p2):
    """
    Using the player[opponents] field, deserialize from json
    Check to see if they've played any matches
    If they have not, return 0
    Otherwise if they total side balance is 0 (they've played both) return None
    Otherwise return the ID of the player who has to Corp
    """
    with get_db().begin() as conn:
        p1_corped_query = conn.execute(
            text("SELECT * from match where corp_id = :p1_id AND runner_id = :p2_id"),
            {"p1_id": p1["id"], "p2_id": p2["id"]},
        ).fetchone()
        p2_corped_query = conn.execute(
            text("SELECT * from match where corp_id = :p2_id AND runner_id = :p1_id"),
            {"p1_id": p1["id"], "p2_id": p2["id"]},
        ).fetchone()

        if p1_corped_query is None and p2_corped_query is None:
            return 0
        elif p1_corped_query is None:
            return p1["id"]
        elif p2_corped_query is None:
            return p2["id"]
        else:
            return None


def make_matches(pairings):
    for key, pair in pairings.items():
        pairings[key]["score"] = (
            get_player(pair["corp"])["score"] + get_player(pair["runner"])["score"]
        )
    return [
        (pairings[i]["corp"], pairings[i]["runner"])
        for i in sorted(
            pairings.keys(), key=lambda j: pairings[j]["score"], reverse=True
        )
    ]


def close_round(tid, rnd):
    """
    Check to see if all matches report
    """
    with get_db().begin() as conn:
        if not all_reported(tid, rnd):
            raise PairingException("Not all matches have reported result")
        update_byes_recieved(tid)

        conn.execute(
            text("UPDATE player SET active=false WHERE is_bye = true AND tid = :tid"),
            {"tid": tid},
        )

    update_scores(tid)
    update_bias(tid)
    update_sos(tid)
    update_esos(tid)
    t = get_tournament(tid)
    with get_db().begin() as conn:
        if rnd == t["current_rnd"]:
            conn.execute(
                text("UPDATE tournament SET current_rnd = :rnd WHERE id = :tid"),
                {
                    "rnd": rnd + 1,
                    "tid": tid,
                },
            )
    return True


def score_byes(tid, rnd):
    with get_db().begin() as conn:
        conn.execute(
            text(
                "UPDATE match SET runner_score = 3, corp_score = 0 FROM player WHERE player.id = match.corp_id AND player.is_bye = true AND match.tid = :tid AND rnd = :rnd"
            ),
            {"tid": tid, "rnd": rnd},
        )
        conn.execute(
            text(
                "UPDATE match SET corp_score = 3, runner_score = 0 FROM player WHERE player.id = match.runner_id AND player.is_bye = true AND match.tid = :tid and rnd = :rnd"
            ),
            {"tid": tid, "rnd": rnd},
        )


def record_result(mid, corp_score, runner_score):
    db = get_db()
    table_match = metadata.tables["match"]
    with db.begin() as conn:
        match = conn.execute(
            select(table_match).where(table_match.c.id == mid)
        ).fetchone()
        if get_player(match["corp_id"]).is_bye or get_player(match["runner_id"]).is_bye:
            return
        conn.execute(
            update(table_match)
            .where(table_match.c.id == mid)
            .values(corp_score=corp_score, runner_score=runner_score)
        )


def update_scores(tid):
    scores_table = []
    with get_db().begin() as conn:
        scores_table = conn.execute(
            text(
                """
            SELECT id, name, SUM(coalesce(corp_points,0)) AS corp_points,
            SUM(coalesce(runner_points,0)) AS runner_points
            FROM(
                SELECT p.id AS id, p.p_name AS name, sum(m.corp_score) AS corp_points, 0 AS runner_points
                FROM player p
                INNER JOIN match m on p.id = m.corp_id
                WHERE p.tid = :tid
                group by p.id
                UNION
                SELECT p.id AS id, p.p_name AS name, 0 AS corp_points, sum(m.runner_score) AS runner_points
                FROM player p
                INNER JOIN match m on p.id = m.runner_id
                WHERE p.tid = :tid
                group by p.id
            ) as t
            group by t.id, t.name
            """
            ),
            {"tid": tid},
        ).fetchall()
    with get_db().begin() as conn:
        for player in scores_table:
            print(player)
            conn.execute(
                text(
                    "UPDATE player SET score = :score WHERE id = :pid AND is_bye = false",
                ),
                {
                    "score": int(player["corp_points"])
                    + int(player["runner_points"]),
                    "pid": player["id"],
                },
            )
    update_bias(tid)


def update_bias(tid):
    with get_db().begin() as conn:
        bias_table = conn.execute(
            text(
                """
        SELECT id, name, sum(coalesce(corp_games,0)) AS corp_games,
        sum(coalesce(runner_games,0)) AS runner_games
            FROM(
                SELECT p.id AS id, p.p_name AS name, count(m.corp_id) AS corp_games, 0 AS runner_games
                FROM player p
                INNER JOIN match m on p.id = m.corp_id
                INNER JOIN player o ON o.id = m.runner_id
                WHERE p.tid = :tid AND o.is_bye = false AND p.is_bye = false
                group by p.id
                UNION
                SELECT p.id AS id, p.p_name AS name, 0 AS corp_games, count(m.runner_id) AS runner_games
                FROM player p
                INNER JOIN match m on p.id = m.runner_id
                INNER JOIN player o ON o.id = m.corp_id
                WHERE p.tid = :tid AND o.is_bye = false AND p.is_bye = false
                group by p.id
            ) as t
        group by t.id, t.name
        """
            ),
            {"tid": tid},
        ).fetchall()
        for player in bias_table:
            conn.execute(
                text(
                    "UPDATE player SET bias = :bias, games_played = :games_played WHERE id = :pid"
                ),
                {
                    "bias": player["corp_games"] - player["runner_games"],
                    "games_played": player["corp_games"] + player["runner_games"],
                    "pid": player["id"],
                },
            )


def update_sos(tid):
    with get_db().begin() as conn:
        sos_table = conn.execute(
            text(
                """
            SELECT id, sum(coalesce(score,0)) as total_opp_score,
            sum(coalesce(opg, 0)) as total_opp_games_played
            FROM (
                    select p.id, sum(coalesce(o.games_played,0)) as opg, sum(coalesce(o.score,0)) as score
                    FROM player p
                    INNER JOIN match m on p.id = m.runner_id
                    INNER JOIN player o ON m.corp_id = o.id
                    where p.tid = :tid AND p.is_bye = false AND o.is_bye = false
                    group by p.id

                UNION
                select p.id, sum(coalesce(o.games_played,0)) as opg, sum(coalesce(o.score,0)) as score
                    FROM player p
                    INNER JOIN match m on p.id = m.corp_id
                    INNER JOIN player o ON m.runner_id = o.id
                    where p.tid = :tid AND p.is_bye = false AND o.is_bye = false
                    group by p.id) as t
            group by t.id
            """
            ),
            {"tid": tid},
        ).fetchall()
        for player in sos_table:
            conn.execute(
                text("UPDATE player SET sos = :sos WHERE id = :pid"),
                {
                    "sos": round(
                        player["total_opp_score"]
                        / max(player["total_opp_games_played"], 1),
                        3,
                    ),
                    "pid": player["id"],
                },
            )


def update_esos(tid):
    with get_db().begin() as conn:
        sos_table = conn.execute(
            text(
                """
            SELECT id, sum(coalesce(sos,0)) as total_opp_sos,
            sum(coalesce(opg, 0)) as total_opp_games_played
            FROM (
                    select p.id, sum(coalesce(o.games_played,0)) as opg, sum(coalesce(o.sos,0)) as sos
                    FROM player p
                    INNER JOIN match m on p.id = m.runner_id
                    INNER JOIN player o ON m.corp_id = o.id
                    where p.tid = :tid AND p.is_bye = false AND o.is_bye = false
                    group by p.id

                UNION
                select p.id, sum(coalesce(o.games_played,0)) as opg, sum(coalesce(o.sos,0)) as sos
                    FROM player p
                    INNER JOIN match m on p.id = m.corp_id
                    INNER JOIN player o ON m.runner_id = o.id
                    where p.tid = :tid AND p.is_bye = false AND o.is_bye = false
                    group by p.id) as t
            group by t.id
            """
            ),
            {"tid": tid},
        ).fetchall()
        for player in sos_table:
            conn.execute(
                text("UPDATE player SET esos = :esos WHERE id = :pid"),
                {
                    "esos": round(
                        player["total_opp_sos"]
                        /max(player["total_opp_games_played"], 1),
                        4,
                    ),
                    "pid": player["id"],
                },
            )


def get_ids():
    if not os.path.exists("ids.json"):
        all_cards = requests.get(
            "https://netrunnerdb.com/api/2.0/public/cards", timeout=5
        )
        ids = [
            {
                "side": card["side_code"],
                "faction": card["faction_code"],
                "name": card["title"],
            }
            for card in all_cards.json()["data"]
            if card["type_code"] == "identity"
        ]
        with open("ids.json", "w") as f:
            dump(ids, f)
    else:
        ids = []
        with open("ids.json", "r") as f:
            ids = load(f)
    return ids


def update_byes_recieved(tid):
    with get_db().begin() as conn:
        byes = conn.execute(
            text(
                """
            SELECT p.id 
            FROM player p
            INNER JOIN match m
            ON p.id = m.corp_id
            INNER JOIN player o
            ON o.id = m.runner_id
            WHERE o.is_bye = true AND p.tid = :tid
            """
            ),
            {"tid": tid},
        ).fetchall()
        for i in byes:
            conn.execute(
                text("UPDATE player SET received_bye = true WHERE id = :pid"),
                {"pid": i["id"]},
            )
        byes = conn.execute(
            text(
                """
            SELECT p.id 
            FROM player p
            INNER JOIN match m
            ON p.id = m.runner_id
            INNER JOIN player o
            ON o.id = m.corp_id
            WHERE o.is_bye = true AND p.tid = :tid
            """
            ),
            {"tid": tid},
        ).fetchall()
        for i in byes:
            conn.execute(
                text("UPDATE player SET received_bye = true WHERE id = :pid"),
                {"pid": i["id"]},
            )


def existing_pairings(tid, rnd):
    q = (
        get_db()
        .connect()
        .execute(
            text("SELECT * FROM match where tid = :tid and rnd = :rnd"),
            {"tid": tid, "rnd": rnd},
        )
        .fetchone()
    )
    return q


def all_reported(tid, rnd):
    q = (
        get_db()
        .connect()
        .execute(
            text(
                "SELECT * FROM match WHERE tid = :tid AND rnd = :rnd AND corp_score IS NULL"
            ),
            {"tid": tid, "rnd": rnd},
        )
        .fetchone()
    )
    return q is None