import abc
import copy
import dataclasses
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum
from functools import wraps
from typing import Any, List, Optional, Union

Buffer = Union[bytes, bytearray, memoryview]

_EMU_CBMAXDATASIZE = 0x3C00
_T32_TAPACCESSSEND_HEADERSIZE = 6


def kwargs_only(cls):
    """Workaround for @dataclass(kw_only=True) before Python 3.10"""  # noqa

    @wraps(cls)
    def call(**kwargs):
        return cls(**kwargs)

    return call


class DirectAccessError(Exception):
    pass


@dataclass
class DirectAccess(abc.ABC):
    _payload_len: int = dataclasses.field(init=False, repr=False, default=0)

    def _serialize_header(self, cmd, payload_bitlen) -> bytes:
        data = bytearray()
        if payload_bitlen < 0x0F:
            data += struct.pack("<B", (cmd << 4) | payload_bitlen)
        elif payload_bitlen < 0xFF:
            data += struct.pack("<BB", (cmd << 4) | 0x0F, payload_bitlen)
        else:
            data += struct.pack("<BBL", (cmd << 4) | 0x0F, 0xFF, payload_bitlen)

        return data

    @abc.abstractmethod
    def _serialize(self) -> bytes: ...

    @abc.abstractmethod
    def _deserialize(self, data: bytes) -> tuple[bytes, "DirectAccessResult"]: ...


class DirectAccessResult:
    pass


class DirectAccessCommand(IntEnum):
    SETINFO = 2
    GETINFO = 3
    SHIFTRAW = 12


class DirectAccessInstanceType(IntEnum):
    TAP = 0
    DAP = 1
    AHB = 2
    APB = 3
    AXI = 4
    I2C = 5  # preliminary


class DirectAccessInfoId(IntEnum):
    TRISTATE_UINT32 = 0
    SWD_UNIT32 = 2
    INSTANCE_EXISTS_UNIT32 = 3

    XXX_DAP_INSTANCE_UINT32 = 300
    XXX_DAPACCESSPORT_UINT32 = 301
    XXX_SYSPOWERUPREQ_UINT32 = 302
    XXX_BIGENDIAN_UINT32 = 303
    XXX_AP_ADDRESS_UINT64 = 304
    XXX_AP_BASETYPE_UINT32 = 305
    XXX_AP_BASEINSTANCE_UINT32 = XXX_DAP_INSTANCE_UINT32

    TAP_CURRENTINSTANCE_UINT32 = 100
    TAP_IRPRE_UINT32 = 101
    TAP_IRPOST_UINT32 = 102
    TAP_DRPRE_UINT32 = 103
    TAP_DRPOST_UINT32 = 104
    TAP_PARKSTATE_UINT32 = 105
    TAP_MCTAPSTATE_UINT32 = 106
    TAP_MCTCKLEVEL_UINT32 = 107
    TAP_DAP_INSTANCE_UINT32 = XXX_AP_BASEINSTANCE_UINT32
    TAP_DAP_ACCESSPORT_UINT32 = XXX_DAPACCESSPORT_UINT32
    TAP_DAP_JTAGACCESSPORTINDEX_UINT32 = 122
    TAP_AUTO_MULTICORETAPSTATE_UINT32 = 123
    TAP_SELECT_SHIFT_PATTERN_UINT32 = 124


class DirectAccessTapInfoId(IntEnum):
    CURRENTINSTANCE_UINT32 = 100
    IRPRE_UINT32 = 101
    IRPOST_UINT32 = 102
    DRPRE_UINT32 = 103
    DRPOST_UINT32 = 104
    PARKSTATE_UINT32 = 105
    MCTAPSTATE_UINT32 = 106
    MCTCKLEVEL_UINT32 = 107
    DAP_INSTANCE_UINT32 = DirectAccessInfoId.XXX_AP_BASEINSTANCE_UINT32
    DAP_ACCESSPORT_UINT32 = DirectAccessInfoId.XXX_DAPACCESSPORT_UINT32
    DAP_JTAGACCESSPORTINDEX_UINT32 = 122
    AUTO_MULTICORETAPSTATE_UINT32 = 123
    SELECT_SHIFT_PATTERN_UINT32 = 124


@dataclass
class DirectAccessGetInfo(DirectAccess):
    instance_type: DirectAccessInstanceType
    instance: int
    info_id: DirectAccessInfoId

    def _serialize(self) -> bytes:

        cmd = int(DirectAccessCommand.GETINFO)

        print(self.info_id.name)

        payload = bytearray()
        payload += b"\xff\xff\xff\xff"
        payload += struct.pack("<BHH", self.instance_type, self.instance, self.info_id)
        # TODO value.uint64 / T32_DirectAccessInfoIs64
        self._payload_len = len(payload)
        assert self._payload_len >= 8
        payload_bitlen = len(payload) * 8

        return self._serialize_header(cmd, payload_bitlen) + payload

    def _deserialize(self, data: bytes) -> tuple[bytes, "DirectAccessResult"]:
        value = int.from_bytes(data[:4], byteorder="little")
        return data[self._payload_len :], DirectAccessGetInfoResult(value)


@dataclass
class DirectAccessGetInfoResult(DirectAccessResult):
    value: int


@dataclass
class DirectAccessSetInfo(DirectAccess):

    instance_type: DirectAccessInstanceType
    instance: int
    info_id: int
    value: int

    def _serialize(self) -> bytes:

        cmd = int(DirectAccessCommand.SETINFO)

        payload = bytearray()
        payload += b"\xff\xff\xff\xff"
        payload += struct.pack("<BHH", self.instance_type, self.instance, self.info_id)
        payload += struct.pack("<L", self.value)
        # TODO value.uint64 / T32_DirectAccessInfoIs64
        self._payload_len = len(payload)
        payload_bitlen = len(payload) * 8

        return self._serialize_header(cmd, payload_bitlen) + payload

    def _deserialize(self, data: bytes) -> tuple[bytes, "DirectAccessResult"]:
        raise NotImplementedError()
        return data, DirectAccessResult()


class DirectAccessShiftRawOption(IntEnum):
    NONE = 0x0000
    _INTERNAL_TMS = 0x0001
    _INTERNAL_TDI = 0x0002
    _INTERNAL_TDO = 0x0004
    _INTERNAL_ALL = 0x0007
    LASTTMS_ONE = 0x0008
    TMS_ZERO = NONE
    TMS_ONE = 0x0010
    TDI_ZERO = NONE
    TDI_LASTTDO = 0x0020
    TDI_ONE = 0x0040


# @kwargs_only  # Python 3.10: @dataclass(kw_only=True)
@dataclass
class DirectAccessShiftRawOptions:
    """Direct access shift raw options.

    At most one tms and tdi option should be set.

    Attributes:
        lasttms_one (bool): Set to shift TMS = 0, except for the last cycle shift TMS = 1. Defaults to False.
        tms_one (bool): Set to shift TMS = 1. Defaults to False.
        tdi_lasttdo (bool): Set to shift TDI pattern that equals last read back TDO. Defaults to False.
        tdi_one (bool): Set to shift TDI = 1. Defaults to False.
    """

    lasttms_one: bool = False
    tms_one: bool = False
    tdi_lasttdo: bool = False
    tdi_one: bool = False


# @kwargs_only  # Python 3.10: @dataclass(kw_only=True)
@dataclass
class DirectAccessShiftRaw(DirectAccess):
    """Direct access raw shift.

    This function is used to send/receive arbitrary TDI/TMS/TDO patterns. The buffers are considered bit wise
    beginning with the first byte e.g. tdi = 0x03 0x04 will shift out 1 1 0 0 0 0 0 0 0 0 1 0 0 0 0 0 for TDI.

    If no tms/tdi is provided by default all 0s are shifted. This can be changed using the options parameter.

    Attributes:
        num_bits (bytes): Number of bits to shift (TCK cycles).
        tms (Optional[Exception], optional): TMS shift pattern. Defaults to None.
        tdi (Optional[Exception], optional): TDI shift pattern. Defaults to None.
        tdo (bool): If True then TDO is captured. Defaults to False.
        options (DirectAccessShiftRawOptions): Defaults to DirectAccessShiftRawOptions()
    """

    num_bits: int
    tms: Optional[bytes] = None
    tdi: Optional[bytes] = None
    tdo: bool = False
    options: DirectAccessShiftRawOptions = dataclasses.field(default_factory=lambda: DirectAccessShiftRawOptions())

    def _serialize_payload(self) -> bytes:
        tmp = bytearray()

        options: int = DirectAccessShiftRawOption.NONE
        if self.tms:
            options |= DirectAccessShiftRawOption._INTERNAL_TMS
        if self.tdi:
            options |= DirectAccessShiftRawOption._INTERNAL_TDI
        if self.tdo:
            options |= DirectAccessShiftRawOption._INTERNAL_TDO
        if self.options.lasttms_one:
            options |= DirectAccessShiftRawOption.LASTTMS_ONE
        if self.options.tms_one:
            options |= DirectAccessShiftRawOption.TMS_ONE
        if self.options.tdi_lasttdo:
            options |= DirectAccessShiftRawOption.TDI_LASTTDO
        if self.options.tdi_one:
            options |= DirectAccessShiftRawOption.TDI_ONE

        tmp += b"\x90"  # EMUMCI CMD Special Shift - see targetsystemtools.cpp
        tmp += b"\x00"  # EMUMCI CMD Special Shift sub function 0x0
        tmp += options.to_bytes(length=2, byteorder="little")
        tmp += self.num_bits.to_bytes(length=4, byteorder="little")
        if self.tms:
            tmp += self.tms
        if self.tdi:
            tmp += self.tdi
        if self.tms is None and self.tdi is None and self.tdo:
            # fake payload if we want tdo but no tdi/tms
            tmp += bytes((self.num_bits + 7) // 8)

        return tmp

    def _serialize(self) -> bytes:

        cmd = int(DirectAccessCommand.SHIFTRAW)
        cmd |= 0x02  # poutbits always for shift raw
        if self.tdo:  # pinbits
            cmd |= 0x01

        payload = self._serialize_payload()
        self._payload_len = len(payload)
        payload_bitlen = self._payload_len * 8

        return self._serialize_header(cmd, payload_bitlen) + payload

    def _deserialize(self, data: bytes) -> tuple[bytes, "DirectAccessShiftRawResult"]:
        result = DirectAccessShiftRawResult()
        if self.tdo:
            result.tdo = data[: ((self.num_bits + 7) // 8)]
            return data[self._payload_len :], result
        else:
            return data, result


@dataclass
class DirectAccessShiftRawResult(DirectAccessResult):
    """Result of a direct access raw shift.

    Attributes:
        tdo (Optional[bytes]): TDO if TDO was returned, None otherwise.
    """

    tdo: Optional[bytes] = None


class DirectAccessBundleRequest:
    def __init__(self) -> None:
        self.access_list: List[DirectAccess] = []
        self.payload: bytearray = bytearray()

    def add_access(self, access: DirectAccess, buffer: Buffer) -> None:
        self.access_list.append(access)
        self.payload += buffer

    def _deserialize(self, buffer: bytes) -> tuple[bytes, List[DirectAccessResult]]:
        """(T32_BundledAccessExecute)"""  # noqa
        result: List[DirectAccessResult] = []
        for access in self.access_list:
            buffer, access_result = access._deserialize(buffer)
            result.append(access_result)
        return buffer, result


class DirectAccessBundle:
    def __init__(self) -> None:
        self._access_list: List[DirectAccess] = []

    def _execute(self, dbg, *, release_debug_port=True) -> List[DirectAccessResult]:
        results: list[DirectAccessResult] = []
        for request in self._get_requests(release_debug_port=release_debug_port):
            results.extend(dbg.library.t32_bundledaccess(request))
        return results

    def _get_requests(self, *, release_debug_port=True) -> Iterator[DirectAccessBundleRequest]:
        request = DirectAccessBundleRequest()
        for access in self._access_list:
            tmp = access._serialize()
            if len(tmp) > _EMU_CBMAXDATASIZE - 1:
                raise DirectAccessError(f"Maximum direct access size exceeded: {len(tmp)} > {_EMU_CBMAXDATASIZE - 1}")
            elif len(request.payload) + len(tmp) > _EMU_CBMAXDATASIZE - 1:
                request.payload += b"\x01"  # T32_DIRECTACCESS_HOLD
                yield request
                request = DirectAccessBundleRequest()
            request.add_access(access, tmp)
        if release_debug_port:
            request.payload += b"\x00"  # T32_DIRECTACCESS_RELEASE
        else:
            request.payload += b"\x01"  # T32_DIRECTACCESS_HOLD
        yield request

    def add_access(self, access: DirectAccess) -> None:
        """Add a (direct) access to the bundle.

        Args:
            access (DirectAccess): Direct access.
        """
        self._access_list.append(access)


class DirectAccessService:
    def __init__(self, conn):
        self.__conn = conn

    def execute_bundle(self, bundle: DirectAccessBundle, *, release_debug_port=True) -> List[DirectAccessResult]:
        """Execute direct access bundle.

        During bundle execution all debugger actions concerning the debug port will be suspended. The API has exclusive access to the debug port. Afterwards the debug port will be released if release_debug_port = True.

        Args:
            bundle (DirectAccessBundle): Direct access bundle to execute.
            release_debug_port (bool): Release debug port after bundle execution. Defaults to True.

        Returns:
            List[DirectAccessResult]: List with results.
        """  # noqa: E501
        return bundle._execute(self.__conn, release_debug_port=release_debug_port)
