import networkx as nx
import json
import sqlite3
from player import Player
from match import Match
from datetime import date
from itertools import combinations
from uuid import uuid4
from random import random


class Tournament:
    """
    This object is basically only created for making pairings
    Maybe long term I move away from this object model
    Could probably stip a lot of the extraneous stuff out
    """
    def __init__(self, _id=None, title=None, t_date=None, current_rnd=None):
        self._id = _id
        if t_date is None:
            t_date = date.today().strftime("%Y-%m-%d")
        self.t_date = t_date
        if current_rnd is None:
            current_rnd = 0
        self.title = title
        self.current_rnd = current_rnd

    def __repr__(self):
        return f"<Tournament> {self._id}: {self.title}"

    def to_db(self):
        """
        Return: Dictionary with _id, title, t_date, current_rnd
        """
        return {
            "id": self._id,
            "title": self.title,
            "t_date": self.t_date,
            "current_rnd": self.current_rnd,
        }

    def pair_round(self, plr_list):
        """
        Takes a list of player objects and returns a list of matches

        It's the job of the app to add those matches to the db

        plr_list: List of Player objects
        returns: list of Match objects
        """
        graph = nx.Graph()
        if len(plr_list) % 2 == 1:
            plr_list.append(add_bye_player())
        players = {plr._id: plr for plr in plr_list}
        pairings = self.make_pairings(players, graph)
        return self.make_matches(pairings, players, graph)

    def make_pairings(self, players, graph):
        """
        Internal function that makes the pairings by producing a graph

        Returns list of sets
        """
        for player in players.values():
            graph.add_node(player._id, player=player)
        for pair in combinations(players, 2):
            corp_player_id, side_bias_cost = get_side_tuple(
                players[pair[0]], players[pair[1]]
            )
            score_cost = calc_score_cost(players[pair[0]], players[pair[1]])
            if side_bias_cost is None:
                continue
            print(f"{pair[0]} vs {pair[1]}: {side_bias_cost+score_cost}")
            graph.add_edge(
                pair[0],
                pair[1],
                weight=1000 - (side_bias_cost + score_cost),
                corp_player=corp_player_id,
            )
        return nx.max_weight_matching(graph, maxcardinality=True)

    def make_matches(self, pairings, players, graph):
        matches = []
        ranked_players = rank_players(players)
        for player in ranked_players:
            # Check if player in table
            for match in matches:
                if match.corp_id == player._id or match.runner_id == player._id:
                    break
            else:
                # Build table logic
                for pair in pairings:
                    if player._id in pair:
                        if player._id == pair[0]:
                            player_position = 0
                        else:
                            player_position = 1
                        opp_position = 1 - player_position
                        if graph[pair[0]][pair[1]]["corp_player"] == player._id:
                            new_match = Match(
                                self.current_rnd,
                                players[pair[player_position]],
                                players[pair[opp_position]],
                                num=len(matches),
                                tid=self._id,
                            )
                        else:
                            new_match = Match(
                                self.current_rnd,
                                players[pair[opp_position]],
                                players[pair[player_position]],
                                num=len(matches),
                                tid=self._id,
                            )

                        matches.append(new_match)

                        break
        return matches


def add_bye_player():
    """
    Internal function that returns a Bye player
    """
    bye = Player("Bye")
    bye._id = -1
    bye.score = -1
    bye.is_bye = True
    return bye


def calc_score_cost(p1, p2):
    """
    Returns triangle number of score difference
    """
    return (p1.score - p2.score + 1) * (p1.score - p2.score) / 6


def get_side_tuple(p1, p2):
    """
    Checks if bye, returns 0, side bias doesn't play into bye pairing
    Otherwise calcualte the cost for both players playing copr side

    Then check to see if there are any non-allowed matches. The algorithm
    does not allow people to rematch with the same decks in swiss

    If they've played both sides already return none,
    If one of them has corp'd already, return the cost of the other pairing
    Otherwise if one cost is lower, return the lower cost
    Finally if the two costs are the same, flip a coin and return that one

    :p1: Player object
    :p2: Player object
    """
    if p1.is_bye or p2.is_bye:
        return (p1._id, 0)

    p1_corps_cost = calc_corp_cost(p1.side_bias, p2.side_bias)
    p2_corps_cost = calc_corp_cost(p2.side_bias, p1.side_bias)

    allowable_pairings = p1.allowable_pairings(p2._id)
    if allowable_pairings is None:
        return (None, None)
    if allowable_pairings == 1:
        return (p1._id, p1_corps_cost)
    if allowable_pairings == -1:
        return (p2._id, p2_corps_cost)
    if p1_corps_cost != p2_corps_cost:
        if p1_corps_cost < p2_corps_cost:
            return (p1._id, p1_corps_cost)
        else:
            return (p2._id, p2_corps_cost)
    if random() > 0.5:
        return (p1._id, p1_corps_cost)
    else:
        return (p2._id, p2_corps_cost)


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


def rank_players(p_dict):
    """
    Takes any dictionary where dictionary values have .esos, .sos, .score
    values and ranks them according to that

    returns a list of objects orderd in descending rate (highest player first)

    :p_dict:
    """
    p_list = [plr for plr in p_dict.values()]
    p_list.sort(key=lambda player: player.esos, reverse=True)
    p_list.sort(key=lambda player: player.sos, reverse=True)
    p_list.sort(key=lambda player: player.score, reverse=True)
    return p_list