import argparse
import collections
import decimal
import enum
import logging
import re
import struct
import sys
import threading
import time
import typing
import uuid
import warnings

from .__version__ import __version__
from ._rc._address import Address, AddressService
from ._rc._breakpoint import Breakpoint, BreakpointService
from ._rc._command import CommandError, CommandService
from ._rc._directaccess import DirectAccessService
from ._rc._error import *
from ._rc._functions import FunctionError, FunctionService
from ._rc._library import Library
from ._rc._memory import *
from ._rc._practice import PracticeError, PracticeMacro, PracticeService
from ._rc._register import Register, RegisterService
from ._rc._symbol import Symbol, SymbolService
from ._rc._variable import Variable, VariableError, VariableService

VERSION = __version__
REVISION = ""
BUILD = ""

MIN_BASE_POWERVIEW = 125398
MIN_BUILD_POWERVIEW = 126615


__DEFAULT_NODE = "localhost"
__DEFAULT_PORT = "20000"
__DEFAULT_PROTOCOL = "TCP"
__DEFAULT_TIMEOUT = 60.0
__DEFAULT_PACKLEN = 1024  # required only for UDP

logger = logging.getLogger("lauterbach.trace32.rcl")


def hexversion():
    """The module version as a 32-bit integer.

    See also: https://docs.python.org/3/library/sys.html#sys.hexversion
    See also: https://docs.python.org/3/c-api/apiabiversion.html#apiabiversion

    Returns:
        int: The module version as a 32-bit integer.
    """
    re_version_match = re.match(
        r"^(?P<major_version>\d+)\."
        r"(?P<minor_version>\d+)\."
        r"(?P<micro_version>\d+)"
        r"(?:(?P<release_level>a|b|rc)(?P<release_serial>\d+))?"
        r"(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$",
        VERSION,
    )
    if re_version_match.groupdict()["release_level"] is None:
        return (
            (int(re_version_match.groupdict()["major_version"]) << 24)
            | (int(re_version_match.groupdict()["minor_version"]) << 16)
            | (int(re_version_match.groupdict()["micro_version"]) << 8)
            | (0xF << 4)
        )
    else:
        release_level = {None: 0xF, "a": 0xA, "b": 0xB, "rc": 0xC}
        return (
            (int(re_version_match.groupdict()["major_version"]) << 24)
            | (int(re_version_match.groupdict()["minor_version"]) << 16)
            | (int(re_version_match.groupdict()["micro_version"]) << 8)
            | (release_level[re_version_match.groupdict()["release_level"]] << 4)
            | int(re_version_match.groupdict()["release_serial"])
        )


def init(**kwargs):
    warnings.warn("init() is deprecated and will be removed in future versions", category=DeprecationWarning)


class __TeeOut(object):
    def __init__(self, pipe, stream, encoding):
        self.stream = stream
        self.pipe = pipe
        self.encoding = encoding

    def __getattr__(self, attr_name):
        return getattr(self.stream, attr_name)

    def write(self, data):
        self.pipe.write(data.encode(self.encoding))
        self.pipe.flush()

    def flush(self):
        self.stream.flush()


class __TeeIn(object):
    def __init__(self, pipe, stream, encoding):
        self.stream = stream
        self.pipe = pipe
        self.encoding = encoding

    def __getattr__(self, attr_name):
        # print ("getattr!",attr_name)
        sys.stdout.flush()
        a = getattr(self.pipe, attr_name)
        # print(a)
        return a

    def read(self, data):
        print("Read!")
        sys.stdout.flush()
        return self.pipe.read(data)

    def readline(self):
        buf = ""  # storage buffer
        handle = self.pipe
        chunk_size = 1
        line_separator = "\r"
        while not handle.closed:  # while our handle is open
            data = handle.read(chunk_size)  # read `chunk_size` sized data from the passed handle
            sys.stdout.write(data.decode(self.encoding))
            buf += data.decode(self.encoding)  # add the collected data to the internal buffer
            if line_separator in buf:  # we've encountered a separator
                sys.stdout.write("\n")
                chunks = buf.split(line_separator)
                buf = chunks.pop()  # keep the last entry in our buffer
                for chunk in chunks:  # yield the rest
                    return chunk
        if buf:
            return buf  # return the last buffer if any

    def flush(self):
        self.con.flush()


def autoconnect():
    """Command-line friendly version of connect().

    Uses argparse to parse sys.argv and then calls connect(<args>).

    Returns:
        Debugger: debugger
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", default=__DEFAULT_NODE, help="Remote API node.")
    parser.add_argument("--packlen", default=__DEFAULT_PACKLEN, help="Remote API packet length.")
    parser.add_argument("--port", default=__DEFAULT_PORT, help="Remote API port.")
    parser.add_argument(
        "--protocol", type=str, choices=("UDP", "TCP"), default=__DEFAULT_PROTOCOL, help="Remote API protocol."
    )
    parser.add_argument("--pipe_in", help="Input redirection pipe name.")
    parser.add_argument("--pipe_out", help="Output redirection pipe name.")
    args = parser.parse_args()

    try:
        pipe_enc = "mbcs"
        "Hello!".encode(pipe_enc)
    except LookupError:
        pipe_enc = "ascii"

    if args.pipe_in is not None:
        input_pipe = open(args.pipe_in, "rb")
        sys.stdin = __TeeIn(input_pipe, sys.stdin, encoding=pipe_enc)

    if args.pipe_out is not None:
        output_pipe = open(args.pipe_out, "wb")
        sys.stdout = __TeeOut(output_pipe, sys.stdout, encoding=pipe_enc)
        sys.stderr = __TeeOut(output_pipe, sys.stderr, encoding=pipe_enc)

    return connect(node=args.node, packlen=args.packlen, port=args.port, protocol=args.protocol)


def connect(
    *,
    node=__DEFAULT_NODE,
    packlen=__DEFAULT_PACKLEN,
    port=__DEFAULT_PORT,
    protocol=__DEFAULT_PROTOCOL,
    timeout=__DEFAULT_TIMEOUT
):
    """Connect to a debugger.

    Args:
        node (str): Remote API node. Defaults to 'localhost'.
        port (:obj:`int`): Remote API port. Defaults to 20000.
        packlen (:obj:`int`): Remote API packet length. Defaults to 1024 for UDP and 16384 for TCP.
        protocol (:obj:`str`): Remote API protocol type: TCP, UDP. Defaults to "TCP".
        timeout (:obj:`float`): Connection establishment timeout in seconds. Defaults to 4.0.

    Return:
        Debugger: debugger
    """

    return Debugger(node=node, port=port, packlen=packlen, protocol=protocol, timeout=timeout)


class Debugger:
    """Connect to a debugger.

    Args:
        node (str): Remote API node. Defaults to 'localhost'.
        port (:obj:`int`): Remote API port. Defaults to 20000.
        packlen (:obj:`int`): Remote API packet length. Defaults to 1024.
        protocol (:obj:`str`): Remote API protocol type: TCP, UDP. Defaults to "TCP".
        timeout (:obj:`float`): Connection establishment timeout in seconds. Defaults to 10.0.

    Attributes:
        address (AddressService): :py:attr:`AddressService<lauterbach.trace32.rcl.connect.AddressService>` for this debugger.
        breakpoint (BreakpointService): :py:attr:`BreakpointService<lauterbach.trace32.rcl.connect.BreakpointService>` for this debugger.
        cmd (CommandService): :py:attr:`CommandService<lauterbach.trace32.rcl.connect.CommandService>` for this debugger.
        fnc (FunctionService): :py:attr:`FunctionService<lauterbach.trace32.rcl.connect.FunctionService>` for this debugger.
        memory (MemoryService): :py:attr:`MemoryService<lauterbach.trace32.rcl.connect.MemoryService>` for this debugger.
        practice (PracticeService): :py:attr:`PracticeService<lauterbach.trace32.rcl.connect.PracticeService>` for this debugger.
        register (RegisterService): :py:attr:`RegisterService<lauterbach.trace32.rcl.connect.RegisterService>` for this debugger.
        symbol (SymbolService): :py:attr:`SymbolService<lauterbach.trace32.rcl.connect.SymbolService>` for this debugger.
        variable (VariableService): :py:attr:`VariableService<lauterbach.trace32.rcl.connect.VariableService>` for this debugger.
    """

    def __init__(self, *, node, port, packlen, protocol, timeout):
        self.__library = Library(self, node=node, port=port, packlen=packlen, protocol=protocol, timeout=timeout)

        self.address = AddressService(self)
        self.breakpoint = BreakpointService(self)
        self.cmd = CommandService(self)
        self.fnc = FunctionService(self)
        self.memory = MemoryService(self)
        self.practice = PracticeService(self)
        self.register = RegisterService(self)
        self.symbol = SymbolService(self)
        self.variable = VariableService(self)
        # added in v1.1
        self.directaccess = DirectAccessService(self)

        self.connect()
        self.check_powerview_version()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        self.__library.t32_init()
        try:
            self.__library.t32_attach(1)
        except ApiConnectionTimeoutError:
            self.__library.t32_exit()
            self.__library.t32_init()
            self.__library.t32_attach(1)

    def check_powerview_version(self):
        # Check version of TRACE32 software:
        self._powerview_software_build = self.fnc.software_build()
        self._powerview_software_build_base = self.fnc.software_build_base()

        if (
            self._powerview_software_build_base < MIN_BASE_POWERVIEW
            or self._powerview_software_build < MIN_BUILD_POWERVIEW
        ):
            raise ApiVersionError(
                "Minimum required software version: {min_build}:{min_base}, current version {curr_build}:{curr_base} (build:base)".format(
                    min_build=MIN_BUILD_POWERVIEW,
                    min_base=MIN_BASE_POWERVIEW,
                    curr_build=self._powerview_software_build,
                    curr_base=self._powerview_software_build_base,
                )
            )

        # Have rcl client version checked by TRACE32:
        version_result = self.fnc("VERSION.PYRCL({})".format(VERSION))

        # if not version_result == "OK":
        #     raise ApiVersionError(version_result) from None

    def disconnect(self):
        """Disconnect from PowerView."""
        self.__library.t32_exit()

    @property
    def library(self):
        return self.__library

    def _cmd(self, cmd: str):
        """Only for internal use! Use 'cmd' without leading underscores instead!"""
        logger.debug(cmd)
        try:
            self.__library.t32_executecommand(cmd.encode(), 4096)
        except CommandError as e:
            raise e.with_traceback(e.__traceback__) from None

    def _fnc(self, fnc: str):
        """Only for internal use! Use 'fnc' without leading underscores instead!"""
        logger.debug(fnc)
        try:
            result_value, result_type = self.__library.t32_executefunction(fnc)
        except FunctionError as e:
            raise e.with_traceback(e.__traceback__) from None
        return self._decode_eval_result(result_type, result_value)

    @staticmethod
    def _decode_eval_result(result_type, result_value):
        if result_type == 0x0000:  # error
            return str(result_value)
        elif result_type == 0x0001:  # bool
            if result_value == "FALSE()":
                return False
            elif result_value == "TRUE()":
                return True
            else:
                raise FunctionError(result_value)
        elif result_type == 0x0002:  # binary
            return int(result_value[2:], 2)
        elif result_type == 0x0004:  # hex
            return int(result_value, 16)
        elif result_type == 0x0008:  # decimal
            return int(result_value[:-1])
        elif result_type == 0x0010:  # float
            return float(result_value)
        elif result_type == 0x0020:  # TODO ascii constant
            return str(result_value)
        elif result_type == 0x0040:  # string
            return str(result_value)
        elif result_type == 0x0080:  # TODO numeric range
            return str(result_value)
        elif result_type == 0x0100:  # TODO address
            return str(result_value)
        elif result_type == 0x0200:  # TODO address range
            return str(result_value)
        elif result_type == 0x0400:  # time
            return float(result_value[:-1])
        elif result_type == 0x0800:  # time range
            return [float(tv[:-1]) for tv in result_value.split("--")]
        elif result_type == 0x4000:  # TODO bitmask
            return str(result_value)
        elif result_type == 0x8000:  # empty
            return None
        return None

    def print(self, string):
        self.cmd('ECHO "{}"'.format(string))

    def ping(self):
        self.__library.t32_ping()

    def cmm(self, cmd: str, *, timeout: float = None):
        """Executes PRACTICE CMM script, blocking.

        Args:
            cmd (str): Script path and name.
            timeout (float, optional, default=0): Timeout in seconds.
                Special values:
                - None: Wait indefinitely.
                - 0: Don't poll for script to finish (non-blocking)

        Raises:
            PracticeError: If script execution took longer than timeout.
        """

        stack_depth_pre = self.fnc("PRACTICE.SD()")
        start_time = time.perf_counter()
        try:
            self.cmd("DO {}".format(cmd))
        except CommandError as e:
            raise PracticeError(str(e)) from None
        if timeout is None or timeout > 0:
            while True:
                stack_depth = self.fnc("PRACTICE.SD()")
                if stack_depth < stack_depth_pre:
                    raise PracticeError("Practice stack depth error")
                elif stack_depth == stack_depth_pre:
                    break
                if timeout is not None:
                    if time.perf_counter() - start_time > timeout:
                        raise TimeoutError()
                time.sleep(0.01)

    def _t32_stop(self):
        self.__library.t32_stop()

    def _t32_eval_get(self):
        evaluation_result = self.__library.t32_evalget()
        return evaluation_result

    def _t32_eval_get_string(self):
        evaluation_string = self.__library.t32_evalgetstring()
        return evaluation_string

    def _get_practice_state(self):
        practice_state = self.__library.t32_getpracticestate()
        return practice_state

    def _get_window_content(self, command: str, requested: int, offset: int, print_code: str) -> bytes:
        PRINT_CODES = {
            "ASCII": 0x41,
            "ASCIIP": 0x42,
            "ASCIIE": 0x43,
            "CSV": 0x44,
            "XML": 0x45,
        }
        try:
            print_code_int = PRINT_CODES[print_code]
        except KeyError:
            raise WindowError(
                'Invalid print_code: "{}". Valid print_codes: "{}"'.format(print_code, '", "'.join(PRINT_CODES.keys()))
            ) from None
        return self.__library.t32_getwindowcontent(command.encode(), requested, offset, print_code_int)

    def get_message(self):
        # execute
        message_text, message_type = self.__library.t32_getmessage()
        return collections.namedtuple("message", ["text", "type"])(message_text, message_type)

    def step(self):
        self.__library.t32_step()

    def step_asm(self):
        self.__library.t32_stepmode(0)

    def step_hll(self):
        self.__library.t32_stepmode(1)

    def step_over(self):
        self.cmd("Step.Over")

    def go(self):
        self.__library.t32_go()

    def go_up(self):
        self.cmd("Go.Up")

    def go_return(self):
        self.cmd("Go.Return")

    def break_(self):
        self.__library.t32_break()

    def get_state(self):
        return self.library.t32_getstate()

    # def window_open(self, window: Window):
    #     """
    #     see Window.open()
    #     """
    #     return window.open(self)
    #
    # def window_close(self, window: Window):
    #     """
    #     see Window.close()
    #     """
    #     return window.close(self)
    #
    # def window_query(self, window: Window):
    #     """
    #     see Window.query()
    #     """
    #     return window.query(self)
    #
    # def window_update(self, window: Window):
    #     """
    #     see Window.update()
    #     """
    #     return window.update(self)

    def t32_exp(self, cmd, data):
        return self.__library.t32_exp(cmd, data)

    def t32_exp_deprecated(self, cmd, data):
        result = self.__library.t32_exp_deprecated(cmd, data)
        return result.payload


class Window:
    """
    Helper class for opening, position, sizing, closing, ... TRACE32 windows.

    TODO WinPage support
    """

    def __init__(
        self,
        window,
        left: decimal.Decimal = None,
        up: decimal.Decimal = None,
        hsize: int = None,
        vsize: int = None,
        hscale: int = None,
        vscale: int = None,
        name=None,
        state=None,
        header=None,
    ):
        """
        Creates a window object.

        :param window: Window, e.g. "Data.dump /SpotLight"
        :param left: x-coordinate
        :param up: y-coordinate
        :param hsize: width
        :param vsize: height
        :param hscale: width of the scale area
        :param vscale: height of the scale area
        :param name: user-defined identifier for the window
        :param state: TODO not implemented
        :param header: TODO not implemented
        """
        self.__window = window
        self.__left = left  # TODO convert to decimal.Decimal?
        self.__up = up  # TODO convert to decimal.Decimal?
        self.__hsize = hsize
        self.__vsize = vsize
        self.__hscale = hscale
        self.__vscale = vscale
        self.__name = name if name is not None else uuid.uuid4()
        if state is not None:
            raise NotImplementedError('parameter "state" is not yet implemented')
        if header is not None:
            raise NotImplementedError('parameter "header" is not yet implemented')

    @staticmethod
    def __int_to_str(value: typing.Union[None, int, str]) -> str:
        """
        Converts int values to a TRACE32 compatible str (leading dot). None is converted to '', str arguments are returned unchanged.

        :param value:
        :return:
        """
        return "" if value is None else value if isinstance(value, str) else "{}.".format(value)

    @staticmethod
    def __decimal_to_str(value: typing.Union[None, decimal.Decimal, str]) -> str:
        """
        Converts decimal.Decimal values to a TRACE32 compatible str (leading dot). None is converted to '', str arguments are returned unchanged.

        :param value:
        :return:
        """
        return "" if value is None else value if isinstance(value, str) else "{:f}".format(value)

    def __exists(self, connection):
        """
        Checks whether a window with the same name already exists.

        :param connection:
        :return:
        """
        return False if connection.f.window_exist(self.__name) == 0 else True

    def open(self, connection):
        """
        Opens the window (window-name == uuid).

        Before opening the window checks whether a window with the same window-name already exists, and if yes raises a WindowError.
        :param connection:
        :return:
        """
        if self.__exists(connection) is True:
            raise WindowError("{} already exists".format(self.__name))
        connection.cmd(
            "WinPOS {left},{up},{hsize},{vsize},{hscale},{vscale},{name}".format(
                left=self.__decimal_to_str(self.__left),
                up=self.__decimal_to_str(self.__up),
                hsize=self.__int_to_str(self.__hsize),
                vsize=self.__int_to_str(self.__vsize),
                hscale=self.__int_to_str(self.__hscale),
                vscale=self.__int_to_str(self.__vscale),
                name=self.__name,
            )
        )
        connection.cmd("{}".format(self.__window))

    def close(self, connection):
        """
        Closes the window (window-name == uuid).

        Before closing the window checks whether a window with the same window-name exists, and if no raises a WindowError.
        :param connection:
        :return:
        """
        if self.__exists(connection) is False:
            raise WindowError("{} not found".format(self.__name))
        connection.cmd("WinCLEAR {}".format(uid=self.__name))

    def query(self, connection):
        """
        Queries the window parameter.

        Before querying the window checks whether a window with the same window-name exists, and if no raises a WindowError.
        :param connection:
        :return:
        """
        if self.__exists(connection) is False:
            raise WindowError("{} not found".format(self.__name))

        query_f = "WINdow.POSition({},LEFT)".format(self.__name)
        result_value, result_type = connection.library.t32_executefunction(query_f)
        self.__left = decimal.Decimal(result_value)

        query_f = "WINdow.POSition({},UP)".format(self.__name)
        result_value, result_type = connection.library.t32_executefunction(query_f)
        self.__up = decimal.Decimal(result_value)

        query_f = "WINdow.POSition({},HSIZE)".format(self.__name)
        result_value, result_type = connection.library.t32_executefunction(query_f)
        self.__hsize = int(decimal.Decimal(result_value))

        query_f = "WINdow.POSition({},VSIZE)".format(self.__name)
        result_value, result_type = connection.library.t32_executefunction(query_f)
        self.__vsize = int(decimal.Decimal(result_value))

        query_f = "WINdow.POSition({},HSCALE)".format(self.__name)
        result_value, result_type = connection.library.t32_executefunction(query_f)
        self.__hscale = int(decimal.Decimal(result_value))

        query_f = "WINdow.POSition({},VSCALE)".format(self.__name)
        result_value, result_type = connection.library.t32_executefunction(query_f)
        self.__vscale = int(decimal.Decimal(result_value))

    def update(self, connection):
        """
        Updates the window parameter (only size at the moment).

        Before updating the window checks whether a window with the same window-name exists, and if no raises a WindowError.
        :param connection:
        :return:
        """
        if self.__exists(connection) is False:
            raise WindowError("{} not found".format(self.__name))
        if self.__hsize is not None and self.__vsize is not None:
            connection.cmd(
                "WinRESIZE {hsize},{vsize},{name}".format(
                    hsize=self.__int_to_str(self.__hsize),
                    vsize=self.__int_to_str(self.__vsize),
                    name=self.__name,
                )
            )

    @property
    def height(self):
        return self.__vsize

    @height.setter
    def height(self, value):
        self.__vsize = value

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, value):
        self.__hsize = value


if __name__ == "__main__":
    pass
