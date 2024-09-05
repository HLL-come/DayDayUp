import struct

from ._error import BaseError


class PracticeMacro:
    def __init__(self, conn, *, name=None, value=None):
        self.__conn = conn
        self.name = name
        self.value = value

    def __str__(self):
        return str(self.to_dict())

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        if name is None:
            self.__name = None
        elif isinstance(name, str):
            self.__name = name
        else:
            raise TypeError(type(name))

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if value is None:
            self.__value = None
        elif isinstance(value, str):
            self.__value = value
        else:
            raise TypeError(type(value))

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }


class PracticeError(BaseError):
    pass


class PracticeService:
    def __init__(self, conn):
        self.__conn = conn

    def get_macro(self, name: str) -> PracticeMacro:
        """Get (global) PRACTICE macro.

        Args:
            name: Name of the Macro.

        Returns:
            PracticeMacro: Macro.

        Todo:
            Raise PracticeMacroNotFound exception when macro name was not found?
        """
        data = struct.pack("<HH{}s".format(len(name)), 0, len(name), name.encode())

        result = self.__conn.t32_exp(2, data)

        if result.payload is None:
            raise PracticeError(result.err_code, result.err_msg)
        else:
            return PracticeMacro(self.__conn, name=name, value=self.deserialize(result.payload))

    def set_macro(self, name: str, value: str) -> PracticeMacro:
        """Set (global) PRACTICE macro.

        Args:
            name: Name of the Macro.
            value: Value of the Macro

        Returns:
            PracticeMacro: Macro
        """
        data = struct.pack(
            "<HH{}sH{}s".format(len(name), len(value)), 1, len(name), name.encode(), len(value), value.encode()
        )

        result = self.__conn.t32_exp(2, data)

        if result.payload is None:
            raise PracticeError(result.err_code, result.err_msg)
        else:
            return PracticeMacro(self.__conn, name=name, value=value)

    @staticmethod
    def deserialize(rbuffer):
        value = rbuffer[2:]
        try:
            return value.decode()
        except AttributeError:
            return value
