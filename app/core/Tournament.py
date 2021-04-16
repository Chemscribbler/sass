import networkx as nx
import jsonpickle
import json
import csv
from random import random
from itertools import combinations
from Player import Player
from Table import Table
import uuid
from datetime import date


class Tournament:
    def __init__(self, id=None, t_date=None):
        if id is None:
            id = str(uuid.uuid4())
        self.id = id
        self.player_dict = {}
        if t_date is None:
            t_date = date.today().strftime("%Y-%m-%d")
        self.t_date = t_date
        # Each round contains a dictionary
        # Each dictionary two keys: Completed, boolean for if the found is done
        # and Dictionary of tables, keyed by table number
        self.rounds = {}
        self.current_round = 0
        self.score_factor = 3

    def __repr__(self):
        return f"<Tournament> {self.id}"

    def add_player(self, name, force=False, **kwargs):
        if self.current_round > 0 and not force:
            raise ValueError("Cannot add after start")
        plr = Player(name, **kwargs)
        self.player_dict[plr.id] = plr
        return plr

    def active_players(self):
        return {plr.id: plr for plr in self.player_dict.values() if not plr.dropped}

    def add_bye_player(self):
        bye = Player("Bye")
        bye.id = -1
        bye.score = -1
        bye.is_bye = True
        return bye

    def pair_round(self):
        self.rounds[self.current_round] = {"complete": False, "tables": {}}
        graph = nx.Graph()
        players = self.active_players()
        if len(players) % 2 == 1:
            players[-1000] = self.add_bye_player()
        pairings = self.make_pairings(players, graph)
        self.make_tables(pairings, players, graph)

    def make_pairings(self, players, graph):
        for player in players.values():
            graph.add_node(player.id, player=player)
        for pair in combinations(players, 2):
            corp_player_id, side_bias_cost = self.get_side_tuple(
                players[pair[0]], players[pair[1]]
            )
            score_cost = (
                self.calc_score_cost(players[pair[0]], players[pair[1]])
                * self.score_factor
            )
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

    def make_tables(self, pairings, players, graph):
        ranked_players = self.rank_players(players)
        for player in ranked_players:
            # Check if player in table
            for table in self.rounds[self.current_round]["tables"].values():
                if table.corp_id == player.id or table.runner_id == player.id:
                    break
            else:
                # Build table logic
                for pair in pairings:
                    if player.id in pair:
                        if player.id == pair[0]:
                            player_position = 0
                        else:
                            player_position = 1
                        opp_position = 1 - player_position
                        if graph[pair[0]][pair[1]]["corp_player"] == player.id:
                            new_table = Table(
                                self.current_round,
                                players[pair[player_position]],
                                players[pair[opp_position]],
                                self.get_next_table_num(),
                            )
                        else:
                            new_table = Table(
                                self.current_round,
                                players[pair[opp_position]],
                                players[pair[player_position]],
                                self.get_next_table_num(),
                            )

                        # Add table to round dictionary
                        self.rounds[self.current_round]["tables"][
                            new_table.id
                        ] = new_table

                        continue

    def calc_score_cost(self, p1, p2):
        return (p1.score - p2.score + 1) * (p1.score - p2.score) / 6

    def get_side_tuple(self, p1, p2):
        if p1.is_bye or p2.is_bye:
            return (p1.id, 0)

        corp_player = None
        p1_corps_cost = self.calc_corp_cost(p1.side_bias, p2.side_bias)
        p2_corps_cost = self.calc_corp_cost(p2.side_bias, p1.side_bias)

        allowable_pairings = p1.allowable_pairings(p2.id)
        if allowable_pairings is None:
            return (None, None)
        if allowable_pairings == 1:
            return (p1.id, p1_corps_cost)
        if allowable_pairings == -1:
            return (p2.id, p2_corps_cost)
        if p1_corps_cost != p2_corps_cost:
            if p1_corps_cost < p2_corps_cost:
                return (p1.id, p1_corps_cost)
            else:
                return (p2.id, p2_corps_cost)
        if random() > 0.5:
            return (p1.id, p1_corps_cost)
        else:
            return (p2.id, p2_corps_cost)

    def calc_corp_cost(self, p1_side_bias, p2_side_bias):
        init_max_bias = max(abs(p1_side_bias), abs(p2_side_bias))
        prime_max_bias = max(abs(p1_side_bias + 1), abs(p2_side_bias - 1))
        return 8 ** prime_max_bias * (prime_max_bias > init_max_bias)

    def get_next_table_num(self):
        if 1 not in self.rounds[self.current_round]["tables"].keys():
            return 1
        else:
            return max(self.rounds[self.current_round]["tables"].keys()) + 1

    def report_result(self, table_number, c_score, r_score, pick_round=None):
        if pick_round is None:
            pick_round = self.current_round
        self.rounds[pick_round]["tables"][table_number].report_result(c_score, r_score)

    def close_round(self):
        if not self.is_round_complete(self.current_round):
            raise InterruptedError("At least 1 table is not reported")

        self.rounds[self.current_round]["complete"] = True

        self.score_tables()
        self.calc_sos()
        self.calc_esos()
        self.current_round += 1
        self.save_tournament()

    def is_round_complete(self, rnd):
        for table in self.rounds[rnd]["tables"].values():
            if table.corp_score is None:
                return False
        return True

    def rank_players(self, p_dict):
        p_list = [plr for plr in p_dict.values()]
        p_list.sort(key=lambda player: player.esos, reverse=True)
        p_list.sort(key=lambda player: player.sos, reverse=True)
        p_list.sort(key=lambda player: player.score, reverse=True)
        return p_list

    def start_tournament(self):
        if self.current_round != 0:
            raise ValueError("Tournament already started")
        self.current_round = 1
        self.pair_round()

    def score_tables(self):
        pd = self.player_dict

        for table in self.rounds[self.current_round]["tables"].values():
            if table.corp_id not in pd.keys():
                runner = pd[table.runner_id]
                runner.score += table.runner_score
            elif table.runner_id not in pd.keys():
                corp = pd[table.corp_id]
                corp.score += table.corp_score
            else:
                runner = pd[table.runner_id]
                corp = pd[table.corp_id]

                runner.score += table.runner_score
                runner.side_bias -= 1
                if corp.id in runner.opponents.keys():
                    runner.opponents[corp.id] -= 1
                else:
                    runner.opponents[corp.id] = -1

                corp.score += table.corp_score
                corp.side_bias += 1
                if runner.id in corp.opponents.keys():
                    corp.opponents[runner.id] += 1
                else:
                    corp.opponents[runner.id] = 1

    def calc_sos(self):
        pd = self.player_dict
        for player in pd.values():
            opp_score = 0
            opp_rounds_played = 0

            for opp_id, value in player.opponents.items():
                if value == 0:
                    opp_score += pd[opp_id].score
                    opp_rounds_played += pd[opp_id].games_played()
                opp_score += pd[opp_id].score
                opp_rounds_played += pd[opp_id].games_played()

            if opp_rounds_played == 0:
                opp_rounds_played = 1

            player.sos = opp_score / opp_rounds_played

    def calc_esos(self):
        pd = self.player_dict
        for player in pd.values():
            opp_sos = 0
            opp_rounds_played = 0

            for opp_id, value in player.opponents.items():
                if value == 0:
                    opp_sos += pd[opp_id].sos
                    opp_rounds_played += pd[opp_id].games_played()
                opp_sos += pd[opp_id].sos
                opp_rounds_played += pd[opp_id].games_played()

            if opp_rounds_played == 0:
                opp_rounds_played = 1

            player.esos = opp_sos / opp_rounds_played

    def testing(self, num_players):
        with open("Names.csv", "r") as names:
            reader = csv.reader(names, delimiter="\t")
            for row in reader:
                plr = self.add_player(row[1])
                plr.strength = random()
                if int(row[0]) == num_players:
                    break
        self.start_tournament()

    def sim_round(self):
        for num, table in self.rounds[self.current_round]["tables"].items():
            try:
                diff = (
                    self.player_dict[table.corp_id].strength
                    - self.player_dict[table.runner_id].strength
                )
                if random() - diff > 0.5:
                    self.report_result(num, 3, 0)
                else:
                    self.report_result(num, 0, 3)
            except AttributeError:
                self.report_result(num, 3, 0)
            except KeyError:
                self.report_result(num, 0, 0)
        self.close_round()

    def save_tournament(self, name=None):
        if name is None:
            name = f"{self.id}_round_{self.current_round}_start.json"

        with open(name, "w") as f:
            f.write(jsonpickle.encode(self,keys=True))

    def export_pairings(self, rnd=None):
        if rnd is None:
            rnd = self.current_round

        pairings = []
        for table in self.rounds[rnd]["tables"].values():
            if table.bye_table:
                if table.corp_id not in self.player_dict.keys():
                    corp_player = self.add_bye_player()
                    runner_player = self.player_dict[table.runner_id]
                else:
                    runner_player = self.add_bye_player()
                    corp_player = self.player_dict[table.corp_id]
            else:
                corp_player = self.player_dict[table.corp_id]
                runner_player = self.player_dict[table.runner_id]

            pairings.append(
                {
                    "table": table.id,
                    "corp_player": {
                        "name": corp_player.name,
                        "id": corp_player.id,
                        "score": table.corp_score,
                    },
                    "runner_player": {
                        "name": runner_player.name,
                        "id": runner_player.id,
                        "score": table.runner_score,
                    },
                    "byeTable": table.bye_table,
                }
            )

        return pairings

    def import_pairings(self, rnd, f, overwrite=False):
        with open(f, "r") as imp:
            results_json = json.load(imp)
            for json_table in results_json:
                if overwrite:
                    # Add bye handling code
                    pd = self.player_dict
                    self.rounds[rnd] = {"complete": False, "tables": {}}
                    tid = json_table["table"]
                    try:
                        self.rounds[rnd]["tables"][tid] = Table(
                            rnd,
                            pd[json_table["corp_player"]["id"]],
                            pd[json_table["runner_player"]["id"]],
                            json_table["table"],
                        )
                    except KeyError:
                        try:
                            self.rounds[rnd]["tables"][tid] = Table(
                                rnd,
                                self.add_bye_player(),
                                pd[s(json_table["runner_player"]["id"]],
                                json_table["table"],
                            )
                        except KeyError:
                            self.rounds[rnd]["tables"][tid] = Table(
                                rnd,
                                pd[json_table["corp_player"]["id"]],
                                self.add_bye_player(),
                                json_table["table"],
                            )
                    self.rounds[rnd]["tables"][tid].report_result(
                        json_table["corp_player"]["score"],
                        json_table["runner_player"]["score"],
                    )
                else:
                    t_table = self.rounds[rnd]["tables"][json_table["table"]]
                    if (
                        json_table["corp_player"]["id"] != t_table.corp_id
                        or json_table["runner_player"]["id"] != t_table.runner_id
                    ):
                        print(
                            f"Table {t_table.id} did not have matching IDs and was not loaded"
                        )
                        continue
                    t_table.report_result(
                        json_table["corp_player"]["score"],
                        json_table["runner_player"]["score"],
                    )

    def export_standings(self):
        """
        Creates json that matches ABR format
        """
        exp_json = {
            "name": self.id,
            "date": self.t_date,
            "cutToTop": 0,
            "preliminaryRounds": self.current_round,
            "tournamentOrganiser": {"nrdbId": "", "nrdbUsername": "YsengrinSC"},
            "players": [],
            "eliminationPlayers": {},
            "rounds": [],
            "uploadedFrom": "SASS",
            "links": {
                0: {
                    "rel": "schemaderivedfrom",
                    "href": "http://steffens.org/nrtm/nrtm-schema.json",
                },
                1: {
                    "rel": "uploadedfrom",
                    "href": "https://github.com/Chemscribbler/Netrunner/tree/main/SingleSided_App",
                },
            },
        }

        player_list = self.rank_players(self.player_dict)
        for i, plr in enumerate(player_list):
            exp_json["players"].append(
                {
                    "id": plr.id,
                    "name": plr.name,
                    "rank": i + 1,
                    "corpIdentity": plr.corp_id,
                    "runnerIdentity": plr.runner_id,
                    "matchPoints": plr.score,
                    "strengthOfSchedule": str(round(plr.sos, 4)),
                    "extendedStrengthOfSchedule": str(round(plr.esos, 6)),
                    "sideBalance": plr.side_bias,
                }
            )

        for rnd in self.rounds.values():
            table_list = []
            for table in rnd["tables"].values():
                table_list.append(
                    {
                        "table": table.id,
                        "corp": {"id": table.corp_id, "score": table.corp_score,},
                        "runner": {"id": table.runner_id, "score": table.runner_score},
                        "isBye": table.bye_table,
                    }
                )

        return exp_json

    def exp_rnrs_standings(self):
        """
        Creates json that matches ABR format
        """
        exp_json = {
            "name": self.id,
            "date": self.t_date,
            "cutToTop": 0,
            "preliminaryRounds": self.current_round,
            "tournamentOrganiser": {"nrdbId": "", "nrdbUsername": "SASS"},
            "players": {},
            "eliminationPlayers": {},
            "uploadedFrom": "SASS",
            "links": {
                0: {
                    "rel": "schemaderivedfrom",
                    "href": "http://steffens.org/nrtm/nrtm-schema.json",
                },
                1: {
                    "rel": "uploadedfrom",
                    "href": "https://github.com/Chemscribbler/Netrunner/tree/main/SingleSided_App",
                },
            },
        }

        player_list = self.rank_players(self.player_dict)
        for i, plr in enumerate(player_list):
            exp_json["players"][i] = {
                "id": plr.id,
                "name": plr.name,
                "rank": i + 1,
                "corpIdentity": plr.corp_id,
                "runnerIdentity": plr.runner_id,
                "matchPoints": plr.score,
                "strengthOfSchedule": str(round(plr.sos, 4)),
                "extendedStrengthOfSchedule": str(round(plr.esos, 6)),
                "sideBalance": plr.side_bias,
            }

        return exp_json


def save_json(name, f):
    with open(f"{name}.json", "w") as jsonfile:
        json.dump(f, jsonfile)


def tournament_from_csv(filepath, name):
    t = Tournament(name)
    with open(filepath, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            t.add_player(row[0], corp_id=row[1], runner_id=row[2])

    return t


def load_tournament(filepath):
    with open(filepath, "r") as f:
        return jsonpickle.decode(f.read(),keys=True)
