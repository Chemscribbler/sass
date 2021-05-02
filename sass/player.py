from json import dumps


class Player:
    """
    Player object with a few functions, only built when doing pairings
    """

    def __init__(self, plr_name, tid, _id=None, corp_id=None, runner_id=None):
        self.plr_name = plr_name
        self.tid = tid
        self._id = _id
        self.corp_id = corp_id
        self.runner_id = runner_id

        self.score = 0
        self.sos = 0.0
        self.esos = 0.0
        self.side_bias = 0

        # self.opponents is a dictionary key'd by opponent _id
        # value is the side they played against the opponent
        self.opponents = {}

        self.is_bye = False
        self.dropped = False
        self.recieved_bye = False

    def __repr__(self):
        return f"<Player> {self._id} : {self.plr_name}"

    def to_db(self):
        return {
            "id": self._id,
            "tid": self.tid,
            "corp_id": self.corp_id,
            "runner_id": self.runner_id,
            "score": self.score,
            "sos": self.sos,
            "esos": self.esos,
            "recieved_bye": self.recieved_bye,
            "opponents": dumps(self.opponents),
        }

    def allowable_pairings(self, opp_id):
        """
        For a given opponent return what sides they can play
        Only works in swiss
        """
        if opp_id not in self.opponents.keys():
            return 0  # Sum of -1 and 1
        if self.opponents[opp_id] == 0:
            return None
        else:
            return self.opponents[opp_id] * (-1)

    def games_played(self):
        """
        Count the number of games played
        """
        count = 0
        for side in self.opponents.values():
            if side == 0:
                count += 2
            else:
                count += 1
        return count