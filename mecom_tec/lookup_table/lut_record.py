from typing import List


class LutRecord(object):
    """
    Lookup Table Record definition.
    This class represents a bit field struct in C/C++ which consist of,
    an Instruction that takes up 8 bits, a Field1 that takes up 24 bits
    and a Field2 that takes up 32 bits (can be an int or a float).
    """

    def __init__(self):
        # Instruction value
        self.instruction = 0  # type: int
        # First field value
        self._field1 = 0  # type: int
        # First field value split into three bytes
        self._field1b0: int = self.field1 & 0x0000FF
        self._field1b1: int = (self.field1 & 0x00FF00) >> 8
        self._field1b2: int = (self.field1 & 0xFF0000) >> 16
        # Instruction combined with Field1 in a 32-bit int
        self._instruction_and_field_1 = 0  # type: int
        # Second field value is an integer (use Field2Float to store a float)
        self.field2_int = 0  # type: int
        # Second field value is a float (use Field2Int to store an int)
        self.field2_float = 0  # type: float

    @property
    def field1(self):
        return self._field1

    @field1.setter
    def field1(self, new_value):
        self._field1 = new_value
        self._field1b0: int = self.field1 & 0x0000FF
        self._field1b1: int = (self.field1 & 0x00FF00) >> 8
        self._field1b2: int = (self.field1 & 0xFF0000) >> 16

    @property
    def field1b0(self):
        return self._field1b0

    @field1b0.setter
    def field1b0(self, new_value):
        self._field1b0 = new_value
        self._field1 = int(self._field1b0 | self._field1b1 << 8 | self._field1b2 << 16)

    def get_int_array(self) -> List[int]:
        """
        An int array that contains the Instruction (8-bit) combined with
        Field1 (24-bit) in a 32-bit int as well as Field2 in a 32-bit.

        :return: LutG1Record split into two 32-bit int parts.
        :rtype: List[int]
        """
        return [self._instruction_and_field_1, self.field2_int]

    def get_bytes(self) -> bytearray:
        """
        This will return the whole LutG1Record object as a byte array.
        The whole object uses 64-bit, therefore there will be 8 bytes in the array.

        :return: LutG1Record split into byte array.
        :rtype: bytearray
        """
        bytearray_ = bytearray(b"")
        bytearray_.append(self.instruction)
        bytearray_.append(self._field1b0)
        bytearray_.append(self._field1b1)
        bytearray_.append(self._field1b2)
        bytearray_.append(self.field2_int)
        return bytearray_

    def set_bytes(self, buffer: bytearray):
        """
        This method can be used to set all parts of a LutG1Record through the use
        of a byte array in which all parts are individually specified.

        :param buffer: Must be a byte array that contains 8 bytes (64-bit).
        :type buffer: bytearray
        """
        raise NotImplementedError
