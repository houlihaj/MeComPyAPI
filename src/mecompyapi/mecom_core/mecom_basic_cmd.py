from mecompyapi.mecom_core.com_command_exception import ComCommandException
from mecompyapi.mecom_core.mecom_frame import MeComPacket
from mecompyapi.mecom_core.mecom_query_set import MeComQuerySet
from mecompyapi.mecom_core.mecom_var_convert import MeComVarConvert
from mecompyapi.phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort


class MeComBasicCmd:
    """
    Basic communication commands. Most of the products do support them.
    """
    def __init__(self, mequery_set: MeComQuerySet):
        """
        Initializes a new instance of MeComBasicCmd.

        :param mequery_set: Reference to the communication interface.
        :type mequery_set: MeComQuerySet
        """
        self.mequery_set: MeComQuerySet = mequery_set

        # self.address = self.get_device_address()

    # region Misc Functions
    # noinspection PyMethodMayBeStatic
    def get_device_address(self) -> int:
        """
        The device reacts to the following cases:

            1) The device receives a package that matched the user configurable device address

            2) The device receives a package with the address 0. (broadcast)

            3) The device receives a package with address 255. Similar to 0, except the device
            will not send an answer back to the host.

        :return:
        :rtype: int
        """
        tx_frame: MeComPacket = MeComPacket(control="#", address=0)
        address_str: str = tx_frame.payload
        address: int = int(address_str)
        return address

    def reset_device(self, address: int, channel: int) -> None:
        """
        Resets the device.
        Usually the device does answer to this command, because the reset is slightly delayed.
        During reboot, the device can not answer to commands.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param channel: TEC output channel (i.e. Parameter Instance)
        :type channel: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: None
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "RS")
            self.mequery_set.set(tx_frame)
        except Exception as e:
            raise ComCommandException(f"Reset Device failed: {e}")

    def get_ident_string(self, address: int, channel: int) -> str:
        """
        Returns the Device Identification String.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param channel: TEC output channel (i.e. Parameter Instance)
        :type channel: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: Device Identification String. Usually 20 Chars long.
        :rtype: str
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "?IF")
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, channel)
            rx_frame: MeComPacket = self.mequery_set.query(tx_frame=tx_frame)
            return rx_frame.payload
        except Exception as e:
            raise ComCommandException(f"Get Identification String failed: {e}")

    # endregion

    # region Functions for ID Parameter system
    def get_int32_value(self, address: int, parameter_id: int, instance: int) -> int:
        """
        Returns a signed int 32Bit value from the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: Returned value.
        :rtype: int
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "?VR")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            rx_frame: MeComPacket = self.mequery_set.query(tx_frame=tx_frame)
            return mecom_var_convert.read_int32(rx_frame.payload)
        except Exception as e:
            raise ComCommandException(f"Get INT32 Value failed: {e}")

    def get_float_value(self, address: int, parameter_id: int, instance: int) -> float:
        """
        Returns a float 32Bit value from the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: Returned value.
        :rtype: float
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "?VR")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            rx_frame: MeComPacket = self.mequery_set.query(tx_frame=tx_frame)
            return mecom_var_convert.read_float32(rx_frame.payload)
        except Exception as e:
            raise ComCommandException(f"Get FLOAT Value failed: {e}")

    def get_double_value(self, address: int, parameter_id: int, instance: int) -> str:
        """
        Returns a double 64Bit value from the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: Returned value.
        :rtype: str
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "?VR")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            rx_frame: MeComPacket = self.mequery_set.query(tx_frame=tx_frame)
            return rx_frame.payload
        except Exception as e:
            raise ComCommandException(f"Get DOUBLE Value failed: {e}")

    def get_int64_value(self, address: int, parameter_id: int, instance: int) -> str:
        """
        Returns a signed int 64Bit value from the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: Returned value.
        :rtype: str
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "?VR")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            rx_frame: MeComPacket = self.mequery_set.query(tx_frame=tx_frame)
            return rx_frame.payload
        except Exception as e:
            raise ComCommandException(f"Get INT64 Value failed: {e}")

    def set_int32_value(self, address: int, parameter_id: int, instance: int, value: int) -> MeComPacket:
        """
        Sets a signed int 32Bit value to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :param value: Vale to set.
        :type value: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "VS")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            tx_frame.payload = mecom_var_convert.add_int32(tx_frame.payload, value)
            rx_frame: MeComPacket = self.mequery_set.set(tx_frame=tx_frame)
            return rx_frame

        except Exception as e:
            raise ComCommandException(
                f"Set INT32 Value failed: Address: {address}; "
                f"ID: {parameter_id}; Detail: {instance} : {e}"
            )

    def set_int64_value(self, address: int, parameter_id: int, instance: int, value: int) -> MeComPacket:
        """
        Sets a signed int 64Bit value to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :param value: Vale to set.
        :type value: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "VS")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            tx_frame.payload = mecom_var_convert.add_int64(tx_frame.payload, value)
            rx_frame: MeComPacket = self.mequery_set.set(tx_frame=tx_frame)
            return rx_frame

        except Exception as e:
            raise ComCommandException(
                f"Set INT64 Value failed: Address: {address}; "
                f"ID: {parameter_id}; Detail: {instance} : {e}"
            )

    def set_float_value(self, address: int, parameter_id: int, instance: int, value: float) -> MeComPacket:
        """
        Sets a float 32Bit value to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :param value: Vale to set.
        :type value: float
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "VS")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            tx_frame.payload = mecom_var_convert.add_float32(tx_frame.payload, value)
            rx_frame: MeComPacket = self.mequery_set.set(tx_frame=tx_frame)
            return rx_frame

        except Exception as e:
            raise ComCommandException(
                f"Set FLOAT32 Value failed: Address: {address}; "
                f"ID: {parameter_id}; Detail: {instance} : {e}"
            )

    def set_double_value(self, address: int, parameter_id: int, instance: int, value: int) -> MeComPacket:
        """
        Sets a double 64Bit value to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :param value: Vale to set.
        :type value: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        mecom_var_convert: MeComVarConvert = MeComVarConvert()
        try:
            tx_frame: MeComPacket = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "VS")
            tx_frame.payload = mecom_var_convert.add_uint16(tx_frame.payload, parameter_id)
            tx_frame.payload = mecom_var_convert.add_uint8(tx_frame.payload, instance)
            tx_frame.payload = mecom_var_convert.add_double64(tx_frame.payload, value)
            rx_frame: MeComPacket = self.mequery_set.set(tx_frame=tx_frame)
            return rx_frame

        except Exception as e:
            raise ComCommandException(
                f"Set DOUBLE64 Value failed: Address: {address}; "
                f"ID: {parameter_id}; Detail: {instance} : {e}"
            )

    def set_device_address(
            self, address: int, device_type: int, serial_number: str, set_address: int, option: int
    ):
        """
        Sets a signed int 64Bit value to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param device_type: Type of the device.
        :type device_type: int
        :param serial_number: Serial number of the Device
        :type serial_number: str
        :param set_address: Address to be set.
        :type set_address: int
        :param option: Option. 0=Set address, 1=rack system.
        :type option: int
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        raise NotImplementedError

    def get_limits(
            self, address: int, parameter_id: int, instance: int, min_: float, max_: float
    ):
        """
        Returns the basic Meta data to the parameter.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on MeComQuerySet.
        :type address: int
        :param parameter_id: Device Parameter ID.
        :type parameter_id: int
        :param instance: Parameter Instance. (usually 1)
        :type instance: int
        :param min_: Minimal value. Is always a double value.
        :type min_: float
        :param max_: Maximal value. Is always a double value.
        :type max_: float
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        raise NotImplementedError

    # endregion


if __name__ == "__main__":
    phy_com: MeComPhySerialPort = MeComPhySerialPort()
    phy_com.connect(port_name="COM9")

    mequery_set_: MeComQuerySet = MeComQuerySet(phy_com=phy_com)

    mecom_basic_cmd: MeComBasicCmd = MeComBasicCmd(mequery_set=mequery_set_)

    identify: str = mecom_basic_cmd.get_ident_string(address=2, channel=1)
    print(f"identify : {identify}")
    print(f"type(identify) : {type(identify)}")
    print("\n", end="")

    device_type_: int = mecom_basic_cmd.get_int32_value(
        address=2, parameter_id=100, instance=1
    )  # parameter_name : "Device Type"
    print(f"device_type : {device_type_}")
    print(f"type(device_type) : {type(device_type_)}")
    print("\n", end="")

    object_temperature: float = mecom_basic_cmd.get_float_value(
        address=2, parameter_id=1000, instance=1
    )  # parameter_name : "Object Temperature"
    print(f"object_temperature : {object_temperature}")
    print(f"type(object_temperature) : {type(object_temperature)}")
    print("\n", end="")

    phy_com.tear()
    print("Done...")
