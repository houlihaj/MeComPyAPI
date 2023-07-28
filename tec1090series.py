import logging
import datetime
import time
import statistics
from enum import Enum
from typing import Tuple, List, Dict, Optional
from serial import SerialException

from mecom_core.mecom_frame import MeComPacket
from mecom_core.mecom_query_set import MeComQuerySet
from mecom_core.mecom_var_convert import MeComVarConvert
from mecom_core.mecom_basic_cmd import MeComBasicCmd
from mecom_core.com_command_exception import ComCommandException

from phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort

from mecom_tec.lookup_table.lut_cmd import LutCmd
from mecom_tec.lookup_table.lut_status import LutStatus
from mecom_tec.lookup_table.lut_exception import LutException


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

        :param: Port, as described in description
        :type: str
        :param:
        :type: int
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

    def get_firmware_identification_string(self) -> str:
        """
        Query the Firmware Identification String of the device.

        :return: The firmware identification string of the device.
        :rtype: str
        """
        identify = self.mecom_basic_cmd.get_ident_string(address=self.address, channel=self.instance)
        return identify

    def download_lookup_table(self) -> None:
        """

        :return: None
        """
        filepath = "LookupTable Sine ramp_0.1_degC_per_sec.csv"  # Need to update with correct path

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

        :return: None
        """
        try:
            self.mecom_lut_cmd.start_lookup_table(address=self.address, instance=self.instance)
        except LutException as e:
            raise ComCommandException(f"start_lookup_table failed: Detail: {e}")

    def stop_lookup_table(self) -> None:
        """

        :return: None
        """
        try:
            self.mecom_lut_cmd.stop_lookup_table(address=self.address, instance=self.instance)
        except LutException as e:
            raise ComCommandException(f"stop_lookup_table failed: Detail: {e}")


if __name__ == "__main__":
    mc = MeerstetterTEC()
    mc.connect(port="COM9", address=2, instance=1)

    print(mc.get_firmware_identification_string())
    print(type(mc.get_firmware_identification_string()))
    print("\n", end="")

    print(mc.get_device_type())
    print(type(mc.get_device_type()))
    print("\n", end="")

    print(mc.get_temperature())
    print(type(mc.get_temperature()))
    print("\n", end="")

    mc.tear()
