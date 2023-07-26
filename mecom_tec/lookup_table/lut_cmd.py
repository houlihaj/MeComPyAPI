import time
import csv
from typing import List

from PyCRC.CRCCCITT import CRCCCITT

from lut_record import LutRecord
from lut_status import LutStatus
from lut_exception import LutException
from lut_constants import *

# from ..mecom import MeCom
import instruments.meerstetter.pyMeCom.mecom.mecom


class LutCmd(object):
    """
    Lookup Table commands (only supported for TEC Controllers)
    Please take a look at the TEC Controller communication protocol document for more information.
    """
    def __init__(self, mecom_instance: instruments.meerstetter.pyMeCom.mecom.mecom.MeCom):
        self.mecom = mecom_instance
        # self.lut_cmd(me_query_set=)
        # raise NotImplementedError

    def lut_cmd(self, me_query_set) -> None:
        """
        Initializes a new instance of LutG1Cmd.

        :param me_query_set: Reference to the communication interface.
        :type me_query_set:
        :return: None
        """
        raise NotImplementedError

    def download_lookup_table(self, address: bytes, filepath: str) -> None:
        """
        Downloads a lookup table file (*.csv) to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: bytes
        :param filepath: Path of the lookup table file.
        :type filepath: str
        :return: None
        """
        # Get all records from the CSV file, enumerate them and put them in a list
        records: List[LutRecord] = self._parse_lut_into_list(reader=filepath)

        print("Pause...")

        # Calculate the CRC over all records in the list and add it to Field2 of the EOF record
        self._add_crc_to_table(records=records)

        print("Pause 1...")

        # Split the list into separate lists holding 32 entries each
        lists = self._split_list(list_input=records, max_list_size=32)

        print("Pause 2...")

        # Create a payload for each list of records and send them to the device
        for list_ in lists:
            index_of_list_ = lists.index(list_)
            # Check whether the device is ready to receive the next page
            self._download_page(address=address, list_lut_record=list_, page_offset=index_of_list_)

        # Send the signal to start analyzing the lookup table on the device
        self._start_analyze_and_wait(address=address)

    def start_analyze_lut(self, address: bytes) -> bool:
        """
        This query is used to analyze the lookup table.
        It has to be sent after a lookup table has been completely downloaded onto the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: bytes
        :return: True if the query was successful, False if Device MeComPacket was denied
        :return: bool
        """
        try:
            # MeComPacket answers to the query:
            # 0 = Idle
            # 1 = Erasing or Writing (Sent Data is ignored)
            # 2 = New Data accepted
            # 3 = Error
            status = self.mecom.do_analyze_lut()
            return status == LUT_FLASH_STATUS_IDLE
        except LutException as e:
            raise LutException(f"Lookup table test failed: Address: {address}; Detail: {e}")

    # def get_status(self, address: bytes, instance: bytes) -> LutStatus:
    #     """
    #     Get lookup table status by retrieving the parameter value 52002.
    #
    #     :param address: Device Address. Use null to use the DefaultDeviceAddress
    #         defined on MeComQuerySet.
    #     :type address: bytes
    #     :param instance: Device Instance/Channel.
    #     :type instance: bytes
    #     :return: LutStatus Enum value
    #     :rtype: LutStatus
    #     """
    #     raise NotImplementedError
    #
    # def start_lookup_table(self, address: bytes, instance: bytes) -> None:
    #     """
    #     Starts the lookup table that is currently stored on the device.
    #
    #     :param address: Device Address. Use null to use the DefaultDeviceAddress
    #         defined on MeComQuerySet.
    #     :type address: bytes
    #     :param instance: Device Instance/Channel.
    #     :type instance: bytes
    #     :return: None
    #     """
    #     # Initiate the Lookup Table Start process by writing 1 to ParID 52000
    #     logging.debug(f"start the lookup table for channel {self.channel}")
    #     success = self.session().set_parameter(parameter_name="Lookup Table Start", value=1,
    #                                            address=self.address, parameter_instance=self.channel)
    #     if not success:
    #         raise LutException("[EXCEPTION] start_lookup_table() was unsuccessful...")
    #
    # def stop_lookup_table(self, address: bytes, instance: bytes) -> None:
    #     """
    #     Cancels the active lookup table progress process.
    #
    #     :param address: Device Address. Use null to use the DefaultDeviceAddress
    #         defined on MeComQuerySet.
    #     :type address: bytes
    #     :param instance: Device Instance/Channel.
    #     :type instance: bytes
    #     :return: None
    #     """
    #     # Stop the Lookup Table process by writing 1 to ParID 52001
    #     logging.debug(f"stop the lookup table for channel {self.channel}")
    #     success = self.session().set_parameter(parameter_name="Lookup Table Stop", value=1,
    #                                            address=self.address, parameter_instance=self.channel)
    #     if not success:
    #         raise LutException("[EXCEPTION] stop_lookup_table() was unsuccessful...")
    #
    # def get_current_table_line(self, address: bytes, instance: bytes) -> int:
    #     """
    #     Get the number of the currently executed Data Table line.
    #     Only valid if the current "Lookup Table Status" is "Executing...".
    #
    #     :param address: Device Address. Use null to use the DefaultDeviceAddress
    #         defined on MeComQuerySet.
    #     :type address: bytes
    #     :param instance: Device Instance/Channel.
    #     :type instance: bytes
    #     :return: None
    #     :rtype: int
    #     """
    #     logging.debug(f"get the lookup table status current table line for channel {self.channel}")
    #     resp = self.session().get_parameter(parameter_name="Lookup Table Status Current Table Line",
    #                                         address=self.address)
    #     return int(resp)
    #
    # def set_lookup_table_id(self, address: bytes, instance: bytes, table_id: int) -> None:
    #     """
    #     Select the Lookup Table part to be executed by passing the Table ID
    #     defined in the Data Table.
    #
    #     :param address: Device Address. Use null to use the DefaultDeviceAddress
    #         defined on MeComQuerySet.
    #     :type address: bytes
    #     :param instance: Device Instance/Channel.
    #     :type instance: bytes
    #     :param table_id: Lookup Table ID to be executed.
    #     :type table_id: int
    #     :return: None
    #     """
    #     logging.debug(f"set the lookup table id selection for channel {self.channel}")
    #     self.session().set_parameter(value=table_id, parameter_name="Lookup Table ID Selection",
    #                                  address=self.address)
    #
    # def set_number_of_repetitions(self, address: bytes, instance: bytes, nr_of_repetitions: int) -> None:
    #     """
    #     Set the number of executions of the "REPEAT_MARK" elements.
    #     See the Lookup Table definitions for more information about these elements.
    #
    #     :param address: Device Address. Use null to use the DefaultDeviceAddress
    #         defined on MeComQuerySet.
    #     :type address: bytes
    #     :param instance: Device Instance/Channel.
    #     :type instance: bytes
    #     :param nr_of_repetitions: Amount of repetitions. Value Range: 0 ... 100'000.
    #     :type nr_of_repetitions: int
    #     :return: None
    #     """
    #     logging.debug(f"set the number of repetitions for channel {self.channel}")
    #     self.session().set_parameter(value=repetitions, parameter_name="Number Of Repetitions",
    #                                  address=self.address)

    def _download_page(self, address: bytes, list_lut_record: List[LutRecord], page_offset: int) -> None:
        """
        Downloads a page of the lookup table to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: bytes
        :param list_lut_record: List of LutG1Records for the page.
        :type list_lut_record: List[LutRecord]
        :param page_offset: The offset of the page.
        :type page_offset: int
        :return: None
        """
        try:
            count = len(list_lut_record)
            lut_record_bytearray = bytearray(b"")
            for i in range(count):
                lut_record_bytearray.extend(list_lut_record[i].get_bytes())

            # Create MeFrame with Payload
            lt = self.mecom.program_lut(page_offset=page_offset, lut_record_bytearray=lut_record_bytearray)

            timeout: int = 0
            while True:
                status = lt.RESPONSE.PAYLOAD
                if status != LUT_FLASH_STATUS_DATA_ACCEPTED:
                    # Manage device busy
                    timeout += 1
                    if timeout < 50:
                        time.sleep(0.010)
                    else:
                        LutException(f"Device Busy while sending Lookup Table")
                else:
                    break

        except LutException as e:
            raise LutException(f"DownloadPage failed: Address {address}; Detail: {e}")

    def _start_analyze_and_wait(self, address: bytes) -> None:
        """


        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: bytes
        :return: None
        """
        timeout: int = 0
        while True:
            # Send LUT analyze query
            successfully_started = self.start_analyze_lut(address=address)
            if successfully_started is not True:
                timeout += 1
                if timeout < 50:
                    time.sleep(0.010)
                else:
                    LutException(f"Device Busy while trying to analyze Lookup Table")
            else:
                break

    def _add_crc_to_table(self, records: List[LutRecord]) -> None:
        """


        :param records:
        :type records: List[LutRecord]
        :return: None
        """        
        old_crc = 0xFFFFFFFF
        for record in records:  # All Records without the EOF Record
            if record.instruction != LUT_EOF_INSTR:
                # Calculate the CRC over all records
                old_crc = self._calc_crc(crc=old_crc, record=record)
            else:
                # Add the CRC to the last record (EOF record) as Field2 attribute
                record.field_to_int = int(old_crc)

    def _calc_crc(self, crc: int, record: LutRecord) -> int:
        """


        :param crc: CRC to use as base for the calculation.
        :type crc: int
        :param record:
        :type record: LutRecord
        :return:
        :rtype: int
        """
        # Split the whole record (64-bit) into two 32-bit int parts
        split_record: List[int] = record.get_int_array()
        
        # First calculate the CRC with Field2
        crc = self._crc32_calc(crc=crc, data=int(split_record[0]))
        
        # Then, calculate the CRC with the previous CRC and Instruction + Field1 together
        crc = self._crc32_calc(crc=crc, data=int(split_record[1]))
        
        return crc

    def _crc32_calc(self, crc: int, data: int) -> int:
        """
        Generate CRC32 Checksum.

        :param crc: CRC to use as base for the calculation.
        :type crc: int
        :param data: Data to combine with previous CRC.
        :type data: int
        :return:
        :rtype: int
        """
        crc ^= data
        for i in range(32):
            if (crc & 0x80000000) != 0:
                crc = (crc << 1) ^ 0x04C11DB7  # Polynomial used in STM32
            else:
                crc <<= 1
        return crc

    def _split_list(self, list_input: List[LutRecord], max_list_size) -> List[List[LutRecord]]:
        """
        Split a list into multiple lists which only hold a specified amount of elements.

        :param list_input: List that shall be split.
        :type list_input: List[LutRecord]
        :param max_list_size: Maximum amount of elements in the lists.
        :type max_list_size: int
        :return: List holding the split up lists.
        :rtype: List[List[LutRecord]]
        """
        list_ = []
        count = len(list_input)
        for i in range(0, count, max_list_size):
            list_.append(list_input[i:i + min(max_list_size, count - i)])
        return list_

    def _parse_lut_into_list(self, reader) -> List[LutRecord]:
        """

        :param reader:
        :type reader:
        :return:
        :rtype: List[LutRecord]
        """
        with open(reader) as f:
            # splits by line, but keeps the \n
            lines = list(f)
        print(lines)

        list_ = []
        line_count = 0
        for line in lines:
            if line_count == 0:
                if "Instruction;Field 1;Field 2" not in lines[0]:
                    raise LutException(f"The Title of the .csv file must be 'Instruction;Field 1;Field 2'")
                line_count += 1
            elif "EOF" in line:
                break
            else:
                record: LutRecord = self._enumerate_lut(line=line, line_count=line_count)
                list_.append(record)
                line_count += 1

        print(list_)

        return list_

    def _enumerate_lut(self, line: str, line_count: int) -> LutRecord:
        """

        :param line:
        :type line: str
        :param line_count:
        :type line_count: int
        :return:
        :rtype: LutRecord
        """
        buffer = line.split(";")
        instruction = buffer[0]
        field1 = buffer[1]
        field2 = buffer[2]
        
        record = LutRecord()
        record.Field1(value=0).set()
        
        try:
            if instruction == "TABLE_INFO":
                record.instruction = LUT_TABLE_INFO_INSTR
                if field1 == "START":
                    record.Field1(value=LUT_TABLE_INFO_F1_START).set()
                elif field1 == "END":
                    record.Field1(value=LUT_TABLE_INFO_F1_END).set()
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
                record.field_to_int = int(field2)
            
            elif instruction == "SIN_RAMP_TO":
                record.instruction = LUT_SIN_RAMP_TO_INSTR
                if field1 == "FROM_ACT":
                    record.Field1(value=LUT_SIN_RAMP_TO_F1_FROM_ACT).set()
                elif field1 == "FROM_NOM":
                    record.Field1(value=LUT_SIN_RAMP_TO_F1_FROM_NOM).set()
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
                record.field_to_float = float(field2)
            
            elif instruction == "REPEAT_MARK":
                record.instruction = LUT_REPEAT_MARK_INSTR
                if field1 == "START":
                    record.Field1(value=LUT_REPEAT_MARK_F1_START).set()
                elif field1 == "END":
                    record.Field1(value=LUT_REPEAT_MARK_F1_END).set()
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
             
            elif instruction == "LIN_RAMP_TIME":
                record.instruction = LUT_LIN_RAMP_TIME_INSTR
                f1_temp = int(field1)
                if 10 >= f1_temp >= 16_777_216:
                    record.Field1(value=f1_temp).set()
                record.field_to_float = float(field2)
            
            elif instruction == "STATUS":
                record.instruction = LUT_STATUS_INSTR
                if field1 == "DISABLE":
                    record.Field1(value=LUT_STATUS_F1_DISABLE).set()
                elif field1 == "ENABLE":
                    record.Field1(value=LUT_STATUS_F1_ENABLE).set()
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
            
            elif instruction == "WAIT":
                record.instruction = LUT_WAIT_INSTR
                if field1 == "FOREVER":
                    record.Field1(value=LUT_WAIT_F1_FOREVER).set()
                elif field1 == "TIME":
                    record.Field1(value=LUT_WAIT_F1_TIME).set()
                    f2_temp = int(field2)
                    if f2_temp >= 0:
                        record.field_to_int = f2_temp
            
            elif instruction == "SET_FLOAT":
                record.instruction = LUT_SET_FLOAT_INSTR
                f1temp_1 = int(field1)  # need to confirm operation
                if 0 <= f1temp_1 <= 16_777_216:
                    record.Field1(value=f1temp_1).set()  # need to confirm operation
                record.field_to_int = int(field2)  # need to confirm operation
            
            elif instruction == "SET_INT":
                record.instruction = LUT_SET_INT_INSTR
                f1temp_2 = int(field1)  # need to confirm operation
                if 0 <= f1temp_2 <= 16_777_216:
                    record.Field1(value=f1temp_2).set()  # need to confirm operation
                record.field_to_int = int(field2)  # need to confirm operation
                
            elif instruction == "TILL_TEMP_STABLE":
                record.instruction = LUT_WAIT_TILL_STABLE_INSTR
                
            elif instruction == "SET_TARGET_INST":
                record.instruction = LUT_CHANGE_TARGET_INST_INSTR
                record.field_to_int = int(field2)  # need to confirm operation
                
            elif instruction == "EOF":
                record.instruction = LUT_EOF_INSTR
                
            else:
                LutException(f"Error in Instruction Enumeration : {instruction}")
        
        except LutException as e:
            raise LutException("Error on line {have to implement}")  # need to fully implement
            
        finally:
            return record


if __name__ == "__main__":
    mecom = instruments.meerstetter.pyMeCom.mecom.mecom.MeCom(serialport="COM9", timeout=1)

    address_ = mecom.identify()

    serial_number_int = mecom.get_parameter(parameter_name="Serial Number", address=address_,
                                            parameter_instance=1)
    print(f"serial_number_int : {serial_number_int}")

    lut_cmd = LutCmd(mecom_instance=mecom)

    # records_ = lut_cmd._parse_lut_into_list(reader="LookupTable Sine ramp_0.1_degC_per_sec.csv")
    # print("Pause...")
    # lut_cmd._add_crc_to_table(records=records_)
    # print("Pause 2...")
    # print(lut_cmd._split_list(list_input=records_, max_list_size=32))
    # print("Done...")

    lut_cmd.download_lookup_table(address=address_, filepath="LookupTable Sine ramp_0.1_degC_per_sec.csv")
