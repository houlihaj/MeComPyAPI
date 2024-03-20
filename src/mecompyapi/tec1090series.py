import os
import logging
import time
import datetime
import statistics
from enum import Enum
from typing import Tuple, List, Optional

from mecompyapi.mecom_core.mecom_query_set import MeComQuerySet
from mecompyapi.mecom_core.mecom_basic_cmd import MeComBasicCmd
from mecompyapi.mecom_core.com_command_exception import ComCommandException

from mecompyapi.phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort
from mecompyapi.phy_wrapper.mecom_phy_ftdi import MeComPhyFtdi

from mecompyapi.mecom_tec.lookup_table.lut_cmd import LutCmd
from mecompyapi.mecom_tec.lookup_table.lut_status import LutStatus
from mecompyapi.mecom_tec.lookup_table.lut_exception import LutException


class TimeoutException(Exception):
    def __init__(self, message):
        super().__init__(message)


class TemperatureStability(Enum):
    NOT_ACTIVE = 0  # Temperature regulation is not active
    NOT_STABLE = 1  # Is not stable
    STABLE = 2  # Is stable


class DeviceStatus(Enum):
    INIT = 0
    READY = 1
    RUN = 2
    ERROR = 3
    BOOTLOADER = 4
    DEVICE_WILL_RESET_WITHIN_NEXT_200_MS = 5


class ControlInputSelection(Enum):
    STATIC_CURRENT_VOLTAGE = 0  # Static Current/Voltage
    LIVE_CURRENT_VOLTAGE = 1  # Live Current/Voltage
    TEMPERATURE_CONTROLLER = 2  # Temperature Controller


class GeneralOperatingMode(Enum):
    SINGLE = 0  # Single (Independent)
    PARALLEL_INDIVIDUAL_LOADS = 1  # Parallel (CH1 -> CH2); Individual Loads
    PARALLEL_COMMON_LOAD = 2  # Parallel (CH1 -> CH2); Common Load


class ThermalRegulationMode(Enum):
    PELTIER_FULL_CONTROL = 0  # Peltier, Full Control
    PELTIER_HEAT_ONLY_COOL_ONLY = 1  # Peltier, Heat Only - Cool Only
    RESISTOR_HEAT_ONLY = 2  # Resistor, Heat Only


class PositiveCurrentIs(Enum):
    COOLING = 0
    HEATING = 1


class ObjectSensorType(Enum):
    UNKNOWN_TYPE = 0
    PT100 = 1
    PT1000 = 2
    NTC18K = 3
    NTC39K = 4
    NTC56K = 5
    NTC1M_NTC = 6  # NTC1M/NTC
    VIN1 = 7


class OutputStageEnable(Enum):
    STATIC_OFF = 0
    STATIC_ON = 1
    LIVE_OFF_ON = 2
    HW_ENABLE = 3


class LookupTableStatus(Enum):
    NOT_INITIALIZED = 0
    TABLE_DATA_NOT_VALID = 1
    ANALYZING_DATA_TABLE = 2
    READY = 3  # Data Table Okay
    EXECUTING = 4
    MAX_NUMBERS_OF_TABLES_EXCEEDED = 5
    SUB_TABLE_NOT_FOUND = 6


class SaveToFlashState(Enum):
    ENABLED = 0
    DISABLED = 1  # all parameters are now RAM parameters


class FlashStatus(Enum):
    ALL_SAVED_TO_FLASH = 0
    """
    All Parameters are saved to Flash
    """
    PENDING = 1
    """
    Save to Flash pending or in progress.
    Please do not power off the device now.
    """
    DISABLED = 2
    """
    Saving to Flash is disabled
    """


class MeerstetterTEC(object):
    r"""
    Controlling TEC devices via serial.

    Definitions of command and error codes as stated in the "Mecom" protocol standard:

    ./meerstetter/pyMeCom/mecom/commands.py
    """
    def __init__(self, *args, **kwargs) -> None:
        self.phy_com: Optional[MeComPhySerialPort | MeComPhyFtdi] = None
        self.mequery_set: Optional[MeComQuerySet] = None
        self.mecom_basic_cmd: Optional[MeComBasicCmd] = None
        self.mecom_lut_cmd: Optional[LutCmd] = None
        self.address: Optional[int] = None
        self.instance: Optional[int] = None

    def connect_serial_port(self, port: str = "COM9", instance: int = 1) -> None:
        """
        Connects to a serial port. On Windows, these are typically 'COMX' where X
        is the number of the port. In Linux, they are often /dev/ttyXXXY where XXX
        usually indicates if it is a serial or USB port, and Y indicates the number.
        E.g. /dev/ttyUSB0 on Linux and 'COM7' on Windows

        The get_device_address() query is in a retry after exception loop because
        the query will return fewer bytes than expected after closing the Meerstetter
        TEC Service Software application. The query typically fails on the first
        request but will succeed on the second request.

        :param port: Port, as described in description
        :type port: str
        :param instance:
        :type instance: int
        :return: None
        """
        self.instance: int = instance

        self.phy_com: MeComPhySerialPort = MeComPhySerialPort()
        self.phy_com.connect(port_name=port)

        mequery_set = MeComQuerySet(phy_com=self.phy_com)
        self.mecom_basic_cmd = MeComBasicCmd(mequery_set=mequery_set)

        # Get Identification String
        fw_id_str: str = self.get_firmware_identification_string(broadcast=True)
        logging.debug(f"Connected device firmware identification string (?IF) : {fw_id_str}")

        self.mecom_lut_cmd = LutCmd(mecom_query_set=mequery_set)

        retries = 3
        for _ in range(retries):
            try:
                self.address = self.get_device_address()
                logging.debug(f"connected to {self.address}")
                return
            except ComCommandException as e:
                logging.debug(f"[ComCommandException] : {e}")
                continue
        raise ComCommandException(
            f"Could not successfully query the controller address after {retries} retries..."
        )

    def connect_ftdi(self, id_str: Optional[str] = None, instance: int = 1) -> None:
        """
        Connect to the controller using the FTDI chip drivers.

        :param id_str:
        :type id_str: Optional[str]
        :param instance:
        :type instance: int
        :raises ComCommandException:
        :return: None
        """
        self.instance: int = instance

        self.phy_com: MeComPhyFtdi = MeComPhyFtdi()

        self.phy_com.connect(id_str=id_str)
        mequery_set: MeComQuerySet = MeComQuerySet(phy_com=self.phy_com)
        self.mecom_basic_cmd: MeComBasicCmd = MeComBasicCmd(mequery_set=mequery_set)
        self.mecom_lut_cmd: LutCmd = LutCmd(mecom_query_set=mequery_set)

        retries: int = 3
        for _ in range(retries):
            try:
                self.address: int = self.get_device_address()
                logging.debug(f"connected to {self.address}")
                return
            except ComCommandException as e:
                logging.debug(f"[ComCommandException] : {e}")
                continue
        raise ComCommandException(
            f"Could not successfully query the controller address after {retries} retries..."
        )

    def tear(self) -> None:
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.

        :return: None
        """
        self.phy_com.tear()

    def reset(self) -> None:
        """
        Resets the device after an error has occurred.

        :return: None
        """
        self.mecom_basic_cmd.reset_device(address=self.address, channel=self.instance)

    def get_firmware_identification_string(self, broadcast: bool = False) -> str:
        """
        Query the Firmware Identification String of the device.

        Using address 0, the device will always answer independent of its address. The
        device is in broadcast mode and receives a package when using address 0.

        The device should only be in broadcast mode during the connection routine. Once
        connected, all methods should use the unique address of the device.

        :param broadcast: When True, the device will answer independent of its
            unique address.
        :type broadcast: bool
        :return: The firmware identification string of the device.
        :rtype: str
        """
        logging.debug(f"get the firmware identification string for channel {self.instance}")
        address = 0 if broadcast else self.address
        identify: str = self.mecom_basic_cmd.get_ident_string(address=address, channel=self.instance)
        return identify

    def get_id(self) -> str:
        """
        Query the Identification String of the device.

        :return: The identification string for the device. The string is comma separated and contains
            the follow components in order: Make, Model, Serial Number, Hardware Version, and Firmware
            Version.
        :rtype: str
        """
        model: int = self.get_device_type()
        sn: int = self.get_serial_number()
        hw: int = self.get_hardware_version()
        fw: int = self.get_firmware_version()
        identity: str = f"Meerstetter,TEC{model},{sn},{hw},{fw}"
        return identity

    def get_device_type(self) -> int:
        """
        Query the device type (Ex. 1090, 1091, 1092, etc.).

        :return: the TEC controller device type identification
        :rtype: int
        """
        logging.debug(f"get device type for channel {self.instance}")
        device_type = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=100, instance=self.instance
        )
        return device_type

    def get_hardware_version(self) -> int:
        """
        Query the hardware version from the device.

        :return: The hardware version of the device.
        :rtype: int
        """
        logging.debug(f"get hardware version for channel {self.instance}")
        hardware_version = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=101, instance=self.instance
        )
        return hardware_version

    def get_serial_number(self) -> int:
        """
        Query the serial number of the device.

        :return: The serial number of the device.
        :rtype: int
        """
        logging.debug(f"get serial number for channel {self.instance}")
        serial_number = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=102, instance=self.instance
        )
        return serial_number

    def get_firmware_version(self) -> int:
        """
        Query the firmware version of the device.

        :return: The firmware version of the device.
        :rtype: int
        """
        logging.debug(f"get firmware version for channel {self.instance}")
        firmware_version = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=103, instance=self.instance
        )
        return firmware_version

    def get_device_status(self) -> DeviceStatus:
        """
        Query the status of the device.

        :return: the active status of the TEC controller
        :rtype: DeviceStatus
        """
        logging.debug(f"get device status for channel {self.instance}")
        status_id_int = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=104, instance=self.instance
        )
        status_id = DeviceStatus(status_id_int)
        return status_id

    def set_automatic_save_to_flash(self, save_to_flash: SaveToFlashState) -> None:
        """
        Enable or disable the automatic save to flash mechanism.

        :param save_to_flash: enable or disable the automatic save to flash mechanism
        :type save_to_flash: SaveToFlashState
        :return: None
        """
        logging.debug(f"set the automatic save to flash state for channel {self.instance} to {save_to_flash}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=108, instance=self.instance, value=save_to_flash.value
        )

    def get_automatic_save_to_flash(self) -> SaveToFlashState:
        """
        Get the automatic save to flash mechanism state.

        :return: returns whether the automatic save to flash mechanism
            is enabled or disabled
        :rtype: SaveToFlashState
        """
        logging.debug(f"get the automatic save to flash state for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=108, instance=self.instance
        )
        save_to_flash_state = SaveToFlashState(int(resp))
        return save_to_flash_state

    def get_flash_status(self):
        """

        """
        logging.debug(f"get the flash status for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=109, instance=self.instance
        )
        flash_status = FlashStatus(int(resp))
        return flash_status

    def get_temperature(self) -> float:
        """
        Get object temperature of channel to desired value.

        :return: The object temperature in units of degrees Celsius (degC).
        :rtype: float
        """
        logging.debug(f"get object temperature for channel {self.instance}")
        object_temperature = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1000, instance=self.instance
        )
        return object_temperature

    def get_sink_temperature(self) -> float:
        """
        Get the sink temperature of channel.

        :return: The sink temperature in units of degrees Celsius (degC).
        :rtype: float
        """
        logging.debug(f"get sink temperature for channel {self.instance}")
        sink_temperature = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1001, instance=self.instance
        )
        return sink_temperature

    def get_setpoint_temperature(self) -> float:
        """
        Get the setpoint temperature from the TEC controller

        :return: the setpoint temperature from the TEC controller
            in units of degC
        :rtype: float
        """
        logging.debug(f"get the setpoint temperature for channel {self.instance}")
        setpoint = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1010, instance=self.instance
        )
        return setpoint

    def get_ramp_nominal_object_temperature(self) -> float:
        """
        Get the (ramp) nominal object temperature from the TEC controller

        :return: the (ramp) nominal object temperature from the TEC controller
            in units of degC
        :rtype: float
        """
        logging.debug(f"get the (ramp) nominal object temperature for channel {self.instance}")
        ramp_nominal_temperature = (
            self.mecom_basic_cmd.get_float_value(
                address=self.address, parameter_id=1011, instance=self.instance
            )
        )
        return ramp_nominal_temperature

    def get_thermal_power_model_current(self) -> float:
        """
        Get the thermal power model current from the TEC controller

        :return: the thermal power model current in units of Amps (A)
        :rtype: float
        """
        logging.debug(f"get the thermal power model current for channel {self.instance}")
        current = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1012, instance=self.instance
        )
        return current

    def get_tec_current(self) -> float:
        """
        Get the actual output current.

        :return: The output current in units of Amps (A).
        :rtype: float
        """
        logging.debug(f"get output current for channel {self.instance}")
        output_current = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1020, instance=self.instance
        )
        return output_current

    def get_tec_voltage(self) -> float:
        """
        Get the actual output voltage.

        :return: The output voltage in units of Volts (V).
        :rtype: float
        """
        logging.debug(f"get output voltage for channel {self.instance}")
        output_voltage = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1021, instance=self.instance
        )
        return output_voltage

    def get_pid_control_variable(self) -> float:
        """
        Get the PID Control Variable percentage. Part of the Temperature Control
        PID Status section.

        :return: The PID Control Variable as a percentage (%).
        :rtype: float
        """
        logging.debug(f"get the PID control variable percentage for channel {self.instance}")
        pid_control_variable = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1032, instance=self.instance
        )
        return pid_control_variable

    def get_device_temperature(self) -> float:
        """
        Get the temperature of the TEC controller device.

        :return: The TEC controller temperature in units of degrees Celsius (degC).
        :rtype: float
        """
        logging.debug(f"get the device temperature for channel {self.instance}")
        device_temp = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=1063, instance=self.instance
        )
        return device_temp

    def is_temperature_stable(self) -> bool:
        """
        Check to see if the temperature is stable.

        :return: True if the temperature is stable, False otherwise
        :rtype: bool
        """
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=1200, instance=self.instance
        )
        stability = TemperatureStability(int(resp))
        logging.debug(f"Temperature Stability: {stability.name}")
        return stability == TemperatureStability.STABLE

    def set_input_selection(self, input_selection: ControlInputSelection) -> None:
        """
        Set the output control input selection.

        :param input_selection: the output control input selection for the TEC controller
        :type input_selection: ControlInputSelection
        :return: None
        """
        logging.debug(f"set the input selection for channel {self.instance} to {input_selection}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=2000, instance=self.instance, value=input_selection.value
        )

    def get_input_selection(self) -> ControlInputSelection:
        """
        Get the output control input selection.

        :return: the output control input selection for the TEC controller
        :rtype: ControlInputSelection
        """
        logging.debug(f"get the input selection for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=2000, instance=self.instance
        )
        input_selection = ControlInputSelection(int(resp))
        return input_selection

    def set_output_stage_enable(self, output_stage_enable: OutputStageEnable) -> None:
        """
        Set the output stage enable used by the TEC controller

        :param output_stage_enable: the output stage enable used by the TEC controller
        :type output_stage_enable: OutputStageEnable
        :return: None
        """
        logging.debug(f"set the output stage enable for channel {self.instance} to {output_stage_enable}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=2010, instance=self.instance, value=output_stage_enable.value
        )

    def get_output_stage_enable(self) -> OutputStageEnable:
        """
        Get the output stage enable used by the TEC controller.

        :return: the output stage enable used by the TEC controller
        :rtype: OutputStageEnable
        """
        logging.debug(f"get the output stage enable for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=2010, instance=self.instance
        )
        return OutputStageEnable(int(resp))

    def set_current_limitation(self, current_limit_amps: float) -> None:
        """
        Set the limiting drive current in units of Amps.

        :param current_limit_amps: the limiting drive current value in units of Amps.
        :type current_limit_amps: float
        :return: None
        """
        logging.debug(
            f"set current limitation for channel {self.instance} to {float(current_limit_amps)} Amps"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=2030, instance=self.instance, value=float(current_limit_amps)
        )

    def get_current_limitation(self) -> float:
        """
        Get the limiting drive current in units of Amps.

        :return: the limiting drive current for the TEC controller in units of Amps
        :rtype: float
        """
        logging.debug(f"get the current limitation for channel {self.instance}")
        current_limit = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=2030, instance=self.instance
        )
        return current_limit

    def set_voltage_limitation(self, voltage_limit_volts: float) -> None:
        """
        Set the limiting drive voltage in units of Volts.

        :param voltage_limit_volts: the limiting drive current value in units of Volts.
        :type voltage_limit_volts: float
        :return: None
        """
        logging.debug(
            f"set voltage limitation for channel {self.instance} to {float(voltage_limit_volts)} Volts"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=2031, instance=self.instance, value=float(voltage_limit_volts)
        )

    def get_voltage_limitation(self) -> float:
        """
        Get the limiting drive voltage in units of Volts.

        :return: the limiting drive voltage for the TEC controller in units of Volts
        :rtype: float
        """
        logging.debug(f"get the voltage limitation for channel {self.instance}")

        voltage_limit = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=2031, instance=self.instance
        )
        return voltage_limit

    def set_current_error_threshold(self, threshold_amps: float) -> None:
        """
        Set the current error threshold in units of Amps.

        :param threshold_amps: the current error threshold in units of Amps
        :type threshold_amps: float
        :return: none
        """
        logging.debug(
            f"set current error threshold for channel {self.instance} to {float(threshold_amps)} Amps"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=2032, instance=self.instance, value=float(threshold_amps)
        )

    def get_current_error_threshold(self) -> float:
        """
        Get the current error threshold.

        :return: the current error threshold in units of Amps
        :rtype: float
        """
        logging.debug(f"get the current error threshold for channel {self.instance}")
        curr_threshold = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=2032, instance=self.instance
        )
        return curr_threshold

    def set_voltage_error_threshold(self, threshold_volts: float) -> None:
        """
        Set the voltage error threshold in units of Volts.

        :param threshold_volts: the voltage error threshold in units of Volts
        :type threshold_volts: float
        :return: none
        """
        logging.debug(
            f"set voltage error threshold for channel {self.instance} to {float(threshold_volts)} Volts"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=2033, instance=self.instance, value=float(threshold_volts)
        )

    def get_voltage_error_threshold(self) -> float:
        """
        Get the voltage error threshold.

        :return: the voltage error threshold in units of Volts
        :rtype: float
        """
        logging.debug(f"get the voltage error threshold for channel {self.instance}")
        volt_threshold = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=2033, instance=self.instance
        )
        return volt_threshold

    def set_general_operating_mode(self, operating_mode: GeneralOperatingMode) -> None:
        """
        Set the operating mode of the TEC controller.

        :param operating_mode: the operating mode of the TEC controller
        :type operating_mode: GeneralOperatingMode
        :return: None
        """
        logging.debug(
            f"set the general operating mode for channel {self.instance} to {operating_mode}"
        )
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=2040, instance=self.instance, value=operating_mode.value
        )

    def get_general_operating_mode(self) -> GeneralOperatingMode:
        """
        Get the operating mode of the TEC controller.

        :return: the operating mode of the TEC controller
        :rtype: GeneralOperatingMode
        """
        logging.debug(f"get the general operating mode for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=2040, instance=self.instance
        )
        operating_mode = GeneralOperatingMode(int(resp))
        return operating_mode

    def get_base_baud_rate(self) -> int:
        """
        Get the UART base baud rate.

        :return: the UART base baud rate
        :rtype: int
        """
        logging.debug(f"get the UART base baud rate for channel {self.instance}")
        baud_rate = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=2050, instance=self.instance
        )
        return baud_rate

    def get_device_address(self) -> int:
        """
        Query the device address.

        Using address 0, the device will always answer independent of its address. The
        device is in broadcast mode and receives a package when using address 0.

        The advice is to use address 0 for this method alone. This method will return
        the device address, which should be used for all other methods.

        :return: the device address
        :rtype: int
        """
        logging.debug(f"get the device address for channel {self.instance}")
        device_address = self.mecom_basic_cmd.get_int32_value(
            address=0, parameter_id=2051, instance=self.instance
        )
        return device_address

    def get_uart_response_delay(self) -> float:
        """
        Get the UART response delay for the controller.

        :return: the UART response delay in units of microseconds (us)
        :rtype: float
        """
        logging.debug(f"get the UART response delay for channel {self.instance}")
        delay_us = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=2052, instance=self.instance
        )
        return delay_us

    def set_temperature(self, temp_degc: float) -> None:
        """
        Set object temperature of channel to desired value in units of degrees Celsius.

        :param temp_degc: The desired object temperature value in units of degrees Celsius.
            The controller will set the object to this temperature value.
        :type temp_degc: float
        :return: None
        """
        logging.debug(f"set object temperature for channel {self.instance} to {temp_degc} C")
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=3000, instance=self.instance, value=float(temp_degc)
        )

    def set_coarse_temperature_ramp(self, temp_ramp_degc_per_sec: float) -> None:
        """
        Set the coarse temperature ramp of the TEC controller to desired value in
        units of degrees Celsius per second.

        :param temp_ramp_degc_per_sec: the coarse temperature ramp value in units of degrees Celsius per second.
        :type temp_ramp_degc_per_sec: float
        :return: None
        """
        logging.debug(
            f"set coarse temperature ramp for channel {self.instance} to {float(temp_ramp_degc_per_sec)} degC/second"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=3003, instance=self.instance, value=float(temp_ramp_degc_per_sec)
        )

    def get_coarse_temperature_ramp(self) -> float:
        """
        Get the coarse temperature ramp setting.

        :return: the coarse temperature ramp setting for the controller
            in units of degC/second
        :rtype: float
        """
        logging.debug(f"get the coarse temperature ramp for channel {self.instance}")
        temp_ramp = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=3003, instance=self.instance
        )
        return temp_ramp

    def set_proportional_gain(self, prop_gain: float) -> None:
        """
        Set the proportional gain (Kp) for the PID controller.

        :param prop_gain: the proportional gain (Kp)
        :type prop_gain: float
        :return: None
        """
        logging.debug(
            f"set the proportional gain (Kp) for channel {self.instance} to {float(prop_gain)}"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=3010, instance=self.instance, value=float(prop_gain)
        )

    def get_proportional_gain(self) -> float:
        """
        Get the proportional gain (Kp) for the PID controller.

        :return: the proportional gain (Kp)
        :rtype: float
        """
        logging.debug(f"get the proportional gain (Kp) for channel {self.instance}")
        proportional_gain = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=3010, instance=self.instance
        )
        return proportional_gain

    def set_integration_time(self, int_time_sec: float) -> None:
        """
        Set the integration time (Ti) for the PID controller.

        :param int_time_sec: the integration time (Ti) in units of seconds
        :type int_time_sec: float
        :return: None
        """
        logging.debug(
            f"set the integration time (Ti) for channel {self.instance} to {float(int_time_sec)} seconds"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=3011, instance=self.instance, value=float(int_time_sec)
        )

    def get_integration_time(self) -> float:
        """
        Get the integration time (Ti) for the PID controller.

        :return: the integration time (Ti) in units of seconds
        :rtype: float
        """
        logging.debug(f"get the integration time (Ti) for channel {self.instance}")
        integration_time = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=3011, instance=self.instance
        )
        return integration_time

    def set_differential_time(self, diff_time_sec: float) -> None:
        """
        Set the differential time (Td) for the PID controller.

        :param diff_time_sec: the differential time (Td) in units of seconds
        :type diff_time_sec: float
        :return: None
        """
        logging.debug(
            f"set the differential time (Td) for channel {self.instance} to {float(diff_time_sec)} seconds"
        )
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=3012, instance=self.instance, value=float(diff_time_sec)
        )

    def get_differential_time(self) -> float:
        """
        Get the differential time (Td) for the PID controller.

        :return: the differential time (Td) in units of seconds
        :rtype: float
        """
        logging.debug(f"get the differential time (Td) for channel {self.instance}")
        differential_time = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=3012, instance=self.instance
        )
        return differential_time

    def set_part_damping(self, part_damping: float) -> None:
        """
        Set D Part Damping PT1 for the PID controller. The value “D Part Damping PT1” is damping the resulting value of
        the derivative term. It may be useful for very slow thermal models which result in high Td times.

        :param part_damping: D Part Damping PT1 value
        :type part_damping: float
        :return: None
        """
        logging.debug(f"set D Part Damping PT1 for channel {self.instance} to {float(part_damping)}")
        self.mecom_basic_cmd.set_float_value(
            address=self.address, parameter_id=3013, instance=self.instance, value=float(part_damping)
        )

    def get_part_damping(self) -> float:
        """
        Get D Part Damping PT1 for the PID controller. The value “D Part Damping PT1” is damping the resulting value of
        the derivative term. It may be useful for very slow thermal models which result in high Td times.

        :return: D Part Damping PT1 value
        :rtype: float
        """
        logging.debug(f"get D Part Damping PT1 for channel {self.instance}")
        part_damping = self.mecom_basic_cmd.get_float_value(
            address=self.address, parameter_id=3013, instance=self.instance
        )
        return part_damping

    def set_thermal_regulation_mode(self, regulation_mode: ThermalRegulationMode) -> None:
        """
        Set the thermal regulation mode used by the TEC controller

        :param regulation_mode: the operating mode of the TEC controller
        :type regulation_mode: ThermalRegulationMode
        :return: None
        """
        logging.debug(f"set the thermal regulation mode for channel {self.instance} to {regulation_mode}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=3020, instance=self.instance, value=regulation_mode.value
        )

    def get_thermal_regulation_mode(self) -> ThermalRegulationMode:
        """
        Get the thermal regulation mode used by the TEC controller

        :return: the thermal regulation mode
        :rtype: ThermalRegulationMode
        """
        logging.debug(f"get the thermal regulation mode for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=3020, instance=self.instance
        )
        regulation_mode = ThermalRegulationMode(int(resp))
        return regulation_mode

    def set_positive_current_is(self, positive_current_is: PositiveCurrentIs) -> None:
        """
        Set whether positive current is "cooling" or "heating"; meaning,
        is the TEC controller causing the TEC to cool or heat the object.

        :param positive_current_is: returns whether positive current flow causes cooling or
            heating of the TEC
        :type positive_current_is: PositiveCurrentIs
        :return: None
        """
        logging.debug(f"set the positive current is for channel {self.instance} to {positive_current_is}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=3034, instance=self.instance, value=positive_current_is.value
        )

    def get_positive_current_is(self) -> PositiveCurrentIs:
        """
        Check to see if positive current is "cooling" or "heating"; meaning,
        is the TEC controller causing the TEC to cool or heat the object.

        :return: returns whether positive current flow causes cooling or
            heating of the TEC
        :rtype: PositiveCurrentIs
        """
        logging.debug(f"get the positive current is for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=3034, instance=self.instance
        )
        return PositiveCurrentIs(int(resp))

    def set_object_sensor_type(self, sensor_type: ObjectSensorType) -> None:
        """
        Set the object sensor type used by the TEC controller

        :param sensor_type: the type of temperature sensor being used to provide feedback
        :type sensor_type: ObjectSensorType
        :return: None
        """
        logging.debug(f"set the object sensor type for channel {self.instance} to {sensor_type}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=4034, instance=self.instance, value=sensor_type.value
        )

    def get_object_sensor_type(self) -> ObjectSensorType:
        """
        Get the object sensor type being used to provide temperature feedback to the
        TEC controller.

        :return: the type of temperature sensor being used to provide feedback
        :rtype: ObjectSensorType
        """
        logging.debug(f"get the object sensor type for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(
            address=self.address, parameter_id=4034, instance=self.instance
        )
        return ObjectSensorType(int(resp))

    def download_lookup_table(self, filepath: str) -> None:
        """
        Downloads a lookup table file (*.csv) to the device. Raise an LutException
        if a timeout is triggered while trying to download the lookup table.

        :param filepath: Path of the lookup table file.
        :type filepath: str
        :raises LutException:
        :return: None
        """
        # Enter the path to the lookup table file (*.csv)
        try:
            self.mecom_lut_cmd.download_lookup_table(address=self.address, filepath=filepath)
            timeout: int = 0
            while True:
                status: LutStatus = self.mecom_lut_cmd.get_status(address=self.address, instance=self.instance)
                logging.info(f"LutCmd status : {status}")
                if status == LutStatus.NO_INIT or status == LutStatus.ANALYZING:
                    timeout += 1
                    if timeout < 50:
                        time.sleep(0.010)
                    else:
                        raise LutException("Timeout while trying to get Lookup Table status!")
                else:
                    break
            lut_table_status = self.mecom_lut_cmd.get_status(address=self.address, instance=self.instance)
            logging.info(f"Lookup Table Status (52002): {lut_table_status}")
        except LutException as e:
            raise LutException(f"Error while trying to download lookup table: {e}")

    def start_lookup_table(self) -> None:
        """
        Starts the lookup table that is currently stored on the device.

        :raises ComCommandException:
        :return: None
        """
        try:
            self.mecom_lut_cmd.start_lookup_table(address=self.address, instance=self.instance)
        except LutException as e:
            raise ComCommandException(f"start_lookup_table failed: Detail: {e}")

    def stop_lookup_table(self) -> None:
        """
        Cancels the active lookup table progress process.

        :raises ComCommandException:
        :return: None
        """
        try:
            self.mecom_lut_cmd.stop_lookup_table(address=self.address, instance=self.instance)
        except LutException as e:
            raise ComCommandException(f"stop_lookup_table failed: Detail: {e}")

    def get_lookup_table_status(self) -> LutStatus:
        """
        The status returned during the Lookup Table operating procedure

        :return: the status for the lookup table
        :rtype: LutStatus
        """
        logging.debug(f"get the lookup table status for channel {self.instance}")
        status = self.mecom_lut_cmd.get_status(address=self.address, instance=self.instance)
        return status

    def execute_lookup_table(self, timeout: float = 300) -> bool:
        """
        Runs through the entire process for successfully executing a
        lookup table.

        Method to be used after a lookup table has been successfully
        downloaded to the TEC controller.

        The method will time out if the lookup table does not complete
        its execution within the defined timeout period.

        :param timeout: Timeout period in units of seconds.
        :type timeout: float
        :return: True if the lookup table was executed successfully,
            False otherwise.
        :rtype: bool
        """
        logging.debug(f"execute the lookup table for channel {self.instance}")

        success = False

        # Stop an existing lookup table execution, if one exists
        if self.get_lookup_table_status() == LutStatus.EXECUTING:
            self.stop_lookup_table()

        try:
            self.start_lookup_table()

            lut_status: LutStatus = self.get_lookup_table_status()
            logging.info(f"lookup table status : {lut_status}")

            if lut_status != LutStatus.EXECUTING:
                raise LutException(
                    f"The lookup status should be LutStatus.EXECUTING after starting the lookup table ; "
                    f"instead the lookup status is {lut_status}."
                )

            # timeout = 300  # timeout is in units of seconds
            runtime = 0.0
            start_time = time.time()  # acquisition start
            acq = 0
            lut_status: LutStatus = self.get_lookup_table_status()
            while lut_status == LutStatus.EXECUTING and runtime < timeout:
                runtime = time.time() - start_time  # runtime is in units of seconds
                time.sleep(0.1)

                acq += 1

                if acq % 20 == 0:
                    logging.info(
                        f"The object temperature is {self.get_temperature()} degC"
                    )

                if acq % 200 == 0:
                    logging.info(f"lookup table status : {self.get_lookup_table_status()}")

                    logging.info(
                        f"The lookup table has been executing for {round(acq * 0.1)} seconds..."
                    )

                lut_status: LutStatus = self.get_lookup_table_status()

            if runtime >= timeout:
                raise LutException(
                    "Timeout raised while executing the Lookup Table ; "
                    "the lookup table took longer than expected to completely execute..."
                )

            logging.info(f"The Lookup Table has executed successfully after {round(runtime, 3)} seconds...")

            success = True

        except LutException as e:
            success = False
            raise e

        except Exception as e:
            success = False
            raise e

        finally:
            if self.get_lookup_table_status() == LutStatus.EXECUTING:
                self.stop_lookup_table()
                logging.info(
                    "Lookup Table was force stopped ; this may be because the "
                    "routine timed out while the lookup table was still executing..."
                )

            return success

    def _set_enable(self, enable: bool = True) -> None:
        """
        Enable or disable control loop.

        :param enable:
        :type enable: bool
        :return: None
        """
        value, description = (1, "on") if enable else (0, "off")
        logging.debug(f"set loop for channel {self.instance} to {description}")
        self.mecom_basic_cmd.set_int32_value(
            address=self.address, parameter_id=2010, instance=self.instance, value=value
        )

    def enable(self) -> None:
        """
        Enable or disable control loop.

        :return: None
        """
        self._set_enable(True)

    def disable(self) -> None:
        """
        Enable or disable control loop.

        :return: None
        """
        self._set_enable(False)

    def get_monitor_data_logger(self, header: bool = False) -> str:
        """

        :param header:
        :type header:
        :return:
        :rtype: str
        """
        data_log = ""
        if header is True:
            data_log += (
                "Time;CH 1 Object Temperature;CH 1 Sink Temperature;CH 1 Target Object Temperature;"
                "CH 1 (Ramp) Nominal Temperature;CH 1 Thermal Power Model Current;CH 1 Actual Output Current;"
                "CH 1 Actual Output Voltage;CH 1 PID Control Variable;\n"
            )
        time_datetime: datetime.datetime = datetime.datetime.fromtimestamp(time.time())
        object_temperature: float = self.get_temperature()
        sink_temperature: float = self.get_sink_temperature()
        setpoint_temperature: float = self.get_setpoint_temperature()
        ramp_nominal_temperature: float = self.get_ramp_nominal_object_temperature()
        thermal_power_model_current: float = self.get_thermal_power_model_current()
        actual_output_current: float = self.get_tec_current()
        actual_output_voltage: float = self.get_tec_voltage()
        pid_control_variable: float = self.get_pid_control_variable()
        data_log += (
            f"{time_datetime};{object_temperature};{sink_temperature};{setpoint_temperature};"
            f"{ramp_nominal_temperature};{thermal_power_model_current};{actual_output_current};"
            f"{actual_output_voltage};{pid_control_variable};\n"
        )
        return data_log

    def wait_for_stable_temperature(self, timeout: int = 120) -> None:
        """
        Wait for the temperature to stabilize after calling
        the set_temperature() method.

        The method starts with a one-second wait period to ensure
        the "Temperature is Stable" status has been updated after the
        set_temperature() is called. It takes approximately a half second
        for the "Temperature is Stable" status to be updated after the
        set_temperature() call.

        :param timeout: the timeout period in units of seconds
        :type timeout: int
        :raises TimeoutException:
        :return: None
        """
        time.sleep(1.0)
        runtime = 0.0
        start_time = time.time()
        stabilizing = self.is_temperature_stable()
        while stabilizing is False and runtime < timeout:
            stabilizing = self.is_temperature_stable()
            runtime = time.time() - start_time  # runtime is in units of seconds
            time.sleep(0.5)
        if runtime >= timeout:
            raise TimeoutException(f"wait_for_stable_temperature() timed out after {runtime} seconds")

    def set_and_stabilize_tec_temperature(
            self, temperature: float = 30.0, threshold_deg_c: float = 0.1
    ) -> Tuple[float, List[float]]:
        """
        Set the TEC temperature and wait for it to stabilize. The temperature is
        considered stable when the measured standard deviation is less than the defined
        threshold standard deviation (i.e. threshold_deg_c).

        :param temperature: Use the TEC controller to set the ambient temperature for the ETM
            in units of degrees Celsius.
        :type temperature: float
        :param threshold_deg_c: Threshold standard deviation (units of degC) needed for temperature
            to be considered stable
        :type: float
        :return: A tuple containing: the time taken for the object temperature to become stable
            and a list of standard deviation values measured while waiting for the object
            temperature to become stable
        :rtype: float, List[float]
        """
        self.disable()
        try:
            self.set_temperature(float(temperature))
        finally:
            self.enable()
        start_time = time.time()
        logging.info("Waiting for the temperature to stabilize...")
        standard_deviation_list = []
        standard_deviation = 1
        # Measured (i.e. object) temperature standard deviation < threshold_deg_c
        while standard_deviation > threshold_deg_c:
            # Using 100 samples to calculate the standard deviation
            object_temperatures = [self.get_temperature() for _ in range(100)]
            logging.debug(f"Object temperatures: {object_temperatures}")
            # Using statistics package to find the standard deviation
            standard_deviation = statistics.stdev(object_temperatures)
            logging.debug(f"standard_deviation: {standard_deviation}")
            standard_deviation_list.append(standard_deviation)
        total_time_to_stabilize = time.time() - start_time
        return total_time_to_stabilize, standard_deviation_list

    def get_all_settings(self) -> dict:
        """
        Query all settings from the device.

        :return:
        :rtype: dict
        """
        settings = {
            "idn": self.get_id(),
            "device_address": self.get_device_address(),
            "device_type": self.get_device_type(),
            "serial_number": self.get_serial_number(),
            "hardware_version": self.get_hardware_version(),
            "firmware_id": self.get_firmware_identification_string(),
            "firmware_version": self.get_firmware_version(),
            "device_status": self.get_device_status(),
            "object_temperature": self.get_temperature(),
            "actual_output_current": self.get_tec_current(),
            "actual_output_voltage": self.get_tec_voltage(),
            "device_temperature": self.get_device_temperature(),
            "input_selection": self.get_input_selection(),
            "current_limitation": self.get_current_limitation(),
            "voltage_limitation": self.get_voltage_limitation(),
            "current_error_threshold": self.get_current_error_threshold(),
            "voltage_error_threshold": self.get_voltage_error_threshold(),
            "general_operating_mode": self.get_general_operating_mode(),
            "base_baud_rate": self.get_base_baud_rate(),
            "uart_response_delay": self.get_uart_response_delay(),
            "coarse_temp_ramp": self.get_coarse_temperature_ramp(),
            "proportional_gain_kp": self.get_proportional_gain(),
            "integration_time_ti": self.get_integration_time(),
            "differential_time_td": self.get_differential_time(),
            "pid_part_damping": self.get_part_damping(),
            "thermal_regulation_mode": self.get_thermal_regulation_mode(),
            "positive_current_is": self.get_positive_current_is(),
            "object_sensor_type": self.get_object_sensor_type(),
            "output_stage_enable": self.get_output_stage_enable()
        }
        return settings


if __name__ == "__main__":
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    mc = MeerstetterTEC()
    mc.connect_serial_port(port="COM9", instance=1)

    firmware_identification_string = mc.get_firmware_identification_string()
    logging.info(
        f"firmware_identification_string : "
        f"{firmware_identification_string} ; "
        f"type {type(firmware_identification_string)}\n"
    )

    logging.info(f"device_type : {mc.get_device_type()} ; type {type(mc.get_device_type())}\n")

    logging.info(f"temperature : {mc.get_temperature()} ; type {type(mc.get_temperature())}\n")

    filepath_ = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "mecom_tec/lookup_table/csv/LookupTable Sine ramp_0.1_degC_per_sec.csv"
    )
    mc.download_lookup_table(filepath=filepath_)

    mc.set_proportional_gain(prop_gain=50.0)
    logging.info(f"proportional_gain : {mc.get_proportional_gain()} ; type {type(mc.get_proportional_gain())}\n")

    mc.set_proportional_gain(prop_gain=60.0)
    logging.info(f"proportional_gain : {mc.get_proportional_gain()} ; type {type(mc.get_proportional_gain())}\n")

    mc.set_integration_time(int_time_sec=40.0)
    logging.info(f"integration_time : {mc.get_integration_time()} ; type {type(mc.get_integration_time())}\n")

    mc.set_integration_time(int_time_sec=45.0)
    logging.info(f"integration_time : {mc.get_integration_time()} ; type {type(mc.get_integration_time())}\n")

    mc.set_differential_time(diff_time_sec=1.0)
    logging.info(f"differential_time : {mc.get_differential_time()} ; type {type(mc.get_differential_time())}\n")

    mc.set_differential_time(diff_time_sec=0.0)
    logging.info(f"differential_time : {mc.get_differential_time()} ; type {type(mc.get_differential_time())}\n")

    logging.info(f"part_damping : {mc.get_part_damping()} ; type {type(mc.get_part_damping())}\n")

    mc.tear()
