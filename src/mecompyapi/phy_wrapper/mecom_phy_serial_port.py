from serial import Serial, SerialException, SerialTimeoutException

from mecompyapi.phy_wrapper.int_mecom_phy import (
    IntMeComPhy, MeComPhyInterfaceException, MeComPhyTimeoutException
)


class InstrumentException(Exception):
    def __init__(self, message):
        super().__init__(message)


class InstrumentConnectionError(InstrumentException):
    pass


class ResponseException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ResponseTimeout(ResponseException):
    pass


class MeComPhySerialPort(IntMeComPhy):
    def __init__(self):
        """
        Implements the IMeComPhy interface for the Serial Port interface.
        """
        super().__init__()
        self.ser = Serial()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ser.__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self):
        return self

    def open_with_default_settings(self, port_name: str, baud_rate):
        """
        Opens the SerialPort with the standard settings used to communicate with ME devices.

        :param port_name:
        :type port_name: str
        :param baud_rate:
        :type baud_rate: int
        """
        raise NotImplementedError

    def connect(self, port_name: str, timeout: int = 1, baudrate: int = 57600):
        """
        Connects to a serial port. On Windows, these are typically 'COMX' where X is the number of the port. In Linux,
        they are often /dev/ttyXXXY where XXX usually indicates if it is a serial or USB port, and Y indicates the
        number. E.g. /dev/ttyUSB0 on Linux and 'COM7' on Windows

        :param port_name: Port, as described in description
        :type port_name: str
        :param timeout: Time in seconds for read timeout. If timeout happens, read returns empty string.
        :type timeout: int
        :param baudrate: The baud rate setting.
        :type baudrate: int
        :raises SerialException:
        :raises InstrumentConnectionError:
        """
        self.ser.port = port_name
        self.ser.timeout = timeout
        self.ser.write_timeout = timeout
        self.ser.baudrate = baudrate
        if self.ser.is_open is False:
            try:
                self.ser.open()
            except SerialException as e:
                raise e
        else:
            raise InstrumentConnectionError("Serial device is already open!")

    def tear(self):
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.
        """
        self.ser.flush()
        self.ser.close()

    def _read(self, size):
        """
        Read n=size bytes from serial, if <n bytes are received (serial.read() return because of timeout),
        raise a timeout.
        """
        recv = self.ser.read(size=size)
        if len(recv) < size:
            raise ResponseTimeout("timeout because serial read returned less bytes than expected")
        else:
            return recv

    def send_string(self, stream: str):
        """
        Sends data to the physical interface.

        :param stream: The whole content of the Stream is sent to the physical interface.
        :type stream: str
        """
        # clear buffers
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()

        stream_bytes = stream.encode()

        # send query
        self.ser.write(stream_bytes)

        # flush write cache
        self.ser.flush()

    def get_data_or_timeout(self, stream: str) -> str:
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
        :return:
        :rtype: str
        """
        try:
            # initialize response and carriage return
            cr = "\r".encode()
            response_frame = b''
            response_byte = self._read(size=1)  # read one byte at a time, timeout is set on instance level

            # read until stop byte
            while response_byte != cr:
                response_frame += response_byte
                response_byte = self._read(size=1)

            return response_frame.decode()

        except SerialTimeoutException as e:
            raise MeComPhyTimeoutException(e)

        except Exception as e:
            raise MeComPhyInterfaceException(f"Failure during receiving: {e}")

    def change_speed(self, baudrate: int):
        """
        Used to change the Serial Speed in case of serial communication interfaces.

        :param baudrate:
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
