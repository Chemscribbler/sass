class Match:
    # Match object for storing data (should this be a dict???)

    def __init__(
        self,
        rnd,
        corp_player,
        runner_player,
        tid,
        corp_score=None,
        runner_score=None,
    ):
        self.rnd = rnd
        self.corp_id = corp_player._id
        self.runner_id = runner_player._id
        self.tid = tid

        self.corp_score = corp_score
        self.runner_score = runner_score
        self.bye_table = False

        if corp_player.is_bye:
            self.runner_score = 3
            self.corp_score = 0
            self.bye_table = True

        if runner_player.is_bye:
            self.corp_score = 3
            self.runner_score = 0
            self.bye_table = True

    def __repr__(self):
        return f"<Table> Rnd:{self.rnd} C:{self.corp_id} vs R:{self.runner_id}"

    def to_db(self):
        return {
            "tid": self.tid,
            "corp_id": self.corp_id,
            "runner_id": self.runner_id,
            "rnd": self.rnd,
            "corp_score": self.corp_score,
            "runner_score": self.runner_score,
        }

    def report_result(self, corp_score, runner_score):
        if not self.bye_table:
            self.corp_score = corp_score
            self.runner_score = runner_score