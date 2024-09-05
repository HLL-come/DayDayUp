import struct

from ._error import SymbolQueryError, SymbolAddressError

from ._address import Address


class Symbol:
    def __init__(self, conn, *, address=None, name=None):
        self.__conn = conn
        self.address = address
        self.name = name
        self.path = None
        self.size = None

    def __str__(self):
        return "{}{} {} {}".format(
            self.__path if self.__path is not None else "",
            self.__name,
            str(self.address),
            self.size,
        )

    @property
    def address(self):
        return self.__address

    @address.setter
    def address(self, address):
        if address is None:
            self.__address = None
        elif isinstance(address, Address):
            self.__address = address
        else:
            raise SymbolAddressError("Invalid address type: {} expects Address object".format(type(address)))

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value):
        self.__path = value

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        self.__size = value

    def query(self):
        """Queries symbol

        Returns:
            Symbol: Result
        """
        recv_buffer = self.__conn.library.t32_querysymbolobj(self)
        return self.deserialize(recv_buffer)

    def serialize(self):

        result = b""

        if self.address is not None:
            result += b"AD"
            addr_params_size, addr_params = self.address.serialize()
            result += addr_params

        if self.name is not None:
            # str_serialize
            len0a = (len(self.name) + 2) & ~1
            result += struct.pack("<2sH{}s".format(len0a), b"NM", len0a, self.name.encode())

        result += b"XX"  # end marker

        return len(result), result

    def deserialize(self, recv_buffer):

        self.address = None
        self.name = None
        self.path = None
        self.size = 0

        read_ptr = 0
        parameter_id_len = 2

        if recv_buffer is None:
            raise ValueError

        while read_ptr < len(recv_buffer):

            parameter_id = recv_buffer[read_ptr : read_ptr + parameter_id_len]
            read_ptr += parameter_id_len

            if parameter_id == b"AD":  # address
                addr_params_size, address = Address.deserialize(self.__conn, recv_buffer[read_ptr:])
                next_read_ptr = read_ptr + addr_params_size
                self.address = address

            elif parameter_id == b"NM":  # name
                field_len = int.from_bytes(recv_buffer[read_ptr : read_ptr + 2], byteorder="little")
                read_ptr += 2

                next_read_ptr = read_ptr + field_len
                # str_deserialize
                name = recv_buffer[read_ptr:next_read_ptr].decode().rstrip("\0")

                self.name = name

            elif parameter_id == b"PT":  # path
                field_len = int.from_bytes(recv_buffer[read_ptr : read_ptr + 2], byteorder="little")
                read_ptr += 2

                next_read_ptr = read_ptr + field_len
                # str_deserialize
                path = recv_buffer[read_ptr:next_read_ptr].decode().rstrip("\0")

                self.path = path

            elif parameter_id == b"SZ":  # size
                next_read_ptr = read_ptr + 8
                self.size = int.from_bytes(recv_buffer[read_ptr:next_read_ptr], byteorder="little")

            elif parameter_id == b"NE":  # name extension
                field_len = int.from_bytes(recv_buffer[read_ptr : read_ptr + 2], byteorder="little")
                read_ptr += 2

                next_read_ptr = read_ptr + field_len
                # str_deserialize
                name_extension = recv_buffer[read_ptr:next_read_ptr].decode().rstrip("\0")

                assert self.name is not None
                self.name += name_extension

            elif parameter_id == b"XX":  # end marker
                break

            else:
                raise ValueError(parameter_id)

            read_ptr = next_read_ptr

        return self


class SymbolService:
    def __init__(self, conn):
        self.__conn = conn

    def __call__(self, *args, **kwargs):
        return Symbol(self.__conn, *args, **kwargs)

    def _symbol_query(self, address=None, name=None) -> Symbol:
        if address is None and name is None:
            raise SymbolQueryError("Either address or name must be set to query, but not both.")
        elif address is not None and name is not None:
            raise SymbolQueryError("Either address or name must be set to query, but not both.")
        sym = Symbol(self.__conn, address=address, name=name)
        if name is not None:
            sym.name = name
        elif address is not None:
            sym.address = address

        return sym.query()

    def query_by_address(self, address) -> Symbol:
        """Search symbol by address.

        Args:
            address (Address): Name with which the symbol is searched.

        Returns:
            Symbol: Result
        """
        return self._symbol_query(address=address)

    def query_by_name(self, name) -> Symbol:
        """Search symbol by name.

        Args:
            name (str): Address at which the symbol is searched.

        Returns:
            Symbol: Result
        """
        return self._symbol_query(name=name)
