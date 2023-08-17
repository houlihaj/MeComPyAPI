class MeComPhyTimeoutException(Exception):
    """
    Represents timeout errors occur during data reception.
    
    Initializes a new instance of the Exception class with a specified error message.
    """
    def __init__(self, message):
        super().__init__(message)


class MeComPhyInterfaceException(Exception):
    """
    Represents general physical interface errors.

    Initializes a new instance of the Exception class with a specified error message.
    """
    def __init__(self, message):
        super().__init__(message)
    

class IntMeComPhy:
    """
    Sends data to the physical interface.
    """
    def __init__(self):
        pass
    
    def send_string(self, stream):
        """
        Sends data to the physical interface.

        :param stream: The whole content of the Stream is sent to the physical interface.
        :type stream:
        """
        raise NotImplementedError

    def get_data_or_timeout(self):
        """
        Tries to read data from the physical interface or throws a timeout exception.
        
        Reads the available data in the physical interface buffer and returns immediately. 
        If the receiving buffer is empty, it tries to read at least one byte. 
        It will wait till the timeout occurs if nothing is received.
        Must probably be called several times to receive the whole frame.
        """
        raise NotImplementedError
    
    def change_speed(self):
        """
        Used to change the Serial Speed in case of serial communication interfaces.
        """
        raise NotImplementedError
    
    def set_timeout(self):
        """
        Used to modify the standard timeout of the physical interface.
        """
        raise NotImplementedError
