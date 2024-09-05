class BaseError(Exception):
    pass


class InternalError(BaseError):
    pass


"""API Errors"""


class ApiError(BaseError):
    pass


class ApiVersionError(ApiError):
    pass


class ApiPortError(ApiError):
    pass


class ApiHeaderError(ApiError):
    pass


class ApiProtocolError(ApiError):
    pass


class ApiProtocolTransmitError(ApiProtocolError):
    pass


class ApiNotificationError(ApiError):
    pass


class ApiNotificationEnableFail(ApiNotificationError):
    pass


class ApiNotificationEventEnableFail(ApiNotificationError):
    pass


class ApiNotificationCheckError(ApiNotificationError):
    def __init__(self, event_code):
        super().__init__("Error during callback handling: Event {}".format(event_code))


class ApiNotificationEventCountExceedError(ApiNotificationError):
    def __init__(self, event_code):
        super().__init__("Event Code too high (max = 7): {}".format(event_code))


"""Api Connection Error"""


class ApiConnectionError(ApiError, ConnectionError):
    pass


class ApiConnectionTimeoutError(ApiConnectionError):
    pass


class ApiConnectionReceiveError(ApiConnectionError):
    pass


class ApiConnectionTransmitError(ApiConnectionError):
    pass


class ApiConnectionSyncError(ApiConnectionError):
    pass


class ApiConnectionConfigError(ApiConnectionError):
    pass


class ApiConnectionInitError(ApiConnectionError):
    pass


class WindowError(BaseError):
    pass


"""Address Errors"""


class AddressError(BaseError):
    pass


class AddressValueError(AddressError):
    pass


class AddressParameterError(AddressError):
    pass


"""Breakpoint Errors"""


class BreakpointError(BaseError):
    pass


class BreakpointWriteError(BreakpointError):
    pass


class BreakpointAddressError(BreakpointError):
    pass


class BreakpointActionError(BreakpointError):
    pass


class BreakpointParameterError(BreakpointError):
    pass


class BreakpointNotFoundError(BreakpointError):
    pass


"""Register Errors"""


class RegisterError(BaseError):
    pass


class RegisterWriteError(RegisterError):
    pass


class RegisterValueError(RegisterError):
    pass


class RegisterParameterError(RegisterError):
    pass


class RegisterNotFoundError(RegisterError):
    pass


"""Symbol Errors"""


class SymbolError(BaseError):
    pass


class SymbolQueryError(SymbolError):
    pass


class SymbolAddressError(SymbolError):
    pass
