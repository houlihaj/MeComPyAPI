###################################################################################################################
# PROPRIETARY AND CONFIDENTIAL
# THIS SOFTWARE IS THE SOLE PROPERTY AND COPYRIGHT (c) 2023 OF ROCKLEY PHOTONICS LTD.
# USE OR REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN AGREEMENT OF ROCKLEY PHOTONICS LTD IS PROHIBITED.
# RPLTD NOTICE VERSION: 1.1.1
###################################################################################################################
from enum import Enum


class LutStatus(Enum):
    """
    Status that the TEC controller returns after downloading a lookup table.
    Can be read by using the Parameter ID 52002.
    """
    NO_INIT = 0  # Not initialized
    """
    No lookup table is stored on the device.
    """
    NOT_VALID = 1  # Table Data not valid
    """
    There is an error in the lookup table on the device.
    """
    ANALYZING = 2  # Analyzing Data Table
    """
    Lookup table is currently being analyzed.
    Can occur while the lookup table is being loaded onto a device.
    """
    READY = 3  # Ready (Data Table OK)
    """
    Everything OK, lookup table can be executed.
    """
    EXECUTING = 4  # Executing...
    """
    Lookup table is currently running/being executed.
    """
    MAX_NUMBER_EXCEEDED = 5  # Max Nr of Tables exceeded
    """
    The maximum amount of tables has been exceeded.
    """
    SUB_NOT_FOUND = 6  # Sub Table not found
    """
    Sub table could not be found.
    """
