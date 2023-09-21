from typing import List
from struct import unpack, pack


CONVERT_TO_HEX_DICT = {0: "0", 1: "1", 2: "2", 3: "3",
                       4: "4", 5: "5", 6: "6", 7: "7",
                       8: "8", 9: "9", 10: "A", 11: "B",
                       12: "C", 13: "D", 14: "E", 15: "F"}


CONVERT_TO_DEC_DICT = {"0": 0, "1": 1, "2": 2, "3": 3,
                       "4": 4, "5": 5, "6": 6, "7": 7,
                       "8": 8, "9": 9, "A": 10, "B": 11,
                       "C": 12, "D": 13, "E": 14, "F": 15}


class MeComVarConvert:
    def __init__(self):
        pass

    def add_base64_url(self, stream, array: List[bytes], length: int) -> None:
        """
        Encodes the byte array base64url and adds it to the stream.

        :param stream: Writes data to this stream.
        :type stream:
        :param array: Data source.
        :type array: List[bytes]
        :param length: Length of data source.
        :type length: int
        :return: None
        """
        raise NotImplementedError

    def add_string(self, stream: str, value: str) -> str:
        """
        Writes a string to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: str
        :return:
        :rtype: str
        """
        stream += value
        return stream

    def add_uint4(self, stream: str, value: int) -> str:
        """
        Writes a UINT4 (byte range 0-15) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return:
        :rtype: str
        """
        stream += "{:01X}".format(value)
        return stream

    def add_int8(self, stream: str, value: int) -> str:
        """
        Writes a INT8 (signed byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return: None
        """
        return self.add_uint8(stream=stream, value=value)

    def add_uint8(self, stream: str, value: int) -> str:
        """
        Writes a UINT8 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return: str
        """
        stream += "{:02X}".format(value)
        return stream

    def add_int16(self, stream: str, value: int) -> str:
        """
        Writes a INT16 (signed byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return:
        :return: str
        """
        return self.add_uint16(stream=stream, value=value)

    def add_uint16(self, stream: str, value: int) -> str:
        """
        Writes a UINT16 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return: str
        """
        stream += "{:04X}".format(value)
        return stream

    def add_int32(self, stream: str, value: int) -> str:
        """
        Writes a INT32 (signed byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return: str
        """
        return self.add_uint32(stream=stream, value=value)

    def add_uint32(self, stream: str, value: int) -> str:
        """
        Writes a UINT32 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return:
        :rtype: str
        """
        stream += "{:08X}".format(value)
        return stream

    def add_int64(self, stream: str, value: int) -> str:
        """
        Writes a INT64 (signed byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return:
        :rtype: str
        """
        return self.add_uint64(stream=stream, value=value)

    def add_uint64(self, stream: str, value: int) -> str:
        """
        Writes a UINT64 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream:
        :param value: Value to be added.
        :type value: int
        :return:
        :rtype: str
        """
        stream += "{:16X}".format(value)
        return stream

    def add_float32(self, stream: str, value: float) -> str:
        """
        Writes a FLOAT32 (.net float) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: float
        :return:
        :rtype: str
        """
        stream += '{:08X}'.format(unpack('<I', pack('<f', value))[0])
        return stream

    def add_double64(self, stream, value: int) -> str:
        """
        Writes a DOUBLE64 (.net double) to the stream.

        :param stream: Writes data to this stream.
        :type stream:
        :param value: Value to be added.
        :type value: int
        :return:
        :rtype: str
        """
        raise NotImplementedError

    def add_encoded_string(self, stream, value) -> None:
        """
        Adds the string to the stream payload. The string is converted to an ASCII char array.
        Then each ASCII char is added as a UINT8 element to the stream. Therefore, the whole ASCII range can be used.
        If a zero terminator is needed, just add it to the string before you run this method.

        :param stream: Writes data to this stream.
        :type stream:
        :param value: Value to be added.
        :type value: int
        :return: None
        """
        raise NotImplementedError

    def add_byte_array(self, stream: str, value: bytearray) -> str:
        """
        Writes each byte in the array to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: bytearray
        :return:
        :rtype: str
        """
        for byte in value:
            stream = self.add_uint8(stream=stream, value=byte)
        return stream

    def convert_to_hex(self, value: int):
        """
        Converts a value from 0 to 15 to a char '0' - 'F'

        :param value: Number value to be converted.
        :type value: int
        :return: char value '0' - 'F' represented by a byte value.
        :rtype: str
        """
        return CONVERT_TO_HEX_DICT[value]

    def read_string(self, stream, length: int) -> str:
        """
        Reads a string with a specified length from the stream.
        The chars are not encoded, therefore only a limited range of chars are allowed.
        Basically 'A-Z', 'a-z', '0-9', '-', ' ',
        For example, carriage return or line feed are not allowed,
        because they would conflict the communication protocol 'control characters'.

        :param stream: Stream where the value is read from.
        :type stream:
        :param length: Length of the read string. To read 20 chars, write 20 to this parameter.
        :type length: int
        :return: The read and converted value.
        :rtype: str
        """
        raise NotImplementedError

    def read_encoded_string(self, stream, read_num_of_elements: int) -> str:
        """
        Reads a 0 terminated string from the stream. Each char is read as UINT8 element.
        Therefore, the full ASCII range is usable.
        Stops writing to the output when 0 is detected.
        Reads always readNrOfElements from the stream.

        :param stream: Stream where the value is read from.
        :type stream:
        :param read_num_of_elements: Number of elements to be read from the stream. In this case 1 element equals 2 bytes.
        :type read_num_of_elements: int
        :return: The read and converted value.
        :rtype: str
        """
        raise NotImplementedError

    def read_uint4(self, stream: str) -> int:
        """
        Reads a UINT4 (byte range 0-15) from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: int
        """
        stream_int = int(stream)
        stream = "{:02X}".format(stream_int)

        rsp_format = "!B"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_uint8(self, stream: str) -> int:
        """
        Reads a UINT8 (byte) from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: int
        """
        rsp_format = "!B"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_int16(self, stream: str) -> str:
        """
        Reads a INT16 from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!h"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_uint16(self, stream: str) -> str:
        """
        Reads a UINT16 from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!H"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_int32(self, stream: str) -> int:
        """
        Reads a INT32 from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: int
        """
        rsp_format = "!i"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_uint32(self, stream: str) -> bytes:
        """
        Reads a UINT32 from the stream.

        :param stream: Stream where the value is read from.
        :type stream:
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!I"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_float32(self, stream) -> float:
        """
        Reads a FLOAT32 (.net float) from the stream.

        :param stream: Stream where the value is read from.
        :type stream:
        :return: The read and converted value.
        :rtype: float
        """
        rsp_format = "!f"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_int64(self, stream) -> bytes:
        """
        Reads a INT64 from the stream.

        :param stream: Stream where the value is read from.
        :type stream:
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!q"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_uint64(self, stream) -> bytes:
        """
        Reads a UINT64 from the stream.

        :param stream: Stream where the value is read from.
        :type stream:
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!Q"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_double64(self, stream) -> bytes:
        """
        Reads a DOUBLE64 (.net double) from the stream.

        :param stream: Stream where the value is read from.
        :type stream:
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!d"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def convert_to_dec(self, hex_value: str):
        """
        Converts a char from '0' - 'F' to a number value 0-15.

        :param hex_value: char value '0' - 'F' represented by a int.
        :type hex_value: str
        :return: Number value 0-15.
        :rtype: int
        """
        return CONVERT_TO_HEX_DICT[hex_value]
