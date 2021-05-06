from sass.db import get_db, get_tournament, get_active_players, get_player
from networkx import Graph, max_weight_matching
from itertools import combinations
from random import random
from json import loads, dumps


def pair_round(tid, rnd):
    plrs = get_active_players(tid)
    if len(plrs) % 2 == 1:
        plrs = add_bye_player(tid)
    pairings = make_pairings(plrs)
    match_list = make_matches(pairings)
    db = get_db()
    for i, match in enumerate(match_list):
        db.execute(
            "INSERT INTO match (corp_id, runner_id, tid, rnd, match_num) VALUES (?, ?, ?, ?, ?)",
            (
                match[0],
                match[1],
                tid,
                rnd,
                i + 1,
            ),
        )
    db.commit()
    score_byes(tid, rnd)


def add_bye_player(tid, bye_number=1):
    """
    Adds a bye player- the bye_number is future proofing for multiple 1st round byes
    """
    db = get_db()
    db.execute(
        "INSERT INTO player (id, tid, name, score) VALUES (?, ?, 'Bye', -9)",
        (bye_number * -1, tid),
    )
    db.commit()
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
            continue
        score_cost = calc_score_cost(p1["score"], p2["score"])
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
    First it checks if either of them is the Bye (id <0) and if either player is eligible for the bye
    Then calculates the cost of both players corping.
    Then it checks to see if the players have some forced matchup (because they've alreayd played)
    If there is a forced matchup it returns that value.
    Otherwise it takes the lower of two costs
    If the costs are the same it flips a coin using random.random()
    """
    if p1["id"] < 0 or p2["id"] < 0:
        if p1["recivied_bye"] or p2["recieved_bye"]:
            return (None, None)
        return (p1["id"], 0)

    p1_corp_cost = calc_corp_cost(p1["bias"], p2["bias"])
    p2_corp_cost = calc_corp_cost(p2["bias"], p1["bias"])

    forced_corp = can_corp(p1, p2)

    if forced_corp is None:
        return (None, None)
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
    return 8 ** prime_max_bias * (prime_max_bias > init_max_bias)


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
    try:
        p1_opp = loads(p1["opponents"])
    except:
        p1_opp = {}
    if str(p2["id"]) not in p1_opp.keys():
        return 0
    else:
        played_sides = p1_opp[str(p2["id"])]
        if played_sides == 0:
            # If p1 and p2 have played both sides, return none
            return None
        elif played_sides == -1:
            # If p1 ran against p2, they can corp
            return p1["id"]
        else:
            return p2["id"]


def make_matches(pairings):
    for key, pair in pairings.items():
        pairings[key]["score"] = (
            get_player(pair["corp"])["score"] + get_player(pair["runner"])["score"]
        )
    return [
        (pairings[i]["corp"], pairings[i]["runner"])
        for i in sorted(pairings.keys(), key=lambda j: pairings[j]["score"])
    ]


def close_round(tid, rnd):
    """
    Go through
    """
    db = get_db()
    matches = get_matches(tid, rnd)
    for match in matches:
        if match["corp_score"] is None or match["runner_score"] is None:
            raise ValueError("Not all matches reported")
        corp_player = get_player(match["corp_id"])
        corp_opponents = loads(corp_player["opponents"])
        runner_player = get_player(match["runner_id"])
        runner_opponents = loads(runner_player["opponents"])

        if runner_player["id"] in corp_opponents.keys():
            corp_opponents[runner_player["id"]] = 0
            runner_opponents[corp_player["id"]] = 0
        else:
            corp_opponents[runner_player["id"]] = 1
            runner_opponents[corp_player["id"]] = -1

        db.execute(
            "UPDATE player" "SET opponents = ?" "WHERE id = ?",
            (
                corp_opponents,
                corp_player["id"],
            ),
        )
        db.execute(
            "UPDATE player" "SET opponents = ?" "WHERE id = ?",
            (
                runner_opponents,
                runner_player["id"],
            ),
        )
    db.execute("DELETE FROM player WHERE id < 0")
    db.execute(
        "UPDATE tournament SET current_rnd = ? WHERE id = ?",
        (
            rnd + 1,
            tid,
        ),
    )
    db.commit()


def score_byes(tid, rnd):
    db = get_db()
    db.execute(
        "UPDATE match SET runner_score = 3, corp_score = 0 WHERE corp_id < 0 AND tid = ? AND rnd = ?",
        (
            tid,
            rnd,
        ),
    )
    db.execute(
        "UPDATE match SET corp_score = 3, runner_score = 0 WHERE runner_id < 0 AND tid = ? and rnd = ?",
        (
            tid,
            rnd,
        ),
    )
    db.commit()


def record_result(mid, corp_score, runner_score):
    db = get_db()
    db.execute(
        "UPDATE match SET corp_score = ?, runner_score = ? WHERE id = ?",
        (
            corp_score,
            runner_score,
            mid,
        ),
    )
    db.commit()
