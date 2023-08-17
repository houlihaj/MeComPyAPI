import os
import logging
import time
import statistics
from enum import Enum
from typing import Tuple, List, Optional

from mecompyapi.mecom_core.mecom_query_set import MeComQuerySet
from mecompyapi.mecom_core.mecom_basic_cmd import MeComBasicCmd
from mecompyapi.mecom_core.com_command_exception import ComCommandException

from mecompyapi.phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort

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


class MeerstetterTEC(object):
    r"""
    Controlling TEC devices via serial.

    Definitions of command and error codes as stated in the "Mecom" protocol standard:

    ./meerstetter/pyMeCom/mecom/commands.py
    """
    def __init__(self, *args, **kwargs) -> None:
        self.phy_com = MeComPhySerialPort()
        self.mequery_set = None  # type: Optional[MeComQuerySet]
        self.mecom_basic_cmd = None  # type: Optional[MeComBasicCmd]
        self.mecom_lut_cmd = None  # type: Optional[LutCmd]
        self.address = None  # type: Optional[int]
        self.instance = None  # type: Optional[int]

    def connect(self, port: str = "COM9", address: int = 2, instance: int = 1):
        """
        Connects to a serial port. On Windows, these are typically 'COMX' where X is the number of the port. In Linux,
        they are often /dev/ttyXXXY where XXX usually indicates if it is a serial or USB port, and Y indicates the
        number. E.g. /dev/ttyUSB0 on Linux and 'COM7' on Windows

        :param port: Port, as described in description
        :type port: str
        :param address:
        :type address: int
        :param instance:
        :type instance: int
        :return: None
        """
        self.phy_com.connect(port_name=port)
        mequery_set = MeComQuerySet(phy_com=self.phy_com)
        self.mecom_basic_cmd = MeComBasicCmd(mequery_set=mequery_set)
        self.mecom_lut_cmd = LutCmd(mecom_query_set=mequery_set)
        self.address = address
        self.instance = instance

    def tear(self):
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.
        """
        self.phy_com.tear()

    def reset(self) -> None:
        """
        Resets the device after an error has occurred.

        :return: None
        """
        self.mecom_basic_cmd.reset_device(address=self.address, channel=self.instance)

    def get_id(self) -> str:
        """
        Query the Identification String of the device.

        :return: The identification string for the device. The string is comma separated and contains
            the follow components in order: Make, Model, Serial Number, Hardware Version, and Firmware
            Version.
        :rtype: str
        """
        model = self.get_device_type()
        sn = self.get_serial_number()
        hw = self.get_hardware_version()
        fw = self.get_firmware_version()
        identity = f"Meerstetter,TEC{model},{sn},{hw},{fw}"
        return identity

    def get_device_type(self) -> int:
        """
        Query the device type (Ex. 1090, 1091, 1092, etc.).

        :return: the TEC controller device type identification
        :rtype: int
        """
        logging.debug(f"get device type for channel {self.instance}")
        device_type = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=100,
                                                           instance=self.instance)
        return device_type

    def get_hardware_version(self) -> int:
        """
        Query the hardware version from the device.

        :return: The hardware version of the device.
        :rtype: int
        """
        logging.debug(f"get hardware version for channel {self.instance}")
        hardware_version = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=101,
                                                                instance=self.instance)
        return hardware_version

    def get_serial_number(self) -> int:
        """
        Query the serial number of the device.

        :return: The serial number of the device.
        :rtype: int
        """
        logging.debug(f"get serial number for channel {self.instance}")
        serial_number = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=102,
                                                             instance=self.instance)
        return serial_number

    def get_firmware_version(self) -> int:
        """
        Query the firmware version of the device.

        :return: The firmware version of the device.
        :rtype: int
        """
        logging.debug(f"get firmware version for channel {self.instance}")
        firmware_version = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=103,
                                                                instance=self.instance)
        return firmware_version

    def get_device_status(self) -> DeviceStatus:
        """
        Query the status of the device.

        :return: the active status of the TEC controller
        :rtype: DeviceStatus
        """
        logging.debug(f"get device status for channel {self.instance}")
        status_id_int = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=104,
                                                             instance=self.instance)
        status_id = DeviceStatus(status_id_int)
        return status_id

    def get_temperature(self) -> float:
        """
        Get object temperature of channel to desired value.

        :return: The object temperature in units of degrees Celsius (degC).
        :rtype: float
        """
        logging.debug(f"get object temperature for channel {self.instance}")
        object_temperature = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=1000,
                                                                  instance=self.instance)
        return object_temperature

    def get_setpoint_temperature(self) -> float:
        """
        Get the setpoint temperature from the TEC controller

        :return: the setpoint temperature from the TEC controller
        :rtype: float
        """
        logging.debug(f"get the setpoint temperature for channel {self.instance}")
        setpoint = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=1010,
                                                        instance=self.instance)
        return setpoint

    def get_tec_current(self) -> float:
        """
        Get the actual output current.

        :return: The output current in units of Amps (A).
        :rtype: float
        """
        logging.debug(f"get output current for channel {self.instance}")
        output_current = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=1020,
                                                              instance=self.instance)
        return output_current

    def get_tec_voltage(self) -> float:
        """
        Get the actual output voltage.

        :return: The output voltage in units of Volts (V).
        :rtype: float
        """
        logging.debug(f"get output voltage for channel {self.instance}")
        output_voltage = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=1021,
                                                              instance=self.instance)
        return output_voltage

    def get_device_temperature(self) -> float:
        """
        Get the temperature of the TEC controller device.

        :return: The TEC controller temperature in units of degrees Celsius (degC).
        :rtype: float
        """
        logging.debug(f"get the device temperature for channel {self.instance}")
        device_temp = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=1063,
                                                           instance=self.instance)
        return device_temp

    def is_temperature_stable(self) -> bool:
        """
        Check to see if the temperature is stable.

        :return: True if the temperature is stable, False otherwise
        :rtype: bool
        """
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=1200,
                                                    instance=self.instance)
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
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=2000,
                                             instance=self.instance, value=input_selection.value)

    def get_input_selection(self) -> ControlInputSelection:
        """
        Get the output control input selection.

        :return: the output control input selection for the TEC controller
        :rtype: ControlInputSelection
        """
        logging.debug(f"get the input selection for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=2000,
                                                    instance=self.instance)
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
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=2010,
                                             instance=self.instance, value=output_stage_enable.value)

    def get_output_stage_enable(self) -> OutputStageEnable:
        """
        Get the output stage enable used by the TEC controller.

        :return: the output stage enable used by the TEC controller
        :rtype: OutputStageEnable
        """
        logging.debug(f"get the output stage enable for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=2010,
                                                    instance=self.instance)
        return OutputStageEnable(int(resp))

    def set_current_limitation(self, current_limit_amps: float) -> None:
        """
        Set the limiting drive current in units of Amps.

        :param current_limit_amps: the limiting drive current value in units of Amps.
        :type current_limit_amps: float
        :return: None
        """
        logging.debug(f"set current limitation for channel {self.instance} to {float(current_limit_amps)} Amps")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=2030,
                                             instance=self.instance, value=float(current_limit_amps))

    def get_current_limitation(self) -> float:
        """
        Get the limiting drive current in units of Amps.

        :return: the limiting drive current for the TEC controller in units of Amps
        :rtype: float
        """
        logging.debug(f"get the current limitation for channel {self.instance}")
        current_limit = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=2030,
                                                             instance=self.instance)
        return current_limit

    def set_voltage_limitation(self, voltage_limit_volts: float) -> None:
        """
        Set the limiting drive voltage in units of Volts.

        :param voltage_limit_volts: the limiting drive current value in units of Volts.
        :type voltage_limit_volts: float
        :return: None
        """
        logging.debug(f"set voltage limitation for channel {self.instance} to {float(voltage_limit_volts)} Volts")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=2031,
                                             instance=self.instance, value=float(voltage_limit_volts))

    def get_voltage_limitation(self) -> float:
        """
        Get the limiting drive voltage in units of Volts.

        :return: the limiting drive voltage for the TEC controller in units of Volts
        :rtype: float
        """
        logging.debug(f"get the voltage limitation for channel {self.instance}")

        voltage_limit = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=2031,
                                                             instance=self.instance)
        return voltage_limit

    def set_current_error_threshold(self, threshold_amps: float) -> None:
        """
        Set the current error threshold in units of Amps.

        :param threshold_amps: the current error threshold in units of Amps
        :type threshold_amps: float
        :return: none
        """
        logging.debug(f"set current error threshold for channel {self.instance} to {float(threshold_amps)} Amps")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=2032,
                                             instance=self.instance, value=float(threshold_amps))

    def get_current_error_threshold(self) -> float:
        """
        Get the current error threshold.

        :return: the current error threshold in units of Amps
        :rtype: float
        """
        logging.debug(f"get the current error threshold for channel {self.instance}")
        curr_threshold = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=2032,
                                                              instance=self.instance)
        return curr_threshold

    def set_voltage_error_threshold(self, threshold_volts: float) -> None:
        """
        Set the voltage error threshold in units of Volts.

        :param threshold_volts: the voltage error threshold in units of Volts
        :type threshold_volts: float
        :return: none
        """
        logging.debug(
            f"set voltage error threshold for channel {self.instance} to {float(threshold_volts)} Volts")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=2033,
                                             instance=self.instance, value=float(threshold_volts))

    def get_voltage_error_threshold(self) -> float:
        """
        Get the voltage error threshold.

        :return: the voltage error threshold in units of Volts
        :rtype: float
        """
        logging.debug(f"get the voltage error threshold for channel {self.instance}")
        volt_threshold = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=2033,
                                                              instance=self.instance)
        return volt_threshold

    def set_general_operating_mode(self, operating_mode: GeneralOperatingMode) -> None:
        """
        Set the operating mode of the TEC controller.

        :param operating_mode: the operating mode of the TEC controller
        :type operating_mode: GeneralOperatingMode
        :return: None
        """
        logging.debug(f"set the general operating mode for channel {self.instance} to {operating_mode}")
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=2040,
                                             instance=self.instance, value=operating_mode.value)

    def get_general_operating_mode(self) -> GeneralOperatingMode:
        """
        Get the operating mode of the TEC controller.

        :return: the operating mode of the TEC controller
        :rtype: GeneralOperatingMode
        """
        logging.debug(f"get the general operating mode for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=2040,
                                                    instance=self.instance)
        operating_mode = GeneralOperatingMode(int(resp))
        return operating_mode

    def get_base_baud_rate(self) -> int:
        """
        Get the UART base baud rate.

        :return: the UART base baud rate
        :rtype: int
        """
        logging.debug(f"get the UART base baud rate for channel {self.instance}")
        baud_rate = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=2050,
                                                         instance=self.instance)
        return baud_rate

    def get_device_address(self) -> int:
        """
        Query the device address.

        :return: the device address
        :rtype: int
        """
        logging.debug(f"get the device address for channel {self.instance}")
        device_address = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=2051,
                                                              instance=self.instance)
        return device_address

    def get_uart_response_delay(self) -> float:
        """
        Get the UART response delay for the controller.

        :return: the UART response delay in units of microseconds (us)
        :rtype: float
        """
        logging.debug(f"get the UART response delay for channel {self.instance}")
        delay_us = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=2052,
                                                        instance=self.instance)
        return delay_us

    def get_firmware_identification_string(self) -> str:
        """
        Query the Firmware Identification String of the device.

        :return: The firmware identification string of the device.
        :rtype: str
        """
        identify = self.mecom_basic_cmd.get_ident_string(address=self.address, channel=self.instance)
        return identify

    def set_temperature(self, temp_degc: float) -> None:
        """
        Set object temperature of channel to desired value in units of degrees Celsius.

        :param temp_degc: The desired object temperature value in units of degrees Celsius.
            The controller will set the object to this temperature value.
        :type temp_degc: float
        :return: None
        """
        logging.debug(f"set object temperature for channel {self.instance} to {temp_degc} C")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=3000,
                                             instance=self.instance, value=float(temp_degc))

    def set_coarse_temperature_ramp(self, temp_ramp_degc_per_sec: float) -> None:
        """
        Set the coarse temperature ramp of the TEC controller to desired value in
        units of degrees Celsius per second.

        :param temp_ramp_degc_per_sec: the coarse temperature ramp value in units of degrees Celsius per second.
        :type temp_ramp_degc_per_sec: float
        :return: None
        """
        logging.debug(
            f"set coarse temperature ramp for channel {self.instance} to {float(temp_ramp_degc_per_sec)} degC/second")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=3003,
                                             instance=self.instance, value=float(temp_ramp_degc_per_sec))

    def get_coarse_temperature_ramp(self) -> float:
        """
        Get the coarse temperature ramp setting.

        :return: the coarse temperature ramp setting for the controller
            in units of degC/second
        :rtype: float
        """
        logging.debug(f"get the coarse temperature ramp for channel {self.instance}")
        temp_ramp = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=3003,
                                                         instance=self.instance)
        return temp_ramp

    def set_proportional_gain(self, prop_gain: float) -> None:
        """
        Set the proportional gain (Kp) for the PID controller.

        :param prop_gain: the proportional gain (Kp)
        :type prop_gain: float
        :return: None
        """
        logging.debug(f"set the proportional gain (Kp) for channel {self.instance} to {float(prop_gain)}")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=3010,
                                             instance=self.instance, value=float(prop_gain))

    def get_proportional_gain(self) -> float:
        """
        Get the proportional gain (Kp) for the PID controller.

        :return: the proportional gain (Kp)
        :rtype: float
        """
        logging.debug(f"get the proportional gain (Kp) for channel {self.instance}")
        proportional_gain = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=3010,
                                                                 instance=self.instance)
        return proportional_gain

    def set_integration_time(self, int_time_sec: float) -> None:
        """
        Set the integration time (Ti) for the PID controller.

        :param int_time_sec: the integration time (Ti) in units of seconds
        :type int_time_sec: float
        :return: None
        """
        logging.debug(f"set the integration time (Ti) for channel {self.instance} to {float(int_time_sec)} seconds")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=3011,
                                             instance=self.instance, value=float(int_time_sec))

    def get_integration_time(self) -> float:
        """
        Get the integration time (Ti) for the PID controller.

        :return: the integration time (Ti) in units of seconds
        :rtype: float
        """
        logging.debug(f"get the integration time (Ti) for channel {self.instance}")
        integration_time = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=3011,
                                                                instance=self.instance)
        return integration_time

    def set_differential_time(self, diff_time_sec: float) -> None:
        """
        Set the differential time (Td) for the PID controller.

        :param diff_time_sec: the differential time (Td) in units of seconds
        :type diff_time_sec: float
        :return: None
        """
        logging.debug(f"set the differential time (Td) for channel {self.instance} to {float(diff_time_sec)} seconds")
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=3012,
                                             instance=self.instance, value=float(diff_time_sec))

    def get_differential_time(self) -> float:
        """
        Get the differential time (Td) for the PID controller.

        :return: the differential time (Td) in units of seconds
        :rtype: float
        """
        logging.debug(f"get the differential time (Td) for channel {self.instance}")
        differential_time = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=3012,
                                                                 instance=self.instance)
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
        self.mecom_basic_cmd.set_float_value(address=self.address, parameter_id=3013,
                                             instance=self.instance, value=float(part_damping))

    def get_part_damping(self) -> float:
        """
        Get D Part Damping PT1 for the PID controller. The value “D Part Damping PT1” is damping the resulting value of
        the derivative term. It may be useful for very slow thermal models which result in high Td times.

        :return: D Part Damping PT1 value
        :rtype: float
        """
        logging.debug(f"get D Part Damping PT1 for channel {self.instance}")
        part_damping = self.mecom_basic_cmd.get_float_value(address=self.address, parameter_id=3013,
                                                            instance=self.instance)
        return part_damping

    def set_thermal_regulation_mode(self, regulation_mode: ThermalRegulationMode) -> None:
        """
        Set the thermal regulation mode used by the TEC controller

        :param regulation_mode: the operating mode of the TEC controller
        :type regulation_mode: ThermalRegulationMode
        :return: None
        """
        logging.debug(f"set the thermal regulation mode for channel {self.instance} to {regulation_mode}")
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=3020,
                                             instance=self.instance, value=regulation_mode.value)

    def get_thermal_regulation_mode(self) -> ThermalRegulationMode:
        """
        Get the thermal regulation mode used by the TEC controller

        :return: the thermal regulation mode
        :rtype: ThermalRegulationMode
        """
        logging.debug(f"get the thermal regulation mode for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=3020,
                                                    instance=self.instance)
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
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=3034,
                                             instance=self.instance, value=positive_current_is.value)

    def get_positive_current_is(self) -> PositiveCurrentIs:
        """
        Check to see if positive current is "cooling" or "heating"; meaning,
        is the TEC controller causing the TEC to cool or heat the object.

        :return: returns whether positive current flow causes cooling or
            heating of the TEC
        :rtype: PositiveCurrentIs
        """
        logging.debug(f"get the positive current is for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=3034,
                                                    instance=self.instance)
        return PositiveCurrentIs(int(resp))

    def set_object_sensor_type(self, sensor_type: ObjectSensorType) -> None:
        """
        Set the object sensor type used by the TEC controller

        :param sensor_type: the type of temperature sensor being used to provide feedback
        :type sensor_type: ObjectSensorType
        :return: None
        """
        logging.debug(f"set the object sensor type for channel {self.instance} to {sensor_type}")
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=4034,
                                             instance=self.instance, value=sensor_type.value)

    def get_object_sensor_type(self) -> ObjectSensorType:
        """
        Get the object sensor type being used to provide temperature feedback to the
        TEC controller.

        :return: the type of temperature sensor being used to provide feedback
        :rtype: ObjectSensorType
        """
        logging.debug(f"get the object sensor type for channel {self.instance}")
        resp = self.mecom_basic_cmd.get_int32_value(address=self.address, parameter_id=4034,
                                                    instance=self.instance)
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
                print(f"LutCmd status : {status}")
                if status == LutStatus.NO_INIT or status == LutStatus.ANALYZING:
                    timeout += 1
                    if timeout < 50:
                        time.sleep(0.010)
                    else:
                        raise LutException("Timeout while trying to get Lookup Table status!")
                else:
                    break
            lut_table_status = self.mecom_lut_cmd.get_status(address=self.address, instance=self.instance)
            print(f"Lookup Table Status (52002): {lut_table_status}")
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

    def _set_enable(self, enable: bool = True) -> None:
        """
        Enable or disable control loop.

        :param enable:
        :type enable: bool
        :return: None
        """
        value, description = (1, "on") if enable else (0, "off")
        logging.debug(f"set loop for channel {self.instance} to {description}")
        self.mecom_basic_cmd.set_int32_value(address=self.address, parameter_id=2010,
                                             instance=self.instance, value=value)

    def enable(self) -> None:
        """
        Enable or disable control loop.

        :return:
        :rtype: None
        """
        self._set_enable(True)

    def disable(self) -> None:
        """
        Enable or disable control loop.

        :return:
        :rtype: None
        """
        self._set_enable(False)

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

    def set_and_stabilize_tec_temperature(self, temperature: float = 30.0,
                                          threshold_deg_c: float = 0.1) -> Tuple[float, List[float]]:
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
            "object_sensor_type": self.get_object_sensor_type()
        }
        return settings


if __name__ == "__main__":
    mc = MeerstetterTEC()
    mc.connect(port="COM9", address=2, instance=1)

    firmware_identification_string = mc.get_firmware_identification_string()
    print(f"firmware_identification_string : {firmware_identification_string} ; type {type(firmware_identification_string)}")
    print("\n", end="")

    print(f"device_type : {mc.get_device_type()} ; type {type(mc.get_device_type())}")
    print("\n", end="")

    print(f"temperature : {mc.get_temperature()} ; type {type(mc.get_temperature())}")
    print("\n", end="")

    filepath_ = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "mecom_tec/lookup_table/csv/LookupTable Sine ramp_0.1_degC_per_sec.csv")
    mc.download_lookup_table(filepath=filepath_)
    print("\n", end="")

    mc.set_proportional_gain(prop_gain=50.0)
    print(f"proportional_gain : {mc.get_proportional_gain()} ; type {type(mc.get_proportional_gain())}")
    print("\n", end="")

    mc.set_proportional_gain(prop_gain=60.0)
    print(f"proportional_gain : {mc.get_proportional_gain()} ; type {type(mc.get_proportional_gain())}")
    print("\n", end="")

    mc.set_integration_time(int_time_sec=40.0)
    print(f"integration_time : {mc.get_integration_time()} ; type {type(mc.get_integration_time())}")
    print("\n", end="")

    mc.set_integration_time(int_time_sec=45.0)
    print(f"integration_time : {mc.get_integration_time()} ; type {type(mc.get_integration_time())}")
    print("\n", end="")

    mc.set_differential_time(diff_time_sec=1.0)
    print(f"differential_time : {mc.get_differential_time()} ; type {type(mc.get_differential_time())}")
    print("\n", end="")

    mc.set_differential_time(diff_time_sec=0.0)
    print(f"differential_time : {mc.get_differential_time()} ; type {type(mc.get_differential_time())}")
    print("\n", end="")

    print(f"part_damping : {mc.get_part_damping()} ; type {type(mc.get_part_damping())}")
    print("\n", end="")

    mc.tear()
