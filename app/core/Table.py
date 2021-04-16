class Table:
    # Table object for storing data (should this be a dict???)

    def __init__(self, rnd, corp_player, runner_player, num):
        self.id = num
        self.rnd = rnd
        self.corp_id = corp_player.id
        self.runner_id = runner_player.id

        self.corp_score = None
        self.runner_score = None
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
        return (
            f"<Table> Rnd:{self.rnd} #:{self.id} C:{self.corp_id} vs R:{self.runner_id}"
        )

    def report_result(self, corp_score, runner_score):
        if not self.bye_table:
            self.corp_score = corp_score
            self.runner_score = runner_score
