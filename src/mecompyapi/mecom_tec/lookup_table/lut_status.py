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


class LutServerResponse(Enum):
    """
    Server response to the ?LT query command.
    """
    IDLE = 0
    """
    Idle
    """
    ERASING_OR_WRITING = 1
    """
    Erasing or Writing (Sent Data is ignored)
    """
    NEW_DATA_ACCEPTED = 2
    """
    New Data accepted
    """
    ERROR = 3
    """
    Error
    """
