import uuid


class Player:
    next_id = 1

    def __init__(self, name, corp_id=None, runner_id=None):
        self.id = Player.next_id
        Player.next_id += 1
        self.name = name
        self.corp_id = corp_id
        self.runner_id = runner_id

        self.score = 0
        self.sos = 0
        self.esos = 0
        self.side_bias = 0

        # self.opponents is a dictionary key'd by opponent ID
        # value is the side they played against the opponent
        self.opponents = {}

        self.byes_recieved = 0
        self.dropped = False
        self.is_bye = False

    def __repr__(self):
        return f"<Player> {self.id} : {self.name}"

    def allowable_pairings(self, opp_id):
        # For a given opponent return what sides they can play
        # Only works in swiss
        if opp_id not in self.opponents.keys():
            return 0  # Sum of -1 and 1
        if self.opponents[opp_id] == 0:
            return None
        else:
            return self.opponents[opp_id] * (-1)

    def games_played(self):
        count = 0
        for side in self.opponents.values():
            if side == 0:
                count += 2
            else:
                count += 1
        return count
