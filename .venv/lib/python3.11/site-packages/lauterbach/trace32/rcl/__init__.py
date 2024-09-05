from .__version__ import __version__  # noqa: F401
from ._rc import *
from ._rc._address import Address, AddressService
from ._rc._breakpoint import Breakpoint, BreakpointService
from ._rc._command import CommandError, CommandService
from ._rc._directaccess import (
    DirectAccessBundle,
    DirectAccessService,
    DirectAccessShiftRaw,
    DirectAccessShiftRawOptions,
    DirectAccessShiftRawResult,
)
from ._rc._error import *
from ._rc._functions import FunctionError, FunctionService
from ._rc._memory import MemoryService
from ._rc._memory_bundle import (
    MemoryAccessBundle,
    MemoryAccessError,
    MemoryAccessResult,
)
from ._rc._practice import PracticeError, PracticeMacro, PracticeService
from ._rc._register import Register, RegisterService
from ._rc._symbol import Symbol, SymbolService
from ._rc._variable import Variable, VariableError, VariableService

# We don't export bare functions in __all__ to not pollute the caller's
# namespace in case they use star imports.
#
# This applies to: autoconnect, connect, init
#
# To use these bare functions either import them like so (recommended):
#     import lauterbach.trace32.rcl as t32
#     def main():
#         t32.init()
# Or:
#     from lauterbach.trace32.rcl import init
#     def main():
#         init()
# Using star imports (from ... import *) will not provide these!
from .rcl import VERSION as VERSION  # noqa
from .rcl import Debugger
from .rcl import autoconnect as autoconnect  # noqa
from .rcl import connect as connect  # noqa
from .rcl import hexversion as hexversion  # noqa
from .rcl import init as init  # noqa

__all__ = [
    # RCL
    "Debugger",
    # Address
    "Address",
    "AddressService",
    # Breakpoint
    "Breakpoint",
    "BreakpointService",
    # Command
    "CommandError",
    "CommandService",
    # Error
    "BaseError",
    "InternalError",
    # Function
    "FunctionError",
    "FunctionService",
    # Memory
    "MemoryService",
    "MemoryAccessBundle",
    # Practice
    "PracticeError",
    "PracticeMacro",
    "PracticeService",
    # Register
    "Register",
    "RegisterService",
    # Symbol
    "Symbol",
    "SymbolService",
    # Variable
    "Variable",
    "VariableError",
    "VariableService",
]
