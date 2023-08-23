from abc import ABC, abstractmethod


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
    

class IntMeComPhy(ABC):
    """
    The upper communication level uses this interface 
    to have standardized interface to the physical level.
    The physical interface which implements this interface must already be open, 
    before you can use functions of this interface.
    """
    def __init__(self):
        pass

    @abstractmethod
    def send_string(self, stream: str):
        """
        Sends data to the physical interface.

        :param stream: The whole content of the Stream is sent to the physical interface.
        :type stream: str
        """
        raise NotImplementedError

    @abstractmethod
    def get_data_or_timeout(self, stream: str):
        """
        Tries to read data from the physical interface or throws a timeout exception.
        
        Reads the available data in the physical interface buffer and returns immediately. 
        If the receiving buffer is empty, it tries to read at least one byte. 
        It will wait till the timeout occurs if nothing is received.
        Must probably be called several times to receive the whole frame.

        :param stream: Stream where data will be added to.
        :type stream: str
        :raises MeComPhyInterfaceException: Thrown when the underlying physical interface
            is not OK.
        :raises MeComPhyTimeoutException: Thrown when 0 bytes were received during the
            specified timeout time.
        """
        raise NotImplementedError

    @abstractmethod
    def change_speed(self, baudrate: int):
        """
        Used to change the Serial Speed in case of serial communication interfaces.

        :param baudrate:
        :type baudrate: int
        """
        raise NotImplementedError

    @abstractmethod
    def set_timeout(self, milliseconds: int):
        """
        Used to modify the standard timeout of the physical interface.

        :param milliseconds:
        :type milliseconds: int
        """
        raise NotImplementedError
