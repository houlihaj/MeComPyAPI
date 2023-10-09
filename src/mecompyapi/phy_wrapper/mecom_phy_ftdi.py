import ftd2xx
from ftd2xx import FTD2XX

from mecompyapi.phy_wrapper.int_mecom_phy import (
    IntMeComPhy, MeComPhyInterfaceException, MeComPhyTimeoutException
)


class MeComPhyFtdi(IntMeComPhy):
    """
    Implements the IMeComPhy interface for the FTDI chip drivers.
    """
    def __init__(self):
        """
        Implements the IMeComPhy interface for the FTDI chip drivers.        
        """
        super().__init__()
        self.ftdi = None

    def mecom_set_default_settings(self, baudrate: int):
        """
        Initializes the FTDI default settings, so that is it usually running
        with Meerstetter products.

        This function is not part of the IMeComPhy interface.
        
        :param baudrate: Baud Rate for the Serial Interface.
        :type baudrate: int
        """
        raise NotImplementedError

    def connect(self, id_str: str, timeout: int = 1, baudrate: int = 57600) -> None:
        """
        Open a handle to an usb device by serial number(default), description or
        location(Windows only) depending on value of flags and return an FTD2XX
        instance for it.

        :param id_str: ID string from listDevices
        :type id_str: str
        :param timeout: Time in seconds for read timeout. If timeout happens, read returns empty string.
        :type timeout: int
        :param baudrate: The baud rate setting.
        :type baudrate: int
        :raises SerialException:
        :raises InstrumentConnectionError:
        :return: None
        """
        id_str_bytes: bytes = id_str.encode()
        self.ftdi: FTD2XX = ftd2xx.openEx(id_str=id_str_bytes)
        self.ftdi.purge(mask=3)  # purges receive and transmit buffer in the device
        self.ftdi.setTimeouts(read=timeout * 1000, write=timeout * 1000)

    def tear(self):
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.
        """
        self.ftdi.purge(mask=3)  # purges receive and transmit buffer in the device
        self.ftdi.close()

    def send_string(self, stream: str):
        """
        Sends data to the physical interface.

        :param stream: The whole content of the Stream is sent to the physical interface.
        :type stream: str
        """
        self.ftdi.purge(mask=3)  # purges receive and transmit buffer in the device

        stream_bytes = stream.encode()

        self.ftdi.write(data=stream_bytes)

    def get_data_or_timeout(self):
        """
        Tries to read data from the physical interface or throws a timeout exception.

        Reads the available data in the physical interface buffer and returns immediately. 
        If the receiving buffer is empty, it tries to read at least one byte. 
        It will wait till the timeout occurs if nothing is received.
        Must probably be called several times to receive the whole frame.

        :raises MeComPhyInterfaceException: Thrown when the underlying physical interface
            is not OK.
        :raises MeComPhyTimeoutException: Thrown when 0 bytes were received during the
            specified timeout time.
        """
        try:
            # initialize response and carriage return
            cr = "\r".encode()
            response_frame = b''
            response_byte = self.ftdi.read(nchars=1)  # read one byte at a time, timeout is set on instance level

            # read until stop byte
            while response_byte != cr:
                response_frame += response_byte
                response_byte = self.ftdi.read(nchars=1)

            return response_frame.decode()

        except Exception as e:
            raise MeComPhyInterfaceException(f"Failure during receiving: {e}")

    def change_speed(self, baudrate: int):
        """
        Used to change the Serial Speed in case of serial communication interfaces.

        :param baudrate: Baud Rate for the Serial Interface.
        :type baudrate: int
        """
        raise NotImplementedError

    def set_timeout(self, milliseconds: int):
        """
        Used to modify the standard timeout of the physical interface.

        :param milliseconds:
        :type milliseconds: int
        """
        raise NotImplementedError
