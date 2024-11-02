import logging
import time
from typing import Optional

import ftd2xx

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
        self.ftdi: Optional[ftd2xx.FTD2XX] = None

    def mecom_set_default_settings(self, baudrate: int, timeout: int):
        """
        Initializes the FTDI default settings, so that is it usually running
        with Meerstetter products.

        This function is not part of the IMeComPhy interface.

        :param baudrate: Baud Rate for the Serial Interface.
        :type baudrate: int
        :param timeout: Time in seconds for read timeout. If timeout happens, read returns empty string.
        :type timeout: int
        """
        self.ftdi.setBaudRate(baud=baudrate)
        self.ftdi.setDataCharacteristics(
            wordlen=ftd2xx.ftd2xx.defines.BITS_8,
            stopbits=ftd2xx.ftd2xx.defines.STOP_BITS_1,
            parity=ftd2xx.ftd2xx.defines.PARITY_NONE
        )
        self.ftdi.setFlowControl(flowcontrol=ftd2xx.ftd2xx.defines.FLOW_NONE, xon=0, xoff=0)
        self.ftdi.setTimeouts(read=timeout * 1000, write=timeout * 1000)
        self.ftdi.setLatencyTimer(latency=3)
        # Purges receive and transmit buffer in the device
        self.ftdi.purge(mask=ftd2xx.ftd2xx.defines.PURGE_RX | ftd2xx.ftd2xx.defines.PURGE_TX)

    def connect(
            self, id_str: Optional[str] = None, dev_id: int = 0, baudrate: int = 57_600, timeout: int = 1
    ) -> None:
        """
        Open a handle to an usb device by serial number(default), description or
        location(Windows only) depending on value of flags and return an ftd2xx.FTD2XX
        instance for it.

        :param id_str: ID string from listDevices
        :type id_str: Optional[str]
        :param dev_id:
        :type dev_id: int
        :param baudrate: The baud rate setting.
        :type baudrate: int
        :param timeout: Time in seconds for read timeout. If timeout happens, read returns empty string.
        :type timeout: int
        :return: None
        """
        if id_str is not None:
            id_str_bytes: bytes = id_str.encode()
            self.ftdi: ftd2xx.FTD2XX = ftd2xx.openEx(id_str=id_str_bytes)
        else:
            self.ftdi: ftd2xx.FTD2XX = ftd2xx.open(dev=dev_id)

        self.mecom_set_default_settings(baudrate=baudrate, timeout=timeout)

    def tear(self) -> None:
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.

        :return: None
        """
        # Purges receive and transmit buffer in the device
        self.ftdi.purge(mask=ftd2xx.ftd2xx.defines.PURGE_RX | ftd2xx.ftd2xx.defines.PURGE_TX)
        self.ftdi.close()

    def send_string(self, stream: str) -> None:
        """
        Sends data to the physical interface.

        :param stream: The whole content of the Stream is sent to the physical interface.
        :type stream: str
        :return: None
        """
        # Purges receive and transmit buffer in the device
        self.ftdi.purge(mask=ftd2xx.ftd2xx.defines.PURGE_RX | ftd2xx.ftd2xx.defines.PURGE_TX)

        stream_bytes: bytes = stream.encode()

        self.ftdi.write(data=stream_bytes)

    def get_data_or_timeout(self) -> str:
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
        :return:
        :rtype: str
        """
        # Wait for FTDI receive queue to receive characters from the instrument
        time.sleep(0.1)
        num_bytes_available: int = self.ftdi.getQueueStatus()
        logging.debug(f"num_bytes_available : {num_bytes_available}")
        try:
            to_read: int = 1 if num_bytes_available == 0 else num_bytes_available
            read_bytes: bytes = self.ftdi.read(nchars=to_read)
            logging.debug(f"read_bytes : {read_bytes}")
            if read_bytes == b"":
                raise MeComPhyTimeoutException("The FTDI queue returned an empty byte.")
            response_frame: bytes = read_bytes.rstrip(b"\r")
            logging.debug(f"response_frame : {response_frame}")
            return response_frame.decode()
        except MeComPhyTimeoutException as e:
            raise e
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
