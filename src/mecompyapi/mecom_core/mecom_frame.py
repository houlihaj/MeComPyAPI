from enum import Enum
from typing import Optional
from dataclasses import dataclass

from PyCRC.CRCCCITT import CRCCCITT

from mecompyapi.mecom_core.mecom_var_convert import MeComVarConvert
from mecompyapi.phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort


class WrongChecksumException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ERcvType(Enum):
    """
    EMPTY = 0; ACK = 1; DATA = 2
    """
    EMPTY = 0
    """
    No package has been received. 
    The stream does not contain any data.
    """
    ACK = 1
    """
    A acknowledge has been received.
    """
    DATA = 2
    """
    Data or an server error has been received.
    """


@dataclass
class MeComPacket:
    """
    Represents all fields within a package.

    :param control: The identifiers have been selected such that the receiving device,
            in order to detect the start of a frame, can synchronize to a character with a value.
    :type control: str
    :param address: Destination address.
    :type address: bytes
    :param sequence_number: Sequence number of the package. Should be incremented for each package
        that represents a new query or set with new content.
        Resend packages should contain the same sequence number.
    :type sequence_number: int
    :param payload: Contains the Payload of the package.
    :type payload: str
    :param receive_type: Only used in case of reception.
        Defines the type of package that has been received.
    :type receive_type: ERcvType
    """

    control: str
    address: int
    sequence_number: int
    payload: str
    receive_type: ERcvType

    def __init__(self, control: Optional[str] = None, address: int = 1):
        """
        Initializes a new instance of a data package.

        :param control: The identifiers have been selected such that the receiving device,
            in order to detect the start of a frame, can synchronize to a character with a value.

            Control Type         |        ASCII           |        HEX
            --------------------------------------------------------------------
            Device                         !                       0x21
            Host Frame Start               #                       0x23

            The Server (i.e. TEC controller) does always use Control Type "Device" (i.e. "#").

        :type control: Optional[str]
        :param address: Destination address.
        :type address: int
        """
        self.control = control
        self.address = address
        self.sequence_number = 0  # change from zero to a randomly generated integer
        self.payload = ""
        self.receive_type = ERcvType.EMPTY


class MeComFrame:
    """
    Handles the communication Frame level of the Meerstetter Engineering GmbH
    Communication protocol.
    """
    def __init__(self, int_phy_com: MeComPhySerialPort, statistics: Optional = None):
        """
        Saves the needed interface internally for further use.
        
        :param int_phy_com: Interface to the physical interface.
        :type int_phy_com: MeComPhySerialPort
        :param statistics: Reference to the Statistics module.
        :type statistics: Optional
        """
        self.phy_com: MeComPhySerialPort = int_phy_com
        self.statistics = statistics

        self.last_crc: int = 0

    def send_frame(self, tx_frame: MeComPacket) -> None:
        """
        Serializes the given Data structure to a proper 
        frame and sends it to the physical interface. 
        It returns immediately.
        
        :param tx_frame: Data to send.
        :type tx_frame: MeComPacket
        :raises MeComPhyInterfaceException:
        :return: None
        """
        mecom_var_convert = MeComVarConvert()

        # Build the Transmit Frame (i.e. tx_stream)
        tx_stream: str = ""
        tx_stream += tx_frame.control

        tx_stream = mecom_var_convert.add_uint8(stream=tx_stream, value=tx_frame.address)

        tx_stream = mecom_var_convert.add_uint16(stream=tx_stream, value=tx_frame.sequence_number)

        tx_stream += tx_frame.payload

        self.last_crc = self._calc_crc_citt(frame=tx_stream.encode())

        tx_stream = mecom_var_convert.add_uint16(stream=tx_stream, value=self.last_crc)

        # add end of line (carriage return)
        tx_stream += "\r"

        self.phy_com.send_string(stream=tx_stream)

    def receive_frame_or_timeout(self) -> MeComPacket:
        """
        Receives a correct frame or throws a timeout exception.

        :return: Received data.
        :rtype: MeComPacket
        """
        rx_frame = MeComPacket()
        rx_frame.receive_type = ERcvType.EMPTY

        rx_stream: str = self.phy_com.get_data_or_timeout()

        rx_frame = self._decode_frame(rx_frame=rx_frame, rx_stream=rx_stream)

        return rx_frame

    def _decode_frame(self, rx_frame: MeComPacket, rx_stream: str, local_rx_buf: Optional = None) -> MeComPacket:
        """

        :param rx_frame:
        :type rx_frame: MeComPacket
        :param rx_stream:
        :type rx_stream: bytes
        :param local_rx_buf:
        :type local_rx_buf:
        :return:
        :return: MeComPacket
        """
        # rx_frame.control = rx_stream[0]
        # rx_frame.address = int(rx_stream[1:3], 16)
        # rx_frame.sequence_number = int(rx_stream[3:7], 16)
        #
        # rx_frame.payload = rx_stream[7:-4]

        mecom_var_convert = MeComVarConvert()
        # End of Frame received
        if len(rx_stream) == 11:
            # ACK received
            rcv_crc = mecom_var_convert.read_uint16(stream=rx_stream[7:11])
            if rcv_crc == self.last_crc:
                # Valid ACK received --> Extract Data
                rx_frame.address = mecom_var_convert.read_uint8(stream=rx_stream[1:3])
                rx_frame.sequence_number = mecom_var_convert.read_uint16(stream=rx_stream[3:7])
                rx_frame.receive_type = ERcvType.ACK

        else:
            # Data Frame received
            rcv_crc = int(rx_stream[-4:], 16)

            # Cut received CRC from stream and recalc CRC
            calc_crc = self._calc_crc_citt(frame=rx_stream[:-4].encode())

            if calc_crc == rcv_crc:
                rx_frame.address = mecom_var_convert.read_uint8(stream=rx_stream[1:3])
                rx_frame.sequence_number = mecom_var_convert.read_uint16(stream=rx_stream[3:7])
                rx_frame.payload = rx_stream[7:-4]
                rx_frame.receive_type = ERcvType.DATA
            else:
                raise WrongChecksumException("The RX checksum does not match the TX checksum")

        return rx_frame

    def _calc_crc_citt(self, frame: bytes) -> int:
        """
        Calculate the checksum of a given frame

        :param frame: mecom frame without the checksum
        :type frame: bytes
        :return: the checksum for the given frame
        :rtype: int
        """
        crc: int = CRCCCITT().calculate(input_data=frame)
        return crc
