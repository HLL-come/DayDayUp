import struct

from ._error import BaseError


class Variable:
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
        elif isinstance(value, int):
            self.__value = value
        elif isinstance(value, float):
            self.__value = value
        else:
            raise TypeError(type(value))

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }

    def deserialize(self, buffer):
        """
        Deserializer of the variable class
        Extracts parameters from an API message and sets its own parameters accordingly

        Args:
            buffer(bytes): bytes to deserialize

        Returns:
            Variable: self
        """
        result_type = int.from_bytes(buffer[0:4], byteorder="little")
        result_size = int.from_bytes(buffer[4:8], byteorder="little")
        result_value = buffer[8:].decode()
        if result_type == 0:
            raise VariableError(result_value)
        result_value = self.__conn._decode_eval_result(result_type, result_value)
        self.__value = result_value
        return self

    def serialize(self):
        """
        Serializer of the variable class

        Args:
        Returns:
            Bytes: result
        """
        return struct.pack("<HH{}s".format(len(self.__name)), 0, len(self.__name), self.__name.encode())

    def read(self):
        """
        Calls read function of the VariableService
        """
        self.deserialize(self.__conn.variable.read(self.name).serialize())

    def write(self):
        """
        Calls write function of the VariableService
        """
        self.__conn.variable.write(self.name, self.value)


class VariableError(BaseError):
    pass


class VariableService:
    def __init__(self, conn):
        self.__conn = conn

    def read(self, name: str, **kwargs) -> Variable:
        """
        Reads a Variable from the debugger

        Args:
            name (str): Name of the desired Variable

        Returns:
            Variable: Result
        """
        return self.read_by_name(name, **kwargs)

    def read_by_name(self, name: str, **kwargs) -> Variable:
        """
        Reads a Variable by name from the debugger

        Args:
            name (str): Name of the desired Variable

        Returns:
            Variable: Result
        """
        var = Variable(self.__conn, name=name)
        data = var.serialize()
        result = self.__conn.t32_exp(4, data)
        if result.payload is None:
            raise VariableError(result.err_code, result.err_msg)
        else:
            return var.deserialize(result.payload)

    def write(self, name: str, value, **kwargs) -> Variable:
        """
        Writes a Variable object to the debugger

        Args:
            name (str): Name of the Variable that should be written
            value: Value that should be written

        Returns:
            Variable: Result
        """
        return self.write_by_name(name, value, **kwargs)

    def write_by_name(self, name: str, value, **kwargs) -> Variable:
        """
        Writes a Variable by name to the debugger

        Args:
            name (str): Name of the Variable that should be written
            value: Value that should be written

        Returns:
            Variable: Result
        """
        var = Variable(self.__conn, name=name, value=value)
        if isinstance(var.value, int):
            self.__conn.cmd("Var.Assign {name}={value}.".format(name=var.name, value=var.value))
        elif isinstance(var.value, float):
            self.__conn.cmd("Var.Assign {name}={value}".format(name=var.name, value=var.value))
        else:
            raise VariableError("type of value not supported: " + type(var.value))
        return var
