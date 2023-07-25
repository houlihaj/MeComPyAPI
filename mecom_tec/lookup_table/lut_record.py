###################################################################################################################
# PROPRIETARY AND CONFIDENTIAL
# THIS SOFTWARE IS THE SOLE PROPERTY AND COPYRIGHT (c) 2023 OF ROCKLEY PHOTONICS LTD.
# USE OR REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN AGREEMENT OF ROCKLEY PHOTONICS LTD IS PROHIBITED.
# RPLTD NOTICE VERSION: 1.1.1
###################################################################################################################
from typing import List, Optional


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
        # First field value split into three bytes
        self._field1b0 = 0  # type: int
        self._field1b1 = 0  # type: int
        self._field1b2 = 0  # type: int
        # Instruction combined with Field1 in a 32-bit int
        self._instruction_and_field_1 = 0  # type: int
        # Second field value is an integer (use Field2Float to store a float)
        self.field_to_int = 0  # type: int
        # Second field value is a float (use Field2Int to store an int)
        self.field_to_float = 0  # type: float

    class Field1:
        def __init__(self, value: Optional[int] = None,
                     field1b0: Optional[int] = None,
                     field1b1: Optional[int] = None,
                     field1b2: Optional[int] = None):
            self.value = value
            # Convert from bytes to int for field1b0, field1b1, and field1b2
            # Have to know if bytes are in HEX representation
            self.field1b0 = field1b0
            self.field1b1 = field1b1
            self.field1b2 = field1b2

        def get(self):
            # Convert from bytes to int
            # Have to know if bytes are in HEX representation
            return int(self.field1b0 | self.field1b1 << 8 | self.field1b2 << 16)

        def set(self):
            self.field1b0: int = self.value & 0x0000FF
            self.field1b1: int = (self.value & 0x00FF00) >> 8
            self.field1b2: int = (self.value & 0xFF0000) >> 16

    def field_1(self) -> int:
        """
        This represents a 24 bit uint field.
        """
        raise NotImplementedError
    
    def get_int_array(self) -> List[int]:
        """
        An int array that contains the Instruction (8-bit) combined with
        Field1 (24-bit) in a 32-bit int as well as Field2 in a 32-bit.
        
        :return: LutG1Record split into two 32-bit int parts.
        :rtype: List[int]
        """
        return [self._instruction_and_field_1, self.field_to_int]
        # raise NotImplementedError

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
        bytearray_.append(self.field_to_int)
        return bytearray_
    
    def set_bytes(self, buffer: List[bytes]):
        """
        This method can be used to set all parts of a LutG1Record through the use
        of a byte array in which all parts are individually specified.

        :param buffer: Must be a byte array that contains 8 bytes (64-bit).
        :type buffer: List[bytes]
        """
        raise NotImplementedError
    