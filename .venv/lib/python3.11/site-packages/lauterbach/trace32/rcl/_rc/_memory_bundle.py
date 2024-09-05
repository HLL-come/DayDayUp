import abc
import copy
import dataclasses
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Union

from ._address import Address

Buffer = Union[bytes, bytearray, memoryview]

_EMU_CBMAXDATASIZE = 0x3C00


class MemoryAccessError(Exception):
    pass


class MemoryReadAccessError(MemoryAccessError):
    pass


class MemoryWriteAccessError(MemoryAccessError):
    pass


class MemoryAccessBundleType(IntEnum):
    WRITE = 0
    READ = 1
    READWRITE = 2


class MemoryAccess(abc.ABC):
    @abc.abstractmethod
    def serialize(self) -> bytes: ...

    @abc.abstractmethod
    def deserialize(self, data: Buffer) -> tuple[Buffer, "MemoryAccessResult"]: ...


@dataclass
class MemoryAccessResult:
    """Result of a memory access.

    Attributes:
        data (Optional[bytes]): Data if data was returned, None otherwise.
        error (Optional[Exception], optional): Exception when an error occurred, None otherwise.
    """
    data: Optional[bytes] = None
    error: Optional[Exception] = None


@dataclass
class MemoryReadAccess(MemoryAccess):
    address: Address
    length: int
    width: Optional[int]

    def serialize(self) -> bytes:
        tmp = (
            bytearray()
            + struct.pack("<HH", MemoryAccessBundleType.READ, self.length)
            + self.address.serialize(width=1)[1]
        )
        return tmp

    def deserialize(self, buffer: Buffer) -> tuple[Buffer, "MemoryAccessResult"]:
        ok = struct.unpack_from("<H", buffer)[0]
        if ok == 1:
            data = buffer[2 : 2 + self.length]
            return buffer[2 + self.length :], MemoryAccessResult(data, None)
        else:
            error = MemoryReadAccessError(f"memory error at address {self.address}")
            return buffer[2:], MemoryAccessResult(None, error)


@dataclass
class MemoryWriteAccess(MemoryAccess):
    address: Address
    data: bytes
    width: Optional[int]

    def __post_init__(self):
        self.lenght = len(self.data)

    def serialize(self) -> bytes:
        assert self.data is not None
        tmp = (
            bytearray()
            + struct.pack("<HH", MemoryAccessBundleType.WRITE, len(self.data))
            + self.address.serialize(width=1)[1]
            + self.data
        )
        if len(self.data) % 2:
            tmp += b"\0"
        return tmp

    def deserialize(self, buffer: Buffer) -> tuple[Buffer, "MemoryAccessResult"]:
        ok = struct.unpack_from("<H", buffer)[0]
        if ok == 1:
            return buffer[2:], MemoryAccessResult(None, None)
        else:
            error = MemoryWriteAccessError(f"memory error at address {self.address}")
            return buffer[2:], MemoryAccessResult(None, error)


@dataclass
class MemoryReadWriteAccess(MemoryAccess):
    address: Address
    data: bytes
    mask: bytes
    width: Optional[int]
    length: int = dataclasses.field(init=False)

    def __post_init__(self):
        assert len(self.data) == len(self.mask)
        self.length = len(self.data)

    def serialize(self) -> bytes:
        assert len(self.data) == len(self.mask)
        tmp = (
            bytearray()
            + struct.pack("<HH", MemoryAccessBundleType.READWRITE, len(self.data))
            + self.address.serialize(width=1)[1]
            + self.data
            + self.mask
        )
        return tmp

    def deserialize(self, buffer: Buffer) -> tuple[Buffer, "MemoryAccessResult"]:
        ok = struct.unpack_from("<H", buffer)[0]
        if ok == 1:
            data = buffer[2 : 2 + self.length]
            return buffer[2 + self.length :], MemoryAccessResult(data, None)
        else:
            error = MemoryWriteAccessError(f"memory error at address {self.address}")
            return buffer[2:], MemoryAccessResult(None, error)


class MemoryAccessBundle:
    def __init__(self) -> None:
        self.access_list: List[MemoryAccess] = []

    def add_read(self, address: Address, *, length: int, width: Optional[int] = None) -> None:
        """Add a read access to the bundle.

        Args:
            address (Address): Read address.
            length (int): Access length in bytes.
            width (Optional[int], optional): Access width in bytes. Defaults to None.
        """
        self.access_list.append(MemoryReadAccess(copy.copy(address), length, width))

    def add_write(self, address: Address, data: bytes, *, width: Optional[int] = None) -> None:
        """Add a write access to the bundle.

        Args:
            address (Address): Write address.
            data (bytes): Bytes to write.
            width (Optional[int], optional): Access width in bytes. Defaults to None.
        """
        assert len(data)
        self.access_list.append(MemoryWriteAccess(copy.copy(address), data, width))

    def add_readwrite(self, address: Address, data: bytes, mask: bytes, *, width: Optional[int] = None) -> None:
        """Add a read-write access to the bundle.

        First reads len(data) bytes at address. Then writes ((read_data & ~mask) | (data & mask)) to address.

        Args:
            address (Address): Read-write address
            data (bytes): Bytes to write.
            mask (bytes): Mask for write.
            width (Optional[int], optional): Access width in bytes. Defaults to None.
        """
        assert len(data) == len(mask)
        self.access_list.append(MemoryReadWriteAccess(copy.copy(address), data, mask, width))

    def serialize(self) -> bytes:
        data = bytearray(struct.pack("<HH", 0, len(self.access_list)))
        for access in self.access_list:
            data += access.serialize()
        data += b"XX"
        struct.pack_into("<H", data, 0, len(data))  # overwrite data[0:2]
        if len(data) > _EMU_CBMAXDATASIZE:
            raise NotImplementedError("splitting into multiple bundles not yet implemented")
        return data

    def deserialize(self, buffer: Buffer) -> tuple[Buffer, list[MemoryAccessResult]]:
        results: list[MemoryAccessResult] = []
        for access in self.access_list:
            buffer, result = access.deserialize(buffer)
            results.append(result)
        assert buffer[:2] == b"XX"
        return buffer[2:], results
