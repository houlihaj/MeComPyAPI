class LutException(Exception):
    """
    Is used when a lookup table command to the device fails.
    Check the inner exception for details.
    """
    def __init__(self, message):
        super().__init__(message)
