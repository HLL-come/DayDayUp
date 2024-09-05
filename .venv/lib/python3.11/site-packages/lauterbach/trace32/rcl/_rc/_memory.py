import array
import struct

from ._address import Address
from ._error import BaseError, InternalError
from ._memory_bundle import MemoryAccessBundle, MemoryAccessResult


class MemoryError(BaseError):
    pass


class MemoryReadError(MemoryError):
    pass


class MemoryWriteError(MemoryError):
    pass


class MemoryService:
    def __init__(self, conn):
        self.__conn = conn
        self.byteorder = "little"

    def __byteorder(self, byteorder: str) -> str:
        """Get struct.pack / struct.unpack compatible byteorder format string.

        Args:
            byteorder (NoneType, str): None, "little" or "big".

        Returns:
            str: '<' when byteorder is 'little', '>' when byteorder is 'big', otherwise checks default byteorder.
        """
        if byteorder == "little":
            return "<"
        elif byteorder == "big":
            return ">"
        elif self.byteorder == "little":
            return "<"
        elif self.byteorder == "big":
            return ">"
        else:
            raise ValueError("byteorder must be either 'little' or 'big'")

    def _read(self, address: Address, *, length: int, width=None):
        try:
            return self.__conn.library.t32_readmemoryobj(address, length, width=width)
        except InternalError:
            raise MemoryReadError from None

    def _write(self, address: Address, data, *, length=None, width=None):
        if length is None:
            length = len(data)
        try:
            self.__conn.library.t32_writememoryobj(data, address, length, width=width)
        except MemoryError:
            raise MemoryWriteError from None

    def read(self, *args, **kwargs):
        return self._read(*args, **kwargs)

    def read_int8(self, address: Address, *, width=1) -> int:
        """Read signed 8-bit value from address and return result.

        Args:
            address (Address): Address to read from.
            width (int, optional): Reserved.

        Returns:
            int: Result
        """
        buffer = self.read(address, length=1, width=width)
        return struct.unpack("b", buffer)[0]

    def read_int8_array(self, address: Address, *, length, width=1) -> array.array:
        """Read signed 8-bit values from address and return result.

        Args:
            address (Address): Address to read from
            length (int): Array Length.
            width (int, optional): Reserved.

        Returns:
            array.array: Result
        """
        buffer = self.read(address, length=length, width=width)
        return array.array("b", struct.unpack("{}b".format(length), buffer))

    def read_uint8(self, address: Address, *, width=1) -> int:
        """Read unsigned 8-bit value from address and return result.

        Args:
            address (Address): Address to read from
            width (int, optional): Reserved.

        Returns:
            int: Result
        """
        buffer = self.read(address, length=1, width=width)
        return struct.unpack("B", buffer)[0]

    def read_uint8_array(self, address: Address, *, length=1, width=1) -> array.array:
        """Read unsigned 8-bit values from address and return result.

        Args:
            address (Address): Address to read from
            length (int): Number of 8-bit values to read
            width (int, optional): Reserved.

        Returns:
            Tuple[int]: Result
        """
        buffer = self.read(address, length=length, width=width)
        return array.array("B", struct.unpack("{}B".format(length), buffer))

    def read_int16(self, address: Address, *, byteorder=None, width=2) -> int:
        """Read signed 16-bit value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.

        Returns:
            int: Result
        """
        buffer = self.read(address, length=2, width=width)
        return struct.unpack("{byteorder}h".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_uint16(self, address: Address, *, byteorder=None, width=2) -> int:
        """Read unsigned 16-bit value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            int: Result
        """
        buffer = self.read(address, length=2, width=width)
        return struct.unpack("{byteorder}H".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_int32(self, address: Address, *, byteorder=None, width=4) -> int:
        """Read signed 32-bit value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            int: Result
        """
        buffer = self.read(address, length=4, width=width)
        return struct.unpack("{byteorder}i".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_uint32(self, address: Address, *, byteorder=None, width=4) -> int:
        """Read unsigned 32-bit value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            int: Result
        """
        buffer = self.read(address, length=4, width=width)
        return struct.unpack("{byteorder}I".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_int64(self, address: Address, *, byteorder=None, width=8) -> int:
        """Read signed 64-bit value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            int: Result
        """
        buffer = self.read(address, length=8, width=width)
        return struct.unpack("{byteorder}q".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_uint64(self, address: Address, *, byteorder=None, width=8) -> int:
        """Read unsigned 64-bit value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            int: Result
        """
        buffer = self.read(address, length=8, width=width)
        return struct.unpack("{byteorder}Q".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_float(self, address: Address, *, byteorder=None, width=4) -> float:
        """Read 32-bit IEEE floating point value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            float: Result
        """
        buffer = self.read(address, length=4, width=width)
        return struct.unpack("{byteorder}f".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def read_double(self, address, *, byteorder=None, width=8) -> float:
        """Read IEEE double value from address and return result.

        Args:
            address (Address): Address to read from
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved

        Returns:
            float: Result
        """
        buffer = self.read(address, length=8, width=width)
        return struct.unpack("{byteorder}d".format(byteorder=self.__byteorder(byteorder)), buffer)[0]

    def write(self, *args, **kwargs):
        return self._write(*args, **kwargs)

    def write_int8(self, address, value, *, width=1):
        """Write signed 8-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            width (int, optional): Reserved.
        """
        data = struct.pack("b", value)
        self.write(address, data, length=1, width=width)

    def write_int8_array(self, address, data, *, width=1):
        """Write data as signed 8-bit values to address.

        Args:
            address (Address): Address to read from
            data (Tuple[int]): Data to write.
            width (int, optional): Reserved.
        """
        data = struct.pack("{}b".format(len(data)), *data)
        self.write(address, data, width=width)

    def write_uint8(self, address, value, *, width=1):
        """Write unsigned 8-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            width (int, optional): Reserved.
        """
        data = struct.pack("B", value)
        self.write(address, data, length=1, width=width)

    def write_uint8_array(self, address, data, *, width=1):
        """Write data as signed 8-bit values to address.

        Args:
            address (Address): Address to read from
            data (Tuple[int]): Data to write.
            width (int, optional): Reserved.
        """
        data = struct.pack("{}B".format(len(data)), *data)
        self.write(address, data, width=width)

    def write_int16(self, address, value, *, byteorder=None, width=2):
        """Write signed 16-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.
        """
        data = struct.pack("{byteorder}h".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_uint16(self, address, value, *, byteorder=None, width=2):
        """Write unsigned 16-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.
        """
        data = struct.pack("{byteorder}H".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_int32(self, address, value, *, byteorder=None, width=4):
        """Write signed 32-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.
        """
        data = struct.pack("{byteorder}i".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_uint32(self, address, value, *, byteorder=None, width=4):
        """Write unsigned 32-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.
        """
        data = struct.pack("{byteorder}I".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_int64(self, address, value, *, byteorder=None, width=8):
        """Write signed 64-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.
        """
        data = struct.pack("{byteorder}q".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_uint64(self, address, value, *, byteorder=None, width=8):
        """Write unsigned 64-bit value to address.

        Args:
            address (Address): Address to write to.
            value (int): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width (int, optional): Reserved.
        """
        data = struct.pack("{byteorder}Q".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_float(self, address, value, *, byteorder=None, width=4):
        """Write 32-bit IEEE floating point value to address.

        Args:
            address (Address): Address to read from.
            value (float): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved
        """
        data = struct.pack("{byteorder}f".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def write_double(self, address, value, *, byteorder=None, width=8):
        """Write IEEE double value to address.

        Args:
            address (Address): Address to read from.
            value (float): Value to write.
            byteorder (NoneType, str): Accepted values are None, "little" and "big".
            width(int): Reserved
        """
        data = struct.pack("{byteorder}d".format(byteorder=self.__byteorder(byteorder)), value)
        self.write(address, data, width=width)

    def execute_bundle(self, bundle: MemoryAccessBundle) -> list[MemoryAccessResult]:
        """Execute memory access bundle.

        Args:
            bundle (MemoryAccessBundle): Memory access bundle to execute.

        Raises:
            MemoryError: TODO
            result.error: TODO

        Returns:
            list[MemoryAccessResult]: List with results.
        """
        try:
            results = self.__conn.library.t32_transfermemorybundleobj(bundle)
        except InternalError:
            raise MemoryError from None
        try:
            for result in results:
                if result.error:
                    raise result.error
        finally:
            return results
