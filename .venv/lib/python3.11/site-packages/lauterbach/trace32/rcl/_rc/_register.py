import enum
import struct

from ._error import RegisterError, RegisterValueError
from typing import List


class Register:

    def __init__(self, conn, *, core=None, name=None, value=None, unit=None, fvalue=None):
        self.__conn = conn
        self.core = core
        self.name = name
        self.unit = unit
        self.value = value
        self.fvalue = fvalue

    def __eq__(self, other):
        if not isinstance(other, Register):
            return NotImplemented
        if self.core == other.core and self.name == other.name and self.value == other.value:
            return True
        else:
            return False

    def __str__(self):
        if self.__value is not None:
            tempvalue = struct.pack(">q", self.__value)
            i = 0
            while tempvalue[i] == 0 and i < (len(tempvalue) - 1):
                i = i + 1
            tempvalue = tempvalue[i : len(tempvalue)]
        else:
            tempvalue = None

        return "{{name: '{}', unit: '{}'{value:}{fvalue:}{core:}}}".format(
            self.__name,
            self.__unit,
            value="" if tempvalue is None else ", value: 0x{}".format("".join(format(x, "02X") for x in tempvalue)),
            fvalue="" if self.__fvalue is None else ", fvalue: {}".format(self.__fvalue),
            core="" if self.__core is None else ", core: {}".format(self.__core),
        )

    @property
    def core(self):
        return self.__core

    @core.setter
    def core(self, core):
        self.__core = core

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def unit(self):
        return self.__unit

    @unit.setter
    def unit(self, unit):
        self.__unit = unit

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if value is None:
            self.__value = None
        elif isinstance(value, int):
            self.__value = value
            self.__fvalue = None
        else:
            raise RegisterValueError("value has invalid type {} expected int".format(type(value)))

    @property
    def fvalue(self):
        return self.__fvalue

    @fvalue.setter
    def fvalue(self, fvalue):
        if fvalue is None:
            self.__fvalue = None
        elif isinstance(fvalue, float):
            self.__fvalue = fvalue
            self.__value = None
        else:
            raise RegisterValueError("value has invalid type {} expected float".format(type(fvalue)))

    def _deserialize(self, data):
        """
        deserializes data until it has found a complete register and changes intrinsic registervalues accordingly

        Args:
            data(bytes): bytes to deserialize

        Returns:
            int:  length of the part containing the processed register
        """
        counter = 0

        if data[counter : (counter + 2)] == b"NM":
            # Name extraction
            name_len = int.from_bytes(data[(counter + 2) : (counter + 3)], byteorder="little", signed=False,)
            name = (data[(counter + 4) : (counter + name_len + 4)]).decode("unicode_escape")

            if name[-1] == "\x00":
                name = name[:-1]
            self.__name = name
            counter += 4 + name_len

        if data[counter : (counter + 2)] == b"TY":
            # Type extraction
            reg_type = data[(counter + 2) : (counter + 4)]
            self.__unit = Unit(int.from_bytes(reg_type, byteorder="little", signed=False)).name
            counter += 4

        if data[counter : (counter + 2)] == b"VA":
            # Value extraction
            value = data[(counter + 2) : (counter + 10)]
            self.__value = int.from_bytes(value, byteorder="little", signed=False)
            counter += 10

        if data[counter : (counter + 2)] == b"FV":
            # Floating Point Value extraction
            self.__fvalue = struct.unpack("<d", data[(counter + 2) : (counter + 10)])[0]
            counter += 10

        if data[counter : (counter + 2)] == b"CO":
            # Core extraction
            self.__core = int.from_bytes(data[(counter + 2) : (counter + 4)], byteorder="little", signed=True,)
            counter += 4

        if data[counter : (counter + 2)] == b"XX":
            return counter
        return counter + 1

    def _serialize(self):
        """
        Parses specified register values to a message ready to send to the API

        Returns:
            bytes: Result
        """
        result = bytes()
        name = self.name
        core = self.core
        value = self.value
        fvalue = self.fvalue
        unit = self.unit

        if name is not None:
            if not isinstance(name, str):
                raise TypeError("Expected name of Register to be of type {} but got {}".format(str, type(name)))
            name_len = len(name)
            if name_len & 1:
                name_len += 1
            result += struct.pack("2sH{}s".format(name_len), "NM".encode(), name_len, name.encode())

        if unit is not None:
            try:
                if not isinstance(unit, str):
                    raise TypeError("Expected unit of Register to be of type {} but got {}".format(str, type(unit)))
                reg_type = Unit[unit.upper()].value
            except (KeyError, AttributeError):
                raise ValueError("{}: invalid unit of register".format(unit))
        else:
            reg_type = Unit.CPU.value

        result += struct.pack("2sH", "TY".encode(), reg_type)

        if value is not None:
            if not isinstance(value, int):
                raise TypeError("Expected value of Register to be of type {} but got {}".format(int, type(value)))
            try:
                bytes_value = struct.pack("q", value)
            except struct.error:
                bytes_value = struct.pack("Q", value)
            result += struct.pack("2s", "VA".encode())
            result += bytes_value

        if fvalue is not None:
            if not isinstance(fvalue, float):
                raise TypeError("Expected fvalue of Register to be of type {} but got {}".format(float,
                                                                                                 type(fvalue)))
            bytes_value = struct.pack("d", fvalue)
            result += struct.pack("2s", "FV".encode())
            result += bytes_value

        if core is not None:
            if not isinstance(core, int):
                raise TypeError("Expected core of Register to be of type {} but got {}".format(type(int), type(value)))
            result += struct.pack("2sH", "CO".encode(), core)

        result += struct.pack("4s", "XXXX".encode())

        return result

    def to_dict(self):
        """
        Translates Register into dict

        Returns:
            dict: Result
        """
        return {
            "name": self.__name,
            "unit": self.__unit,
            "core": self.__core,
            "value": self.__value,
            "fvalue": self.__fvalue,
        }

    def read(self):
        """
        Updates own Parameters by re-reading itself from the debugger
        """
        self._deserialize(self.__conn.register.read_list([self])[0]._serialize())

    def write(self):
        """
        Writes current register state to the debugger
        """
        self.__conn.register.write_list([self])


class Mode(enum.IntEnum):
    READALL = 0x00
    READBYNAMES = 0x02
    WRITEBYNAMES = 0x03


class Unit(enum.IntEnum):
    CPU = 0x04
    FPU = 0x08
    VPU = 0x10


register_list = List[Register]
string_list = List[str]
integer_list = List[int]
float_list = List[float]


class RegisterService:
    def __init__(self, conn):
        self.__conn = conn

    def __call__(self, *args, **kwargs):
        return Register(self.__conn, *args, **kwargs)

    def __read_write_exp(self, data):
        """
        Forwards specified data to the Api and returns the answer

        data (Bytes): Bytes containing the Instructions for the API

        Returns:
            Bytes: Result
        """
        result = self.__conn.t32_exp(3, data)
        if result.payload is None:
            raise RegisterError(result.err_code, result.err_msg)
        else:
            return self.__deserialize_registers(result.payload)

    def __deserialize_registers(self, data) -> register_list:
        """
        Parses data to a list of Register objects

        Args:
            data (bytes): Bytes containing the register parameters

        Returns:
            List(Register): Result
        """
        counter = 0
        registers = []
        while counter < len(data):
            reg = Register(self.__conn)
            counter += reg._deserialize(data[counter:])
            if data[counter : (counter + 2)] == b"XX" and reg.name is not None:
                counter += 4
                registers.append(reg)
            else:
                counter += 1

        return registers

    def read(self, name: str, **kwargs) -> Register:
        """
        Reads single Register

        Args:
            name: name of register

        Returns:
            Register: Result
        """
        return self.read_by_name(name=name, **kwargs)

    def read_by_name(self, name: str, **kwargs) -> Register:
        """
        Reads single Register by name

        Args:
            name(str): name of the register to read.

        Returns:
            Register: Result
        """
        return self.read_by_names(names=[name], **kwargs)[0]

    def read_by_names(self, names: string_list, **kwargs) -> register_list:
        """
        Reads registers specified by a list of names

        Args:
            names (List(String)): Names of registers to read.

        Returns:
            List[Register]: Result
        """

        regs = []
        for name in names:
            regs.append(Register(self.__conn, name=name, **kwargs))

        registers = self.read_list(regs)
        return registers

    def read_all(self, *, core=None, unit=None) -> register_list:
        """
        Reads all Registers

        Args:
            core (int, optional): core from which to read.
            unit (string, optional): Type that the Registers should have(CPU, FPU, VPU).

        Returns:
            List[Register]: Result
        """

        data = bytes()
        mode = Mode.READALL.value
        nregs = 1
        data += struct.pack("2H", mode, nregs)

        data += Register(self.__conn, name=None, core=core, unit=unit, value=None)._serialize()

        registers = self.__read_write_exp(data=data)

        return registers

    def read_list(self, regs: register_list) -> register_list:
        """
        Reads a list of Register objects.

        Args:
            regs (List(Register)): Registers to read.

        Returns:
            List[Register]: Result
        """

        if not isinstance(regs, list):
            raise TypeError("Expected argument of type {} but got {}".format(list, type(regs)))

        data = bytes()

        mode = Mode.READBYNAMES.value
        nregs = len(regs)

        data += struct.pack("2H", mode, nregs)
        for reg in regs:
            if not isinstance(reg, Register):
                raise TypeError("Expected list content to be of type {} but got {}".format(Register, type(reg)))
            data += reg._serialize()

        registers = self.__read_write_exp(data=data)
        return registers

    def write(self, name: str, value: (int, float), **kwargs) -> Register:
        """
        Writes single Register

        Args:
            name (String): name of register on which to write.
            value (int, float): value to write

        Returns:
            Register: written Register
        """
        return self.write_by_name(name=name, value=value, **kwargs)

    def write_by_name(self, name: str, value: (int, float), **kwargs) -> Register:
        """
        Writes value to register specified by name

        Args:
            name (String): name of register on which to write.
            value (int, float): value to write

        Returns:
            Register: Register with specified values
        """
        return self.write_by_names(names=[name], values=[value], **kwargs)[0]

    def write_by_names(self, names: string_list, values: (integer_list, float_list), **kwargs) -> register_list:
        """
        Writes one specified value or a list of specified values to registers specified by a list of names

        Args:
            names (List(String)): names of registers on which to write.
            values (list(int), list(float)): Values to write

        Returns:
            List[Register]: List of registers with the specified values
        """
        counter = 0
        regs = []
        for name in names:
            if isinstance(values[counter], int):
                regs.append(Register(self.__conn, name=name, value=values[counter], **kwargs))
            elif isinstance(values[counter], float):
                regs.append(Register(self.__conn, name=name, fvalue=values[counter], **kwargs))
            else:
                raise TypeError("Can't write value of type {}".format(type(values[counter])))

            counter += 1
        return self.write_list(regs)

    def write_list(self, regs: register_list) -> register_list:
        """
        Writes a list of Register Objects.

        Args:
            regs (List(Register)): Registers to write.

        Returns:
            List[Register]: Written registers
        """

        if not isinstance(regs, list):
            raise TypeError("Expected argument of type {} but got {}".format(list, type(regs)))

        data = bytes()

        mode = Mode.WRITEBYNAMES.value
        nregs = len(regs)

        data += struct.pack("2H", mode, nregs)
        for reg in regs:
            if not isinstance(reg, Register):
                raise TypeError("Expected list content to be of type {} but got {}".format(Register, type(reg)))
            data += reg._serialize()

        self.__read_write_exp(data=data)
        return regs
