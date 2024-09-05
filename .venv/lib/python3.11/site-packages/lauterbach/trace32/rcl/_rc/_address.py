import re
import struct

from .common import int2bytearray, up_align

re_addr_access = "(?:(?P<access>.+):)?"
re_addr_machine_id = "(?:(?P<machine_id>.+):::)?"
re_addr_space_id = "(?:(?P<space_id>.+)::)?"
re_addr_value = "(?P<value>(?:[0-9]+)|(?:0x[0-9a-fA-F]+))"
re_addr = re.compile(r"^{}{}{}{}$".format(re_addr_access, re_addr_machine_id, re_addr_space_id, re_addr_value))

T32_ADDRTYPE_NONE = 0
T32_ADDRTYPE_COMMON = 1
T32_ADDRTYPE_A32 = 2
T32_ADDRTYPE_A64 = 3
T32_ADDRTYPE_MAX = 4


class Address:
    def __init__(self, conn, *, access: str = None, value: int = None, **kwargs):
        self.__conn = conn
        self.access = access
        self.value = value
        for key, value in kwargs.items():
            if value is not None:
                raise TypeError("__init__() got an unexpected keyword argument '{}'".format(key))

    def __str__(self):
        return "{}0x{:08x}".format("" if self.__access is None else self.__access + ":", self.__value)

    @property
    def access(self):
        return self.__access

    @access.setter
    def access(self, access):
        self.__access = access

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if value is None:
            self.__value = None
        elif isinstance(value, int):
            self.__value = value
        elif isinstance(value, str):
            self.__value = int(value, 0)
        else:
            raise TypeError(type(value))

    @staticmethod
    def from_string(conn, string):
        """
        Creates an Address object from string

        Args:
            conn (Debugger): Connection to the debugger.
            string (str): String representing the Address

        Returns:
            Address: Result
        """
        return Address(conn, **re_addr.match(string).groupdict())

    def to_dualport(self):
        """
        Converts Address to dualport

        Returns:
            Address: Result
        """
        addr_str = self.__conn.fnc("CONVert.ADDRESSTODUALPORT({})".format(str(self)))
        return self.from_string(self.__conn, addr_str)

    @classmethod
    def deserialize(cls, conn, recv_buffer):
        read_ptr = 0
        parameter_id_len = 2

        addr_type = int.from_bytes(recv_buffer[:2], byteorder="little")

        if addr_type == T32_ADDRTYPE_A32:
            addr_value = int.from_bytes(recv_buffer[2:6], byteorder="little")
            read_ptr += 6
        elif addr_type == T32_ADDRTYPE_A64:
            addr_value = int.from_bytes(recv_buffer[2:10], byteorder="little")
            read_ptr += 10
        else:
            raise ValueError(addr_type)

        while read_ptr < len(recv_buffer):
            parameter_id = recv_buffer[read_ptr : read_ptr + parameter_id_len]

            if parameter_id == b"AC":
                read_ptr += parameter_id_len
                addr_access_len = int.from_bytes(recv_buffer[read_ptr : read_ptr + 2], byteorder="little")
                read_ptr += 2
                value = recv_buffer[read_ptr : read_ptr + addr_access_len]
                next_read_ptr = read_ptr + addr_access_len
                addr_access = cls.parse_access(value)
            elif parameter_id == b"WI":
                read_ptr += parameter_id_len
                next_read_ptr = read_ptr + 2
                # addr_width = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")
            elif parameter_id == b"CO":
                read_ptr += parameter_id_len
                next_read_ptr = read_ptr + 2
                addr_core = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")
            elif parameter_id == b"SI" or parameter_id == b"IM":
                read_ptr += parameter_id_len
                next_read_ptr = read_ptr + 4
                addr_spaceid = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")
            elif parameter_id == b"AT":
                read_ptr += parameter_id_len
                next_read_ptr = read_ptr + 4
                addr_attr = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")
            elif parameter_id == b"MU":
                read_ptr += parameter_id_len
                next_read_ptr = read_ptr + 2
                addr_sizeofmau = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")
            elif parameter_id == b"TU":
                read_ptr += parameter_id_len
                next_read_ptr = read_ptr + 2
                addr_targetsizeofmau = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")
            elif parameter_id == b"XX":
                read_ptr += parameter_id_len
                break
            else:
                raise ValueError(parameter_id)

            read_ptr = next_read_ptr
            # ignore all the other attributes received as they are not implemented yet

        return read_ptr, cls(conn, access=addr_access, value=addr_value)

    @staticmethod
    def parse_access(byte_buffer):
        result = byte_buffer.decode()
        result = result.strip("\x00")
        result = result.strip(":")
        return result

    def serialize(self, address_offset: int = 0, *, width=None):
        # optional width parameter for memory accesses, might be hacky but this way we don't need a width member

        # fixed address type
        addr_type = T32_ADDRTYPE_A64
        result = int2bytearray(addr_type, 2)
        if addr_type == T32_ADDRTYPE_A32:
            tmp_ui32 = self.value + address_offset
            result += int2bytearray(tmp_ui32, 4)
        elif addr_type == T32_ADDRTYPE_A64:
            tmp_ui64 = self.value + address_offset
            result += int2bytearray(tmp_ui64, 8)
        else:
            raise ValueError(addr_type)

        if self.access is not None:
            access = self.access.encode()
            access_len = len(access) + 1
            # align access length to even bytes:
            access_len += (0 - access_len) % 2

            result += struct.pack("<2sH{}s".format(access_len), b"AC", access_len, access)

        if width is not None:
            result += struct.pack("<2sH", b"WI", width)

        # if self.core is not None:
        #     result += b"CO"
        #     result += int2bytearray(self.core, 2)

        # if self.spaceid is not None:
        #     result += b"SI"
        #     result += int2bytearray(self.spaceid, 2)

        # if self.attr is not None:
        #     result += b"AT"
        #     result += int2bytearray(self.attr, 2)

        # if self.sizeofmau is not None:
        #     result += b"MU"
        #     result += int2bytearray(self.sizeofmau, 2)

        result += b"XX"  # = end marker

        return len(result), result


class AddressService:
    def __init__(self, conn):
        self.__conn = conn

    def __call__(self, *args, **kwargs):
        return Address(self.__conn, *args, **kwargs)

    def from_string(self, string) -> Address:
        """
        Generates Address object from string

        Args:
            string(str): String representing the Address.

        Returns:
            Address: Result
        """
        return Address.from_string(self.__conn, string)
