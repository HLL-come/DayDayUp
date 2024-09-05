from ._error import BaseError


class CommandError(BaseError):
    pass


class CommandService:
    """
    Executes a command on call
    """
    def __init__(self, conn):
        self.__conn = conn

    def __call__(self, cmd: str):
        self.__conn._cmd(cmd)
