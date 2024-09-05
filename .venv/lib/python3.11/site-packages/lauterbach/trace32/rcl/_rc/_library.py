import struct
import typing
from collections import namedtuple
from enum import IntEnum

from ._address import Address
from ._breakpoint import Breakpoint
from ._command import CommandError
from ._directaccess import DirectAccessBundleRequest, DirectAccessResult
from ._error import *
from ._functions import FunctionError
from ._memory import MemoryError
from ._memory_bundle import MemoryAccessBundle, MemoryAccessResult
from ._register import Register
from ._symbol import Symbol
from ._variable import VariableError
from .common import down_align, up_align
from .hlinknet import Link

RAPI_CMD_NOP = 0x70  # NOP
RAPI_CMD_ATTACH = 0x71  # Attach to Device
RAPI_CMD_EXECUTE_PRACTICE = 0x72  # Execute generic Practice command
RAPI_CMD_PING = 0x73  # Ping
RAPI_CMD_DEVICE_SPECIFIC = 0x74  # Device-Specific command
RAPI_CMD_CMDWINDOW = 0x75  # T32_CmdWin: Generic PRACTICE command with remote window
RAPI_CMD_GETMSG = 0x76  # T32_GetMessage
RAPI_CMD_SELECTPRECMD = 0x77  # Select Client number precommand. This is only used in PowerView internally.
RAPI_CMD_EDITNOTIFY = 0x78  # T32_EditNotifyEnable
RAPI_CMD_TERMINATE = 0x79  # T32_Terminate
RAPI_CMD_GETMSGSTRING = 0x7A  # T32_GetMessageString
RAPI_CMD_INTERCOMV2 = 0x7E  # Intercom V2
RAPI_CMD_INTERCOM = 0x7F  # Intercom

RAPI_DSCMD_GETSTATE = 0x10
RAPI_DSCMD_RESET = 0x11
RAPI_DSCMD_STATE_SETNOTIFIER = 0x12
RAPI_DSCMD_GETCPUINFO = 0x13
RAPI_DSCMD_EVAL_GETVALUE = 0x14
RAPI_DSCMD_MEMORY_GETMAP = 0x16
RAPI_DSCMD_EVAL_GETSTRING = 0x17
RAPI_DSCMD_EVENT_SETNOTIFIER = 0x18
RAPI_DSCMD_GETLASTERRMSG = 0x19
RAPI_DSCMD_REGISTER_READ = 0x20
RAPI_DSCMD_REGISTER_WRITE = 0x21
RAPI_DSCMD_REGISTER_PC_READ = 0x22
RAPI_DSCMD_REGISTER_READBYNAME = 0x23
RAPI_DSCMD_REGISTER_WRITEBYNAME = 0x24
RAPI_DSCMD_REGISTER_OBJ_READ = 0x25
RAPI_DSCMD_REGISTER_OBJ_WRITE = 0x26
RAPI_DSCMD_REGISTER_FPU_READ = 0x27
RAPI_DSCMD_REGISTER_FPU_WRITE = 0x28
RAPI_DSCMD_REGISTERSET_OBJ_READ = 0x29
RAPI_DSCMD_REGISTERSET_OBJ_WRITE = 0x2A
RAPI_DSCMD_MEMORY_READ = 0x30
RAPI_DSCMD_MEMORY_WRITE = 0x31
RAPI_DSCMD_MEMORY_WRITEPIPE = 0x32
RAPI_DSCMD_MEMORY_TRANSACTION = 0x33
RAPI_DSCMD_MEMORY_ACCESS_SET = 0x34
RAPI_DSCMD_MEMORY_OBJ_READ = 0x35
RAPI_DSCMD_MEMORY_OBJ_WRITE = 0x36
RAPI_DSCMD_ADDRESS_OBJ_QUERY = 0x37
RAPI_DSCMD_BUNDLE_OBJ_TRANSFER = 0x38
RAPI_DSCMD_BREAKPOINT_GET = 0x40
RAPI_DSCMD_BREAKPOINT_SET = 0x41
RAPI_DSCMD_BREAKPOINT_CLEAR = 0x42
RAPI_DSCMD_BREAKPOINT_MCD = 0x43
RAPI_DSCMD_BREAKPOINT_OBJ_READ = 0x44
RAPI_DSCMD_BREAKPOINT_OBJ_WRITE = 0x45
RAPI_DSCMD_BREAKPOINT_OBJ_QUERY = 0x46
RAPI_DSCMD_STEP_SINGLE = 0x50
RAPI_DSCMD_GO = 0x51
RAPI_DSCMD_BREAK = 0x52
RAPI_DSCMD_MODE_SET = 0x53
RAPI_DSCMD_STEP_MODE = 0x54
RAPI_DSCMD_SOURCE_GETFILE = 0x60
RAPI_DSCMD_SOURCE_GETSELECTED = 0x61
RAPI_DSCMD_SYMBOL_GET = 0x62
RAPI_DSCMD_TRIGGER_MESSAGE_GET = 0x63
RAPI_DSCMD_BREAKPOINT_LIST = 0x64
RAPI_DSCMD_VARIABLE_READVALUE = 0x65
RAPI_DSCMD_VARIABLE_READSTRING = 0x66
RAPI_DSCMD_SYMBOL_GETBYADDRESS = 0x67
RAPI_DSCMD_SYMBOL_QUERYOBJ = 0x68
RAPI_DSCMD_VARIABLE_WRITEVALUE = 0x69
RAPI_DSCMD_WINDOW_CONTENT = 0x70
RAPI_DSCMD_ANALYZER_STATE = 0x80
RAPI_DSCMD_ANALYZER_READ = 0x81
RAPI_DSCMD_TRACE_STATE = 0x82
RAPI_DSCMD_TRACE_READ = 0x83
RAPI_DSCMD_DAAPI = 0x92
RAPI_DSCMD_DAAPI_HOLD = 0x93
RAPI_DSCMD_API_LOCK = 0x94
RAPI_DSCMD_API_UNLOCK = 0x95
RAPI_DSCMD_FDX_RESOLVE = 0xA0
RAPI_DSCMD_FDX_OPEN = 0xA1
RAPI_DSCMD_FDX_RECEIVEPOLL = 0xA2
RAPI_DSCMD_FDX_RECEIVE = 0xA3
RAPI_DSCMD_FDX_TRANSMITPOLL = 0xA4
RAPI_DSCMD_FDX_TRANSMIT = 0xA5
RAPI_DSCMD_FDX_CLOSE = 0xA6
RAPI_DSCMD_LUA_EXECUTE = 0xB0
RAPI_DSCMD_FLASHFILE_READ = 0xC0
RAPI_DSCMD_FLASHFILE_WRITE = 0xC1
RAPI_DSCMD_FLASHFILE_FLUSH = 0xC2
RAPI_DSCMD_GUI_LOCK = 0xC3
RAPI_DSCMD_GUI_UNLOCK = 0xC4
RAPI_DSCMD_EXP = 0xFE
RAPI_DSCMD_EXTENSION = 0xFF

T32_ERR_OK = 0x00

T32_E_BREAK = 0x00
T32_E_EDIT = 0x01
T32_E_BREAKPOINTCONFIG = 0x02
T32_E_ONEVENT = 0x03
T32_E_RTSTRIGGER = 0x04
T32_E_ERROR = 0x05


class Library:
    """Implements Remote API protocol functions

    Args:
        configuration (str,dict): Either string or dict representation of the RCL parameters such as node, port, packlen etc.

    Attributes:
        link (Link): :py:attr:`Link<lauterbach.trace32._rc.hlinknet.Link` communication implementation for this client
        maxpacketsize (int): maximum byte count a transfer or receive call may contain, used to chop larger data transfer to chunks of requests

    """

    __LINE_SBLOCK = 4096  # small block mode (backwards compatible)

    def __init__(self, conn, *args, **kwargs):
        self.__conn = conn
        self._link = Link(**kwargs)
        self._maxpacketsize = self._link.packlen

    class NotificationEvent:
        def __init__(self, name, function):
            self.name = name
            self.__function = function

        def __call__(self, *a, **kw):
            return self.__function(*a, **kw)

    def t32_init(self):
        """Connect and init the clients communication socket"""

        self._link.connect()
        self.sync()
        self._notification_callback = {}
        self._eventlist = {}

    # == hremote.c : LINE_Sync()
    def sync(self, maxtry=5):
        """Send syncronisation request to API server"""

        for i in range(maxtry):
            if self._link.sync():
                break

    def t32_exp(self, cmd, payload):
        assert isinstance(payload, bytes) or isinstance(payload, bytearray)
        payload_length = len(payload)

        msg_len = payload_length + 2

        if msg_len > 0xF000:
            raise ApiProtocolTransmitError("message buffer too large")

        send_data = struct.pack(
            "<BBBBHH{}s{}x".format(payload_length, payload_length % 2),
            0,
            RAPI_CMD_DEVICE_SPECIFIC,
            RAPI_DSCMD_EXP,
            self._link.increment_message_id(),
            msg_len,
            cmd,
            payload,
        )

        self._link.transmit(send_data)

        recv_data = self._link.receive()

        result = self.t32_exp_deserialize_response(recv_data)
        if result.status == "Ok":
            return result
        else:
            # Note: only err_codes < 255 can arrive here...
            self.raise_error(result.err_code, result.err_msg)

    @staticmethod
    def t32_exp_deserialize_response(rbuffer):

        if not rbuffer[0] == T32_ERR_OK:
            status = rbuffer[0]
        else:
            status = "Ok"

        err_code = None
        err_msg = None
        payload = None

        msg_len = int.from_bytes(rbuffer[2:4], byteorder="little")

        read_ptr = 6  # begin according to nResBufferOffset + 2 in emuremote.c
        while read_ptr < msg_len:
            identifier = rbuffer[read_ptr : read_ptr + 2]
            if identifier == b"EM":  # error message

                err_msg_len = int.from_bytes(rbuffer[read_ptr + 2 : read_ptr + 4], byteorder="little")
                read_ptr += 4

                err_msg = rbuffer[read_ptr : read_ptr + err_msg_len].decode()

                read_ptr += err_msg_len

            elif identifier == b"EC":  # error code

                # err_code_len probably can be fixed to 2, transmission of length maby be omitted that way
                err_code_len = int.from_bytes(rbuffer[read_ptr + 2 : read_ptr + 4], byteorder="little")
                read_ptr += 4

                err_code = int.from_bytes(rbuffer[read_ptr : read_ptr + err_code_len], byteorder="little")

                read_ptr += err_code_len

            elif identifier == b"PL":  # payload

                payload_len = int.from_bytes(rbuffer[read_ptr + 2 : read_ptr + 4], byteorder="little")
                read_ptr += 4

                payload = rbuffer[read_ptr : read_ptr + payload_len]

                read_ptr += payload_len

            else:
                raise ValueError("invalid t32_exp buffer ", identifier)

        ExpResult = namedtuple("ExpResult", "status payload err_msg err_code")
        return ExpResult(status=status, payload=payload, err_msg=err_msg, err_code=err_code)

    @staticmethod
    def get_exp_serialized_buffer(status=T32_ERR_OK, err_msg=None, err_code=None, payload=None):
        rbuffer = struct.pack("<B", status)

        if err_msg is not None:
            rbuffer += struct.pack("<2sH{}s".format(len(err_msg)), b"EM", len(err_msg), err_msg.encode())

        if err_code is not None:
            rbuffer += struct.pack("<2sH{}s".format(len(err_code)), b"EC", len(err_code), err_code)

        if payload is not None:
            rbuffer += struct.pack("<2sH{}s".format(len(payload)), b"PL", len(payload), payload)

        # in fact the order should be irrelevant
        return rbuffer

    # template to do all the T32_* api functions defined in hremote.c
    def generic_api_call(
        self,
        rapi_cmd,
        opt_arg=0,
        sendonly=False,
        payload=b"",
        force_length=None,
        force_16bit_length=False,
    ):
        """Assemble and transmit API requests, receive response.

        Args:
            rapi_cmd (int): RAPI_CMD_* identifier of api command to be send
            opt_arg (int): api subcommand identifier
            sendonly (bool): flag to supress receivement of a response. Defaults to False.
            payload (bytes, bytesbuffer): message payload associated to the api command. Defaults to None.
            force_length (int): value to overwrite length field of the message

        Return:
            result: bytebuffer containing received response payload
        """

        assert isinstance(payload, bytes) or isinstance(payload, bytearray)
        payload_length = len(payload)

        msg_len = 2 + payload_length

        if force_length is not None:
            msg_len = force_length

        if msg_len > 0xFF or force_16bit_length:
            msg_len += 2

            if msg_len > 0xF000:
                raise ApiProtocolTransmitError("message buffer too large")

            send_data = struct.pack(
                "<BBBBH{}s{}x".format(payload_length, payload_length % 2),
                0,
                rapi_cmd,
                opt_arg,
                self._link.increment_message_id(),
                msg_len,
                payload,
            )
        else:

            send_data = struct.pack(
                "<BBBB{}s{}x".format(payload_length, payload_length % 2),
                msg_len,
                rapi_cmd,
                opt_arg,
                self._link.increment_message_id(),
                payload,
            )

        self._link.transmit(send_data)
        if not sendonly:
            recv_data = self._link.receive()
            if not recv_data[0] == T32_ERR_OK:
                # attempt to extract error message from response
                if len(recv_data) > 10:
                    recv_err_msg_len = int.from_bytes(recv_data[6:10], byteorder="little")
                    try:
                        recv_err_msg = recv_data[10 : 10 + recv_err_msg_len].decode()
                    except UnicodeDecodeError:
                        recv_err_msg = None
                else:
                    recv_err_msg = None

                self.raise_error(recv_data[0], recv_err_msg)

            return recv_data[2:]

    def t32_apilock(self, timeout_ms):
        payload = timeout_ms.to_bytes(4, byteorder="little")
        return self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_API_LOCK,
            payload=payload,
        )

    def t32_apiunlock(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC, opt_arg=RAPI_DSCMD_API_UNLOCK)

    def t32_nopex(self, exdata, options):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_NOP, opt_arg=(options & 0xFF), payload=exdata)

    def t32_nop(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_NOP)

    def t32_nopfail(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_NOP, sendonly=True)

    def t32_ping(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_PING)

    def t32_stop(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_EXECUTE_PRACTICE)

    def t32_terminate(self, shellreturnvalue):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_TERMINATE, opt_arg=shellreturnvalue)

    def t32_attach(self, devicespecifier=1):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_ATTACH, opt_arg=devicespecifier)

    def t32_getstate(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC, opt_arg=RAPI_DSCMD_GETSTATE)

    def t32_resetcpu(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC, opt_arg=RAPI_DSCMD_RESET)

    def t32_cmd(self, command):
        if isinstance(command, str):
            command = command.encode()
        assert isinstance(command, bytes) or isinstance(command, bytearray), "CMD given is not of type bytes"
        command += b"\x00\x00"

        return self.generic_api_call(rapi_cmd=RAPI_CMD_EXECUTE_PRACTICE, opt_arg=0x02, payload=command)

    def t32_config(self, conf):
        self._link.config = conf

    def t32_go(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC, opt_arg=RAPI_DSCMD_GO)

    def t32_break(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC, opt_arg=RAPI_DSCMD_BREAK)

    def t32_step(self):
        return self.generic_api_call(rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC, opt_arg=RAPI_DSCMD_STEP_SINGLE)

    def t32_stepmode(self, mode):
        payload = mode.to_bytes(2, byteorder="little")
        return self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_STEP_MODE,
            payload=payload,
        )

    def t32_setmode(self, mode):
        payload = mode.to_bytes(2, byteorder="little")
        return self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_MODE_SET,
            payload=payload,
        )

    def t32_executecommand(self, cmd, buffer_size):
        payload = buffer_size.to_bytes(4, byteorder="little")
        if isinstance(cmd, str):
            payload += cmd.encode() + b"\0"
        elif isinstance(cmd, bytes) or isinstance(cmd, bytearray):
            payload += cmd + b"\0"
        else:
            raise TypeError(type(cmd))

        try:
            return self.generic_api_call(
                rapi_cmd=RAPI_CMD_EXECUTE_PRACTICE,
                opt_arg=0x04,
                payload=payload,
            )
        except T32_ERR_FN1 as e:
            raise CommandError(str(e), "command: ", cmd) from None

    def t32_writememoryobj(self, buffer, address, length=None, *, width=None):
        assert isinstance(address, Address)
        headersize = 0
        chunk_size = self._maxpacketsize - headersize

        if length is None:
            remaining_size = allover_size = len(buffer)
        else:
            remaining_size = allover_size = min(length, len(buffer))

        while remaining_size:
            chunk_size = min(remaining_size, chunk_size)
            chunk_from = allover_size - remaining_size
            chunk_to = chunk_from + chunk_size

            address_params_length, address_params = address.serialize(address_offset=chunk_from, width=width)

            payload = struct.pack(
                "<H{}s{}s".format(address_params_length, chunk_size),
                chunk_size,
                address_params,
                buffer[chunk_from:chunk_to],
            )

            self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_MEMORY_OBJ_WRITE,
                payload=payload,
                force_length=address_params_length + 6,
            )
            remaining_size -= chunk_size

    def t32_readmemoryobj(self, address, length, *, width=None):
        assert isinstance(address, Address)
        headersize = self._link.getHeadersize()
        chunk_size = down_align(self._maxpacketsize - headersize, 8)
        result = bytearray(0)

        remaining_size = length
        while remaining_size:
            chunk_size = min(remaining_size, chunk_size)
            address_params_length, address_params = address.serialize(
                address_offset=length - remaining_size, width=width
            )

            payload = struct.pack("<H{}s".format(address_params_length), chunk_size, address_params)
            try:
                received = self.generic_api_call(
                    rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                    opt_arg=RAPI_DSCMD_MEMORY_OBJ_READ,
                    payload=payload,
                    force_length=address_params_length + 6,
                )
            except T32_ERR_FN1:
                raise MemoryError() from None
                # self.raise_error(int_code.T32_ERR_READMEMOBJ_PARAFAIL)

            if received is None:
                raise MemoryError()

            result += received[:chunk_size]
            remaining_size -= chunk_size

        return result

    def t32_transfermemorybundleobj(self, bundle: MemoryAccessBundle) -> list[MemoryAccessResult]:
        tx_data = bundle.serialize()
        rx_data = self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_BUNDLE_OBJ_TRANSFER,
            payload=tx_data,
            force_length=0,
        )
        _, result = bundle.deserialize(rx_data)
        return result

    def t32_readregisterobj(self, register, reg_size=64):
        assert isinstance(register, Register)
        try:
            size, payload = register.serialize(reg_size)

            return self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_REGISTER_OBJ_READ,
                payload=payload,
                force_length=len(payload) + 4,
            )

        except T32_ERR_FN1:
            raise RegisterParameterError() from None
            # self.raise_error(int_code.T32_ERR_READREGOBJ_PARAFAIL)

        except T32_ERR_FN2:
            raise RegisterError() from None
            # self.raise_error(int_code.T32_ERR_READREGOBJ_MAXCORE)

        except T32_ERR_FN3:
            raise RegisterNotFoundError() from None
            # self.raise_error(int_code.T32_ERR_READREGOBJ_NOTFOUND)

    def t32_writeregisterobj(self, register, reg_size=64):
        assert isinstance(register, Register)
        try:
            size, payload = register.serialize(reg_size)

            return self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_REGISTER_OBJ_WRITE,
                payload=payload,
            )

        except T32_ERR_FN1:
            raise RegisterParameterError()
            # self.raise_error(int_code.T32_ERR_WRITEREGOBJ_PARAFAIL)

        except T32_ERR_FN2:
            raise RegisterError() from None
            # self.raise_error(int_code.T32_ERR_WRITEREGOBJ_MAXCORE)

        except T32_ERR_FN3:
            raise RegisterNotFoundError() from None
            # self.raise_error(int_code.T32_ERR_WRITEREGOBJ_NOTFOUND)

        except T32_ERR_FN4:
            raise RegisterWriteError() from None
            # self.raise_error(int_code.T32_ERR_WRITEREGOBJ_FAILED)

    def t32_deletebreakpointobj(self, bp):
        return self.t32_writebreakpointobj(bp, delete=True)

    def t32_writebreakpointobj(self, bp, delete=False):
        assert isinstance(bp, Breakpoint)

        payload = {True: b"\x00\x00", False: b"\x01\x00"}.get(delete)

        try:
            bp_stream_size, bp_stream = bp.serialize()
            payload += struct.pack("<2sH{}s".format(bp_stream_size), b"hh", bp_stream_size, bp_stream)
        except Exception as e:
            raise BreakpointParameterError() from e

        try:
            return self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_BREAKPOINT_OBJ_WRITE,
                payload=payload,
                force_length=3 + len(payload),
            )

        except T32_ERR_FN1:
            raise BreakpointWriteError() from None
            # self.raise_error(int_code.T32_ERR_SETBP_FAILED)

        except T32_ERR_FN2:
            raise BreakpointWriteError() from None
            # self.raise_error(int_code.T32_ERR_WRITEBPOBJ_FAILED)

        except T32_ERR_FN3:
            raise BreakpointAddressError() from None
            # self.raise_error(int_code.T32_ERR_WRITEBPOBJ_ADDRESS)

        except T32_ERR_FN4:
            raise BreakpointActionError() from None
            # self.raise_error(int_code.T32_ERR_WRITEBPOBJ_ACTION)

    def t32_querybreakpointobjcount(self):
        payload = b"\x00\x00"

        result = self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_BREAKPOINT_OBJ_QUERY,
            payload=payload,
            force_length=4,
        )

        return int.from_bytes(result[2:6], byteorder="little")

    def t32_readbreakpointobjbyindex(self, bp_index):
        payload = struct.pack("<BxI", 0x01, bp_index)

        return self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_BREAKPOINT_OBJ_READ,
            payload=payload,
            force_length=8,
        )

    def t32_executefunction(self, func):

        func_bytes = func.encode() + b"\0"
        payload = struct.pack("<I{}s".format(len(func_bytes)), 4096, func_bytes)

        try:
            result = self.generic_api_call(
                rapi_cmd=RAPI_CMD_EXECUTE_PRACTICE,
                opt_arg=0x05,
                payload=payload,
            )

            assert result is not None
            assert len(result) >= 8

            result_type = int.from_bytes(result[:4], byteorder="little")
            result_size = int.from_bytes(result[4:8], byteorder="little")

            assert len(result) >= result_size + 8

            result_value = result[8 : 8 + result_size].decode()

            return result_value, result_type
        except T32_ERR_FN1 as e:
            raise FunctionError(str(e)) from None
            # self.raise_error(int_code.T32_ERR_EXECUTECOMMAND_FAIL)

    def t32_evalgetstring(self) -> str:
        return (
            self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_EVAL_GETSTRING,
            )
            .strip(b"\x00")
            .decode()
        )

    def t32_getwindowcontent(self, command, requested, offset, print_code):

        payload = struct.pack(
            "<III",
            requested,
            offset,
            print_code,
        )
        if isinstance(command, bytes) or isinstance(command, bytearray):
            payload += command
        elif isinstance(command, str):
            payload += command.encode()
        else:
            raise TypeError()

        result = self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_WINDOW_CONTENT,
            payload=payload,
        )

        length = int.from_bytes(result[:4], byteorder="little")
        if length >= requested:
            length = requested - 1

        return length, result[4 : 4 + length]

    def t32_querysymbolobj(self, symbol):
        assert isinstance(symbol, Symbol)

        symbol_stream_size, symbol_stream = symbol.serialize()

        # seems there is a bug, we need to add at least 6 to the real length in the symbolstream
        # otherwise we get "illegal character for this context"
        payload = struct.pack("<H{}s".format(symbol_stream_size), symbol_stream_size + 6, symbol_stream)

        return self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_SYMBOL_QUERYOBJ,
            payload=payload,
        )

    def t32_getmessage(self):

        result = self.generic_api_call(
            rapi_cmd=RAPI_CMD_GETMSG,
            opt_arg=0x00,
        )

        message_type = int.from_bytes(result[:4], byteorder="little")
        message = result[4:].decode()

        return message, message_type

    def t32_evalget(self):

        result = self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_EVAL_GETVALUE,
        )

        evaluation_result = int.from_bytes(result[:4], byteorder="little")
        return evaluation_result

    def t32_getpracticestate(self):

        result = self.generic_api_call(
            rapi_cmd=RAPI_CMD_EXECUTE_PRACTICE,
            opt_arg=0x03,
        )

        return int.from_bytes(result, byteorder="little")

    def t32_readvariablestring(self, variable_name):

        payload = variable_name.encode()
        payload += b"\x00"

        try:
            result = self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_VARIABLE_READSTRING,
                payload=payload,
            )
        except T32_ERR_FN1:
            raise VariableError() from None
            # self.raise_error(int_code.T32_ERR_READVAR_ALLOC)

        except T32_ERR_FN2:
            raise VariableError() from None
            # self.raise_error(int_code.T32_ERR_READVAR_ACCESS)

        return result.decode()

    def t32_readvariablevalue(self, variable_name):

        payload = variable_name.encode()
        payload += b"\x00"

        try:
            result = self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_VARIABLE_READVALUE,
                payload=payload,
            )
        except T32_ERR_FN1:
            raise VariableError() from None
            # self.raise_error(int_code.T32_ERR_READVAR_ALLOC)

        except T32_ERR_FN2:
            raise VariableError() from None
            # self.raise_error(int_code.T32_ERR_READVAR_ACCESS)

        return int.from_bytes(result[:8], byteorder="little")

    def t32_gettracestate(self, tracetype):
        payload = struct.pack("<Bs", tracetype, b"\x00")

        result = self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_TRACE_STATE,
            payload=payload,
        )
        state, size, min, max = struct.unpack("<Bxxxiii", result)
        return state, size, min, max

    def t32_readtrace(self, tracetype, record, n, mask):
        NUM_BYTES_RECORD = bin(mask).count("1") * 4  # Python3.10 replace this with mask.bit_count()
        MAX_RECORDS = self.__LINE_SBLOCK // NUM_BYTES_RECORD
        result = bytearray()
        num_records_remaining = n
        while num_records_remaining:
            num_records = min(num_records_remaining, MAX_RECORDS)
            payload = struct.pack("<Bxiii", tracetype, record, mask, num_records)
            result += self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_TRACE_READ,
                payload=payload,
            )
            record += num_records
            num_records_remaining -= num_records
        return result

    def t32_bundledaccess(self, request: DirectAccessBundleRequest) -> list[DirectAccessResult]:
        rx_data = self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_DAAPI,
            payload=request.payload,
            force_16bit_length=True,
        )
        _, result = request._deserialize(rx_data)
        return result

    def t32_guilock(self) -> None:
        if self.__conn._powerview_software_build_base < 172138:
            raise NotImplementedError(
                "Requires PowerView version 172138, current version is "
                + f"{self.__conn._powerview_software_build_base}--{self.__conn._powerview_software_build}"
            )
        self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_GUI_LOCK,
            payload=b"",
        )

    def t32_guiunlock(self) -> None:
        if self.__conn._powerview_software_build_base < 172138:
            raise NotImplementedError(
                "Requires PowerView version 172138, current version is "
                + f"{self.__conn._powerview_software_build_base}--{self.__conn._powerview_software_build}"
            )
        self.generic_api_call(
            rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
            opt_arg=RAPI_DSCMD_GUI_UNLOCK,
            payload=b"",
        )

    def t32_checkstatenotify(self, callback_parameter):
        """Polls for notification messages and calls callbackfunction"""

        msg_data = self._link.receive_notify_message()
        while msg_data is not None:
            event_type = msg_data[1]
            callback_func = self._notification_callback.get(event_type)

            try:
                if callback_func is not None:
                    offset = 16
                    if event_type == T32_E_BREAK:
                        pc_index = offset
                        reason_index = pc_index + 8

                        pc = int.from_bytes(msg_data[pc_index : pc_index + 8], byteorder="little")
                        reason = int.from_bytes(
                            msg_data[reason_index : reason_index + 8],
                            byteorder="little",
                        )

                        callback_func(callback_parameter, pc, reason)

                    elif event_type == T32_E_EDIT:
                        line_number = int.from_bytes(msg_data[offset : offset + 4], byteorder="little")
                        file_name = msg_data[offset + 4 :].decode()
                        callback_func(callback_parameter, line_number, file_name)

                    elif event_type == T32_E_BREAKPOINTCONFIG:
                        callback_func(callback_parameter)

                    elif event_type == T32_E_RTSTRIGGER:
                        time_index = offset
                        code_index = time_index + 8
                        param_index = code_index + 8
                        time = int.from_bytes(msg_data[time_index : time_index + 4], byteorder="little")
                        code = int.from_bytes(msg_data[code_index : code_index + 4], byteorder="little")
                        param = int.from_bytes(msg_data[param_index : param_index + 4], byteorder="little")
                        callback_func(callback_parameter, time, code, param)

                    elif event_type == T32_E_ERROR:
                        code = int.from_bytes(msg_data[offset : offset + 4], byteorder="little")
                        message = msg_data[offset + 4 :].decode()
                        callback_func(callback_parameter, code, message)

                if event_type == T32_E_ONEVENT:
                    event_name = msg_data[offset:].decode()
                    event_function = self._eventlist.get(event_name, None)
                    if event_function is not None:
                        event_function(callback_parameter)

            except Exception as e:
                raise ApiNotificationCheckError(event_type) from e

            msg_data = self._link.receive_notify_message()

    def t32_notifystateenable(self, event_code, callback_function):
        """Enables notification at remote server and registers locally callback_function"""

        if event_code > 7:
            raise ApiNotificationEventCountExceedError(event_code)

        event_mask_value = 1 << event_code

        try:
            if event_code == T32_E_EDIT:
                result = self.generic_api_call(rapi_cmd=RAPI_CMD_EDITNOTIFY, opt_arg=0x00, payload=b"\x01\x00")
            else:
                result = self.generic_api_call(
                    rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                    opt_arg=RAPI_DSCMD_STATE_SETNOTIFIER,
                    payload=event_mask_value.from_bytes(2, byteorder="little"),
                )
        except ApiError as e:
            raise ApiNotificationEnableFail() from e
        else:
            self._notification_callback.update({event_code: callback_function})

        return result

    def t32_notifyeventenable(self, event_name, callbackfunction=None):
        """Registers an event notification and corresponding callbackfuntion"""

        if callbackfunction is None:
            has_notification = 1
        else:
            has_notification = 0

        event_name_bytes = event_name.encode()

        payload = struct.pack("<H{}sx".format(len(event_name_bytes)), has_notification, event_name_bytes)

        try:
            result = self.generic_api_call(
                rapi_cmd=RAPI_CMD_DEVICE_SPECIFIC,
                opt_arg=RAPI_DSCMD_EVENT_SETNOTIFIER,
                payload=payload,
            )
        except ApiError as e:
            raise ApiNotificationEventEnableFail() from e
        else:
            if callbackfunction is None:
                self._eventlist.pop(event_name)
            else:
                self._eventlist.update({event_name: callbackfunction})

        return result

    def t32_notificationpending(self):
        return self._link.notificationpending()

    def exit(self):
        self._link.exit()

    t32_exit = exit

    def config(self, some):
        """Setting configuration parameters of remote api"""

        self._link.config(some)

    def raise_error(self, error_code, error_message=None):
        error = error_code_exception_mapping.get(error_code)
        if error is None:
            raise ApiError(error_code, error_message)
        else:
            if error_message is None:
                error_message = error["msg"]

            raise error["exception"](error_message) from None


####### LIBRARY ERROR HANDLING  #######


class T32_ERR_FN1(InternalError):
    pass


class T32_ERR_FN2(InternalError):
    pass


class T32_ERR_FN3(InternalError):
    pass


class T32_ERR_FN4(InternalError):
    pass


class int_code(IntEnum):
    T32_ERR_COM_RECEIVE_FAIL = -1
    T32_ERR_COM_TRANSMIT_FAIL = -2
    T32_ERR_COM_PARA_FAIL = -3
    T32_ERR_COM_SEQ_FAIL = -4
    T32_ERR_NOTIFY_MAX_EVENT = -5
    T32_ERR_MALLOC_FAIL = -6
    T32_ERR_STD_RUNNING = 2
    T32_ERR_STD_NOTRUNNING = 3
    T32_ERR_STD_RESET = 4
    T32_ERR_STD_ACCESSTIMEOUT = 6
    T32_ERR_STD_INVALID = 10
    T32_ERR_STD_REGUNDEF = 14
    T32_ERR_STD_VERIFY = 15
    T32_ERR_STD_BUSERROR = 16
    T32_ERR_STD_NOMEM = 22
    T32_ERR_STD_RESETDETECTED = 48
    T32_ERR_STD_FDXBUFFER = 49
    T32_ERR_STD_RTCKTIMEOUT = 57
    T32_ERR_STD_INVALIDLICENSE = 60
    T32_ERR_STD_CORENOTACTIVE = 64
    T32_ERR_STD_USERSIGNAL = 67
    T32_ERR_STD_NORAPI = 83
    T32_ERR_FN1 = 90
    T32_ERR_FN2 = 91
    T32_ERR_FN3 = 92
    T32_ERR_FN4 = 93
    T32_ERR_STD_FAILED = 113
    T32_ERR_STD_LOCKED = 123
    T32_ERR_STD_POWERFAIL = 128
    T32_ERR_STD_DEBUGPORTFAIL = 140
    T32_ERR_STD_DEBUGPORTTIMEOUT = 144
    T32_ERR_STD_NODEVICE = 147
    T32_ERR_STD_RESETFAIL = 161
    T32_ERR_STD_EMUTIMEOUT = 162
    T32_ERR_STD_NORTCK = 164
    T32_ERR_STD_ATTACH = 254
    T32_ERR_STD_FATAL = 255
    T32_ERR_GETRAM_INTERNAL = 4096
    T32_ERR_READREGBYNAME_NOTFOUND = 4112
    T32_ERR_READREGBYNAME_FAILED = 4113
    T32_ERR_WRITEREGBYNAME_NOTFOUND = 4128
    T32_ERR_WRITEREGBYNAME_FAILED = 4129
    T32_ERR_READREGOBJ_PARAFAIL = 4144
    T32_ERR_READREGOBJ_MAXCORE = 4145
    T32_ERR_READREGOBJ_NOTFOUND = 4146
    T32_ERR_READREGSETOBJ_PARAFAIL = 4147
    T32_ERR_READREGSETOBJ_NUMREGS = 4148
    T32_ERR_WRITEREGOBJ_PARAFAIL = 4160
    T32_ERR_WRITEREGOBJ_MAXCORE = 4161
    T32_ERR_WRITEREGOBJ_NOTFOUND = 4162
    T32_ERR_WRITEREGOBJ_FAILED = 4163
    T32_ERR_SETBP_FAILED = 4176
    T32_ERR_READMEMOBJ_PARAFAIL = 4192
    T32_ERR_WRITEMEMOBJ_PARAFAIL = 4208
    T32_ERR_TRANSFERMEMOBJ_PARAFAIL = 4209
    T32_ERR_TRANSFERMEMOBJ_TRANSFERFAIL = 4210
    T32_ERR_READVAR_ALLOC = 4224
    T32_ERR_READVAR_ACCESS = 4225
    T32_ERR_READBPOBJ_PARAFAIL = 4241
    T32_ERR_READBPOBJ_NOTFOUND = 4242
    T32_ERR_WRITEBPOBJ_FAILED = 4257
    T32_ERR_WRITEBPOBJ_ADDRESS = 4258
    T32_ERR_WRITEBPOBJ_ACTION = 4259
    T32_ERR_MMUTRANSLATION_FAIL = 4272
    T32_ERR_EXECUTECOMMAND_FAIL = 4288
    T32_ERR_EXECUTEFUNCTION_FAIL = 4289


error_code_exception_mapping = {
    int_code.T32_ERR_COM_RECEIVE_FAIL: {
        "name": "T32_ERR_COM_RECEIVE_FAIL",
        "msg": "receiving API response failed",
        "exception": InternalError,
    },
    int_code.T32_ERR_COM_TRANSMIT_FAIL: {
        "name": "T32_ERR_COM_TRANSMIT_FAIL",
        "msg": "sending API message failed",
        "exception": InternalError,
    },
    int_code.T32_ERR_COM_PARA_FAIL: {
        "name": "T32_ERR_COM_PARA_FAIL",
        "msg": "function parameter error",
        "exception": InternalError,
    },
    int_code.T32_ERR_COM_SEQ_FAIL: {
        "name": "T32_ERR_COM_SEQ_FAIL",
        "msg": "message sequence failed",
        "exception": InternalError,
    },
    int_code.T32_ERR_NOTIFY_MAX_EVENT: {
        "name": "T32_ERR_NOTIFY_MAX_EVENT",
        "msg": "max. notify events exceeded",
        "exception": InternalError,
    },
    int_code.T32_ERR_MALLOC_FAIL: {
        "name": "T32_ERR_MALLOC_FAIL",
        "msg": "malloc() failed",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_RUNNING: {
        "name": "T32_ERR_STD_RUNNING",
        "msg": "target running",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_NOTRUNNING: {
        "name": "T32_ERR_STD_NOTRUNNING",
        "msg": "target not running",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_RESET: {
        "name": "T32_ERR_STD_RESET",
        "msg": "target is in reset",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_ACCESSTIMEOUT: {
        "name": "T32_ERR_STD_ACCESSTIMEOUT",
        "msg": "access timeout, target running",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_INVALID: {
        "name": "T32_ERR_STD_INVALID",
        "msg": "not implemented",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_REGUNDEF: {
        "name": "T32_ERR_STD_REGUNDEF",
        "msg": "registerset undefined",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_VERIFY: {
        "name": "T32_ERR_STD_VERIFY",
        "msg": "verify error",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_BUSERROR: {
        "name": "T32_ERR_STD_BUSERROR",
        "msg": "bus error",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_NOMEM: {
        "name": "T32_ERR_STD_NOMEM",
        "msg": "no memory mapped",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_RESETDETECTED: {
        "name": "T32_ERR_STD_RESETDETECTED",
        "msg": "target reset detected",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_FDXBUFFER: {
        "name": "T32_ERR_STD_FDXBUFFER",
        "msg": "FDX buffer error",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_RTCKTIMEOUT: {
        "name": "T32_ERR_STD_RTCKTIMEOUT",
        "msg": "no RTCK detected",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_INVALIDLICENSE: {
        "name": "T32_ERR_STD_INVALIDLICENSE",
        "msg": "no valid license detected",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_CORENOTACTIVE: {
        "name": "T32_ERR_STD_CORENOTACTIVE",
        "msg": "core has no clock/power/reset in SMP",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_USERSIGNAL: {
        "name": "T32_ERR_STD_USERSIGNAL",
        "msg": "user signal",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_NORAPI: {
        "name": "T32_ERR_STD_NORAPI",
        "msg": "tried to connect to emu",
        "exception": InternalError,
    },
    int_code.T32_ERR_FN1: {
        "name": "T32_ERR_FN1",
        "msg": "",
        "exception": T32_ERR_FN1,
    },
    int_code.T32_ERR_FN2: {
        "name": "T32_ERR_FN2",
        "msg": "",
        "exception": T32_ERR_FN2,
    },
    int_code.T32_ERR_FN3: {
        "name": "T32_ERR_FN3",
        "msg": "",
        "exception": T32_ERR_FN3,
    },
    int_code.T32_ERR_FN4: {
        "name": "T32_ERR_FN4",
        "msg": "",
        "exception": T32_ERR_FN4,
    },
    int_code.T32_ERR_STD_FAILED: {
        "name": "T32_ERR_STD_FAILED",
        "msg": "113 std failed",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_LOCKED: {
        "name": "T32_ERR_STD_LOCKED",
        "msg": "access locked",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_POWERFAIL: {
        "name": "T32_ERR_STD_POWERFAIL",
        "msg": "power fail",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_DEBUGPORTFAIL: {
        "name": "T32_ERR_STD_DEBUGPORTFAIL",
        "msg": "debug port fail",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_DEBUGPORTTIMEOUT: {
        "name": "T32_ERR_STD_DEBUGPORTTIMEOUT",
        "msg": "debug port timeout",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_NODEVICE: {
        "name": "T32_ERR_STD_NODEVICE",
        "msg": "no debug device",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_RESETFAIL: {
        "name": "T32_ERR_STD_RESETFAIL",
        "msg": "target reset fail",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_EMUTIMEOUT: {
        "name": "T32_ERR_STD_EMUTIMEOUT",
        "msg": "emulator communication timeout",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_NORTCK: {
        "name": "T32_ERR_STD_NORTCK",
        "msg": "no RTCK on emulator",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_ATTACH: {
        "name": "T32_ERR_STD_ATTACH",
        "msg": "T32_Attach() is missing",
        "exception": InternalError,
    },
    int_code.T32_ERR_STD_FATAL: {
        "name": "T32_ERR_STD_FATAL",
        "msg": "FATAL ERROR 255",
        "exception": InternalError,
    },
    int_code.T32_ERR_GETRAM_INTERNAL: {
        "name": "T32_ERR_GETRAM_INTERNAL",
        "msg": "T32_GetRam failed internally",
        "exception": InternalError,
    },
    int_code.T32_ERR_READREGBYNAME_NOTFOUND: {
        "name": "T32_ERR_READREGBYNAME_NOTFOUND",
        "msg": "T32_ReadRegisterByName: register not found",
        "exception": RegisterNotFoundError,
    },
    int_code.T32_ERR_READREGBYNAME_FAILED: {
        "name": "T32_ERR_READREGBYNAME_FAILED",
        "msg": "T32_ReadRegisterByName: reading register failed",
        "exception": RegisterError,
    },
    int_code.T32_ERR_WRITEREGBYNAME_NOTFOUND: {
        "name": "T32_ERR_WRITEREGBYNAME_NOTFOUND",
        "msg": "T32_WriteRegisterByName: register not found",
        "exception": RegisterNotFoundError,
    },
    int_code.T32_ERR_WRITEREGBYNAME_FAILED: {
        "name": "T32_ERR_WRITEREGBYNAME_FAILED",
        "msg": "T32_WriteRegisterByName: reading register failed",
        "exception": RegisterError,
    },
    int_code.T32_ERR_READREGOBJ_PARAFAIL: {
        "name": "T32_ERR_READREGOBJ_PARAFAIL",
        "msg": "T32_ReadRegisterObj: wrong parameters",
        "exception": RegisterParameterError,
    },
    int_code.T32_ERR_READREGOBJ_MAXCORE: {
        "name": "T32_ERR_READREGOBJ_MAXCORE",
        "msg": "T32_ReadRegisterObj: max cores exceeded",
        "exception": RegisterError,
    },
    int_code.T32_ERR_READREGOBJ_NOTFOUND: {
        "name": "T32_ERR_READREGOBJ_NOTFOUND",
        "msg": "T32_ReadRegisterObj: register not found",
        "exception": RegisterNotFoundError,
    },
    int_code.T32_ERR_READREGSETOBJ_PARAFAIL: {
        "name": "T32_ERR_READREGSETOBJ_PARAFAIL",
        "msg": "T32_ReadRegisterSetObj: wrong parameters",
        "exception": RegisterParameterError,
    },
    int_code.T32_ERR_READREGSETOBJ_NUMREGS: {
        "name": "T32_ERR_READREGSETOBJ_NUMREGS",
        "msg": "T32_ReadRegisterSetObj: number of read registers wrong",
        "exception": RegisterError,
    },
    int_code.T32_ERR_WRITEREGOBJ_PARAFAIL: {
        "name": "T32_ERR_WRITEREGOBJ_PARAFAIL",
        "msg": "T32_WriteRegisterObj: wrong parameters",
        "exception": RegisterParameterError,
    },
    int_code.T32_ERR_WRITEREGOBJ_MAXCORE: {
        "name": "T32_ERR_WRITEREGOBJ_MAXCORE",
        "msg": "T32_WriteRegisterObj: max cores exceeded",
        "exception": RegisterError,
    },
    int_code.T32_ERR_WRITEREGOBJ_NOTFOUND: {
        "name": "T32_ERR_WRITEREGOBJ_NOTFOUND",
        "msg": "T32_WriteRegisterObj: register not found",
        "exception": RegisterNotFoundError,
    },
    int_code.T32_ERR_WRITEREGOBJ_FAILED: {
        "name": "T32_ERR_WRITEREGOBJ_FAILED",
        "msg": "T32_WriteRegisterObj: writing register failed",
        "exception": RegisterError,
    },
    int_code.T32_ERR_SETBP_FAILED: {
        "name": "T32_ERR_SETBP_FAILED",
        "msg": "T32_WriteBreakpoint/T32_WriteBreakpointObj: setting breakpoint failed",
        "exception": BreakpointWriteError,
    },
    int_code.T32_ERR_READMEMOBJ_PARAFAIL: {
        "name": "T32_ERR_READMEMOBJ_PARAFAIL",
        "msg": "T32_ReadMemoryObj: wrong parameters",
        "exception": MemoryError,
    },
    int_code.T32_ERR_WRITEMEMOBJ_PARAFAIL: {
        "name": "T32_ERR_WRITEMEMOBJ_PARAFAIL",
        "msg": "T32_WriteMemoryObj: wrong parameters",
        "exception": MemoryError,
    },
    int_code.T32_ERR_TRANSFERMEMOBJ_PARAFAIL: {
        "name": "T32_ERR_TRANSFERMEMOBJ_PARAFAIL",
        "msg": "T32_TransferMemoryBundleObj: wrong parameters",
        "exception": MemoryError,
    },
    int_code.T32_ERR_TRANSFERMEMOBJ_TRANSFERFAIL: {
        "name": "T32_ERR_TRANSFERMEMOBJ_TRANSFERFAIL",
        "msg": "T32_TransferMemoryBundleObj: transfer failed",
        "exception": MemoryError,
    },
    int_code.T32_ERR_READVAR_ALLOC: {
        "name": "T32_ERR_READVAR_ALLOC",
        "msg": "T32_ReadVariable*: mem alloc failed",
        "exception": VariableError,
    },
    int_code.T32_ERR_READVAR_ACCESS: {
        "name": "T32_ERR_READVAR_ACCESS",
        "msg": "T32_ReadVariable*: access to symbol failed",
        "exception": VariableError,
    },
    int_code.T32_ERR_READBPOBJ_PARAFAIL: {
        "name": "T32_ERR_READBPOBJ_PARAFAIL",
        "msg": "T32_ReadBreakpointObj: wrong parameters",
        "exception": BreakpointParameterError,
    },
    int_code.T32_ERR_READBPOBJ_NOTFOUND: {
        "name": "T32_ERR_READBPOBJ_NOTFOUND",
        "msg": "T32_ReadBreakpointObj: breakpoint not found",
        "exception": BreakpointNotFoundError,
    },
    int_code.T32_ERR_WRITEBPOBJ_FAILED: {
        "name": "T32_ERR_WRITEBPOBJ_FAILED",
        "msg": "T32_WriteBreakpointObj: setting BP failed",
        "exception": BreakpointError,
    },
    int_code.T32_ERR_WRITEBPOBJ_ADDRESS: {
        "name": "T32_ERR_WRITEBPOBJ_ADDRESS",
        "msg": "T32_WriteBreakpointObj: address error",
        "exception": BreakpointAddressError,
    },
    int_code.T32_ERR_WRITEBPOBJ_ACTION: {
        "name": "T32_ERR_WRITEBPOBJ_ACTION",
        "msg": "T32_WriteBreakpointObj: action error",
        "exception": BreakpointActionError,
    },
    int_code.T32_ERR_MMUTRANSLATION_FAIL: {
        "name": "T32_ERR_MMUTRANSLATION_FAIL",
        "msg": "T32_QueryAddressObjMmuTranslation: translation failed",
        "exception": AddressError,
    },
    int_code.T32_ERR_EXECUTECOMMAND_FAIL: {
        "name": "T32_ERR_EXECUTECOMMAND_FAIL",
        "msg": "T32_ExecuteCommand: command failed",
        "exception": CommandError,
    },
    int_code.T32_ERR_EXECUTEFUNCTION_FAIL: {
        "name": "T32_ERR_EXECUTEFUNCTION_FAIL",
        "msg": "T32_ExecuteFunction: function failed",
        "exception": FunctionError,
    },
}
