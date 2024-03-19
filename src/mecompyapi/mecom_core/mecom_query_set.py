import random

from typing import Union

from mecompyapi.mecom_core.mecom_frame import MeComFrame, MeComPacket, ERcvType
from mecompyapi.phy_wrapper.int_mecom_phy import IntMeComPhy, MeComPhyTimeoutException
from mecompyapi.phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort
from mecompyapi.phy_wrapper.mecom_phy_ftdi import MeComPhyFtdi


class SetServerErrorException(Exception):
    def __init__(self, message):
        super().__init__(message)


class CheckIfConnectedOrException(Exception):
    """
    If the interface is not ready and the current thread is not the
    creator of this instance, throw exception
    """

    def __init__(self, message):
        super().__init__(message)


class ServerException(Exception):
    """
    Is used when the server has returned a Server Error Code.
    """

    def __init__(self, message):
        super().__init__(message)


class NotConnectedException(Exception):
    """
    Initializes a new instance of NotConnectedException.
    """

    def __init__(self, message):
        super().__init__(message)


class GeneralException(Exception):
    """
    Is used to encapsulate all not specific exceptions.
    Check the inner exception for details.
    """

    def __init__(self, message):
        super().__init__(message)


class MeComQuerySet:
    """
    Represents the transport layer of the communication protocol.
    Is responsible that each query of set is executed correctly, 
    otherwise it will throw an exception.
    """

    def __init__(self, phy_com: Union[MeComPhySerialPort, MeComPhyFtdi]):
        """
        Initializes the communication interface.
        This object can then be passed to the Command objects like MeBasicCmd.

        :param phy_com:
        :type phy_com: IntMeComPhy
        """
        self.phy_com = phy_com
        self.me_frame = MeComFrame(int_phy_com=phy_com)
        self.sequence_number: int = random.randrange(0, 65_535, 1)

        self.is_ready: bool = False
        self.version_is_okay: bool = False
        self.default_device_address: int = 1

    def get_is_ready(self) -> bool:
        """
        True when the interface is ready to use; false if not.

        Is automatically set to false if an interface error or timeout error occurs.
        Must be set from application level with set_is_ready() function.

        :return:
        :rtype: bool
        """
        return self.is_ready

    def set_is_ready(self, is_ready: bool) -> None:
        """
        Used from application level to inform other threads that the interface is ready.

        Usually the application device connector searches for a valid device
        and sets then the interface as ready.

        :param is_ready:
        :type is_ready: bool
        :raises NotSupportedException: Thrown when another thread than the creator of
            this instance tries to set ready.
        :return: None
        """
        self.is_ready = is_ready

    def get_version_is_okay(self) -> bool:
        """
        True when the application connector has recognized a valid device firmware version;

        Is automatically set to false if an interface error or timeout error occurs.
        Must be set from application level with SetVersionIsOK() function.

        :return:
        :rtype: bool
        """
        return self._version_is_okay()

    def set_version_is_okay(self, version_is_okay: bool) -> None:
        """
        Used from application level to inform other threads that the interface
        is connected to a device with a valid firmware version.

        :param version_is_okay:
        :type version_is_okay: bool
        :raises NotSupportedException: Thrown when another thread than the creator
            of this instance tries to set version OK.
        :return: None
        """
        self.version_is_okay = version_is_okay

    def _version_is_okay(self) -> bool:
        """
        true when the application connector has recognized a valid device firmware version;

        Is automatically set to false if an interface error or timeout error occurs.
        Must be set from application level with SetVersionIsOK() function.

        :return:
        :rtype: bool
        """
        return self.version_is_okay

    def get_default_device_address(self) -> int:
        """
        Represents the default destination address for the device to be addressed.
        This value is used if null is passed for the device address in a package.

        To set this value use the function SetDefaultDeviceAddress().

        :return:
        :rtype: int
        """
        return self._default_device_address()

    def set_default_device_address(self, address) -> None:
        """
        Sets the default destination address for the device to be addressed.
        This value is used if null is passed for the device address in a package.

        Usually the application device connector searches for a valid device
        and sets then this value.

        :param address:
        :type address:
        :raises NotSupportedException: Thrown when another thread than the creator
            of this instance tries to set.
        :return: None
        """
        self.default_device_address = address

    def _default_device_address(self) -> int:
        """
        Represents the default destination address for the device to be addressed.
        This value is used if null is passed for the device address in a package.

        To set this value use the function SetDefaultDeviceAddress().

        :return:
        :rtype: int
        """
        return self.default_device_address

    def get_statistics(self, xml_table: str, additional_text: str) -> None:
        """
        Returns the collected communication statistics data.

        :param xml_table:
        :type xml_table: str
        :param additional_text:
        :type additional_text: str
        """
        raise NotImplementedError

    def check_if_connected(self) -> bool:
        """
        If the interface is not ready and the current thread is
        not the creator of this instance, throw exception

        :return:
        :rtype: bool
        """
        return True

    def query(self, tx_frame: MeComPacket) -> MeComPacket:
        """
        Executes a Query. A Query is used to get some data back from the server.
        It tries automatically 3 times to resend the package if no data is replayed from the server
        of if the returned data is wrong.

        :param tx_frame: Definition of the data to send.
        :type tx_frame: MeComPacket
        :raises GeneralException: On timeout or any other exception. Check the
            inner exception for details.
        :raises ServerException: When the server replays with a Server Error Code.
        :raises NotConnectedException: When the interface is not connected.
            (Only if the calling thread is different from the creator of this object)
        :return: Received data.
        :rtype: MeComPacket
        """
        try:
            self.check_if_connected()

            try:
                rx_frame: MeComPacket = self.local_query(tx_frame=tx_frame)
                return rx_frame
            except ServerException as e:
                raise e
            except GeneralException as e:
                self.is_ready: bool = False
                raise e

        except NotConnectedException as e:
            raise e

    def set(self, tx_frame: MeComPacket) -> MeComPacket:
        """
        Executes a Set. A Set is used to set some data to the server.
        No data can be received from the server.
        It tries automatically 3 times to resend the package if no data is replayed from the server
        of if the returned data is wrong.

        :param tx_frame: Definition of the data to send.
        :type tx_frame: MeComPacket
        :raises GeneralException: On timeout or any other exception. Check the
            inner exception for details.
        :raises ServerException: When the server replays with a Server Error Code.
        :raises NotConnectedException: When the interface is not connected.
            (Only if the calling thread is different from the creator of this object)
        :return: Received data
        :rtype: MeComPacket
        """
        try:
            self.check_if_connected()

            try:
                rx_frame: MeComPacket = self.local_set(tx_frame=tx_frame)
                return rx_frame

            except ServerException as e:
                raise e

            except GeneralException as e:
                self.is_ready: bool = False
                raise e

        except NotConnectedException as e:
            raise e

    def local_query(self, tx_frame: MeComPacket) -> MeComPacket:
        """

        :param tx_frame:
        :type tx_frame: MeComPacket
        :return:
        :rtype: MeComPacket
        """
        if tx_frame.address is None:
            tx_frame.address = self.get_default_device_address()

        self.sequence_number += 1
        trials_left: int = 3
        rx_frame: MeComPacket = MeComPacket()

        while trials_left > 0:
            trials_left -= 1
            tx_frame.sequence_number = self.sequence_number

            try:
                self.me_frame.send_frame(tx_frame=tx_frame)
                if tx_frame.address == 255:
                    return rx_frame  # on the address 255, no answer is expected
                rx_frame: MeComPacket = self.me_frame.receive_frame_or_timeout()
                # if rx_frame.receive_type == ERcvType.DATA and rx_frame.sequence_number and rx_frame.address == tx_frame.address:
                #     # Corresponding Frame received
                #     if rx_frame.payload.read_byte() == "+":
                #         raise SetServerErrorException("Set Server Error Exception...")
                #     else:
                #         rx_frame.payload.position = 0  # set stream position to zero for the user
                #         return rx_frame
                return rx_frame

            except MeComPhyTimeoutException:
                # Ignore timeout on this level if some trials are left
                if trials_left == 0:
                    raise GeneralException("Query failed: Timeout!")

            except ServerException as e:
                raise e

            except Exception as e:
                raise GeneralException(f"Query failed : {e}")

        # Communication failed, check last error
        if rx_frame.receive_type != ERcvType.DATA:
            raise GeneralException(
                f"Query failed : Wrong Type of package received. "
                f"Received {rx_frame.receive_type} ; Expected {ERcvType.DATA}"
            )
        if rx_frame.sequence_number != self.sequence_number:
            raise GeneralException(
                f"Query failed : Wrong Sequence Number received. "
                f"Received {rx_frame.sequence_number} ; Expected {self.sequence_number}"
            )
        if rx_frame.address != tx_frame.address:
            raise GeneralException(
                f"Query failed : Wrong Address received. "
                f"Received {rx_frame.address} ; Expected {tx_frame.address}"
            )

        raise GeneralException("Query failed : Unknown error")

    def local_set(self, tx_frame: MeComPacket) -> MeComPacket:
        """

        """
        if tx_frame.address is None:
            tx_frame.address = self.get_default_device_address()

        self.sequence_number += 1
        trials_left: int = 3
        rx_frame: MeComPacket = MeComPacket()

        while trials_left > 0:
            trials_left -= 1
            tx_frame.sequence_number = self.sequence_number

            try:
                self.me_frame.send_frame(tx_frame)
                if tx_frame.address == 255:
                    return rx_frame  # on the address 255, no answer is expected
                rx_frame: MeComPacket = self.me_frame.receive_frame_or_timeout()
                # if rx_frame.sequence_number == self.sequence_number and rx_frame.address == tx_frame.address:
                #     # Corresponding Frame received
                #     if rx_frame.receive_type == ERcvType.DATA:
                #         # Data Frame received --> Check for error code
                #         if rx_frame.payload.read_byte() == "+":
                #             SetServerErrorException("Set Server Error Exception...")
                #         elif rx_frame.payload.position == 0:  # set stream position to zero for the user
                #             return rx_frame
                #     elif rx_frame.receive_type == ERcvType.ACK:
                #         return rx_frame
                return rx_frame

            except MeComPhyTimeoutException as e:
                # Ignore Timeout on this level if some trials are left
                if trials_left == 0:
                    raise GeneralException(f"Set failed: Timeout! : {e}")

            except ServerException:
                raise ServerException

            except Exception as e:
                raise GeneralException(f"Set failed : {e}")

        # Communication failed, check last error
        if rx_frame.sequence_number != self.sequence_number:
            raise GeneralException(
                f"Set failed: Wrong Sequence Number received. "
                f"Received {rx_frame.sequence_number} ; Expected {self.sequence_number}"
            )

        if rx_frame.address != tx_frame.address:
            raise GeneralException(
                f"Set failed: Wrong Address received. "
                f"Received {rx_frame.address} ; Expected {tx_frame.address}"
            )

        raise GeneralException("Set failed: Unknown error")
