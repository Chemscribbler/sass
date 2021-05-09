class TournamentException(Exception):
    pass


class PairingException(TournamentException):
    pass


class AdminException(TournamentException):
    pass