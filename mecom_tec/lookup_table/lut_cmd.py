import time
from typing import List

from mecom_tec.lookup_table.lut_record import LutRecord
from mecom_tec.lookup_table.lut_status import LutStatus
from mecom_tec.lookup_table.lut_exception import LutException
from mecom_tec.lookup_table.lut_constants import *

from mecom_core.mecom_query_set import MeComQuerySet
from mecom_core.mecom_var_convert import MeComVarConvert
from mecom_core.mecom_frame import MeComPacket
from mecom_core.mecom_basic_cmd import MeComBasicCmd
from phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort


class LutCmd(object):
    """
    Lookup Table commands (only supported for TEC Controllers)
    Please take a look at the TEC Controller communication protocol document for more information.
    """
    def __init__(self, mecom_query_set: MeComQuerySet):
        """
        Initializes a new instance of LutG1Cmd.
        
        :param mecom_query_set: Reference to the communication interface.
        :type mecom_query_set: MeComQuerySet
        """
        self.mequery_set = mecom_query_set
        self.mecom_basic_cmd = MeComBasicCmd(mequery_set=mecom_query_set)

    def download_lookup_table(self, address: int, filepath: str) -> None:
        """
        Downloads a lookup table file (*.csv) to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param filepath: Path of the lookup table file.
        :type filepath: str
        :return: None
        """
        # Get all records from the CSV file, enumerate them and put them in a list
        records: List[LutRecord] = self._parse_lut_into_list(reader=filepath)

        # Calculate the CRC over all records in the list and add it to Field2 of the EOF record
        self._add_crc_to_table(records=records)

        # Split the list into separate lists holding 32 entries each
        lists = self._split_list(list_input=records, max_list_size=32)

        # Create a payload for each list of records and send them to the device
        for list_ in lists:
            index_of_list_ = lists.index(list_)
            # Check whether the device is ready to receive the next page
            self._download_page(address=address, list_lut_record=list_, page_offset=index_of_list_)

        # Send the signal to start analyzing the lookup table on the device
        self._start_analyze_and_wait(address=address)

    def start_analyze_lut(self, address: int) -> bool:
        """
        This query is used to analyze the lookup table.
        It has to be sent after a lookup table has been completely downloaded onto the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :return: True if the query was successful, False if Device MeComPacket was denied
        :return: bool
        """
        mecom_var_convert = MeComVarConvert()
        try:
            tx_frame = MeComPacket(control="#", address=address)
            tx_frame.payload = mecom_var_convert.add_string(tx_frame.payload, "?LT")
            tx_frame.payload = (
                mecom_var_convert.add_uint4(tx_frame.payload, 2)
            )  # 0 = Status Query, 1 = Program, 2 = Do Analyze
            rx_frame = self.mequery_set.query(tx_frame=tx_frame)
            
            # MeComPacket answers to the query:
            # 0 = Idle
            # 1 = Erasing or Writing (Sent Data is ignored)
            # 2 = New Data accepted
            # 3 = Error
            status = mecom_var_convert.read_uint4(rx_frame.payload)
            print(f"?LT Do Analyze Server Response : {status}")
            return status == LUT_FLASH_STATUS_IDLE
        except LutException as e:
            raise LutException(f"Lookup table test failed: Address: {address}; Detail: {e}")

    def get_lut_status_query(self, address: int) -> int:
        """

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :raises LutException:
        :return:
        :rtype: int
        """
        mecom_var_convert = MeComVarConvert()
        try:
            tx_frame = MeComPacket(control="#", address=address)
            tx_frame.payload = (
                mecom_var_convert.add_string(tx_frame.payload, "?LT")
            )  # Start payload with Lookup Table command, '?LT' is used for write and read
            tx_frame.payload = (
                mecom_var_convert.add_uint4(tx_frame.payload, 0)
            )  # 0 = Status Query, 1 = Program, 2 = Do Analyze

            rx_frame = self.mequery_set.set(tx_frame=tx_frame)
            status = mecom_var_convert.read_uint4(rx_frame.payload)
            return status
        except LutException as e:
            raise LutException(f"Get Lookup Table Status Query failed: Address: {address}; Detail: {e}")

    def get_status(self, address: int, instance: int) -> LutStatus:
        """
        Get lookup table status by retrieving the parameter value 52002.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param instance: Device Instance/Channel.
        :type instance: int
        :return: LutStatus Enum value
        :rtype: LutStatus
        """
        status = self.mecom_basic_cmd.get_int32_value(address=address, parameter_id=52002, instance=instance)
        return LutStatus(status)

    def start_lookup_table(self, address: int, instance: int) -> None:
        """
        Starts the lookup table that is currently stored on the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param instance: Device Instance/Channel.
        :type instance: int
        :return: None
        """
        # Initiate the Lookup Table Start process by writing 1 to ParID 52000
        self.mecom_basic_cmd.set_int32_value(address=address, parameter_id=52000, instance=instance, value=1)

    def stop_lookup_table(self, address: int, instance: int) -> None:
        """
        Cancels the active lookup table progress process.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param instance: Device Instance/Channel.
        :type instance: int
        :return: None
        """
        # Stop the Lookup Table process by writing 1 to ParID 52001
        self.mecom_basic_cmd.set_int32_value(address=address, parameter_id=52001, instance=instance, value=1)

    def get_current_table_line(self, address: int, instance: int) -> int:
        """
        Get the number of the currently executed Data Table line.
        Only valid if the current "Lookup Table Status" is "Executing...".

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param instance: Device Instance/Channel.
        :type instance: int
        :return: None
        :rtype: int
        """
        return self.mecom_basic_cmd.get_int32_value(address=address, parameter_id=52003, instance=instance)

    def set_lookup_table_id(self, address: int, instance: int, table_id: int) -> None:
        """
        Select the Lookup Table part to be executed by passing the Table ID
        defined in the Data Table.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param instance: Device Instance/Channel.
        :type instance: int
        :param table_id: Lookup Table ID to be executed.
        :type table_id: int
        :return: None
        """
        self.mecom_basic_cmd.set_int32_value(address=address, parameter_id=52010, instance=instance, value=table_id)

    def set_number_of_repetitions(self, address: int, instance: int, nr_of_repetitions: int) -> None:
        """
        Set the number of executions of the "REPEAT_MARK" elements.
        See the Lookup Table definitions for more information about these elements.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param instance: Device Instance/Channel.
        :type instance: int
        :param nr_of_repetitions: Amount of repetitions. Value Range: 0 ... 100'000.
        :type nr_of_repetitions: int
        :return: None
        """
        if 0 <= nr_of_repetitions <= 100_000:
            self.mecom_basic_cmd.set_int32_value(address=address, parameter_id=52012, instance=instance,
                                                 value=nr_of_repetitions)
        else:
            raise LutException("NrOfRepetitions value range is 0 ... 100_000!")

    def _download_page(self, address: int, list_lut_record: List[LutRecord], page_offset: int) -> None:
        """
        Downloads a page of the lookup table to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :param list_lut_record: List of LutG1Records for the page.
        :type list_lut_record: List[LutRecord]
        :param page_offset: The offset of the page.
        :type page_offset: int
        :return: None
        """
        mecom_var_convert = MeComVarConvert()
        try:
            tx_frame = MeComPacket(control="#", address=address)
            tx_frame.payload = (
                mecom_var_convert.add_string(tx_frame.payload, "?LT")
            )  # Start payload with Lookup Table command, '?LT' is used for write and read
            tx_frame.payload = (
                mecom_var_convert.add_uint4(tx_frame.payload, 1)
            )  # 0 = Status Query, 1 = Program, 2 = Do Analyze
            tx_frame.payload = mecom_var_convert.add_uint32(tx_frame.payload, page_offset)  # Lookup Table Page Offset

            # Add bytearray generated from List[LutRecord]
            count = len(list_lut_record)
            lut_record_bytearray = bytearray(b"")
            for i in range(count):
                lut_record_bytearray.extend(list_lut_record[i].get_bytes())
            tx_frame.payload = mecom_var_convert.add_byte_array(stream=tx_frame.payload, value=lut_record_bytearray)

            # Fill the rest of the payload with UINT4 bytes with the value '0' up
            # until the payload is 524 UINT4 bytes long. This is so that the payload
            # is always 256 UINT8 bytes large when sent to the device.
            payload_length = len(tx_frame.payload)
            if payload_length < 524:  # 524
                for i in range(524 - payload_length):
                    tx_frame.payload = mecom_var_convert.add_uint4(tx_frame.payload, value=0)

            timeout: int = 0
            while True:
                rx_frame = self.mequery_set.set(tx_frame=tx_frame)
                status = mecom_var_convert.read_uint4(rx_frame.payload)
                print(f"?LT Program Server Response : {status}")

                if status != LUT_FLASH_STATUS_DATA_ACCEPTED:
                    # Manage device busy
                    timeout += 1
                    if timeout < 50:
                        time.sleep(0.010)
                    else:
                        raise LutException(f"Device Busy while sending Lookup Table")
                else:
                    break

        except LutException as e:
            raise LutException(f"DownloadPage failed: Address {address}; Detail: {e}")

    def _start_analyze_and_wait(self, address: int) -> None:
        """

        :param address: Device Address. Use null to use the DefaultDeviceAddress
            defined on MeComQuerySet.
        :type address: int
        :return: None
        """
        timeout: int = 0
        while True:
            # Send LUT analyze query
            successfully_started = self.start_analyze_lut(address=address)
            print(f"successfully_started : {successfully_started}")
            if successfully_started is not True:
                timeout += 1
                if timeout < 50:
                    time.sleep(0.010)
                else:
                    raise LutException(f"Device Busy while trying to analyze Lookup Table")
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
                record.field2_int = int(old_crc)

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

    def _parse_lut_into_list(self, reader: str) -> List[LutRecord]:
        """

        :param reader:
        :type reader: str
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
            else:
                record: LutRecord = self._enumerate_lut(line=line, line_count=line_count)
                list_.append(record)
                line_count += 1

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

        try:
            if instruction == "TABLE_INFO":
                record.instruction = LUT_TABLE_INFO_INSTR
                if field1 == "START":
                    record.field1 = LUT_TABLE_INFO_F1_START
                elif field1 == "END":
                    record.field1 = LUT_TABLE_INFO_F1_END
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
                record.field2_int = int(field2)
            
            elif instruction == "SIN_RAMP_TO":
                record.instruction = LUT_SIN_RAMP_TO_INSTR
                if field1 == "FROM_ACT":
                    record.field1 = LUT_SIN_RAMP_TO_F1_FROM_ACT
                elif field1 == "FROM_NOM":
                    record.field1 = LUT_SIN_RAMP_TO_F1_FROM_NOM
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
                record.field2_float = float(field2)

            elif instruction == "REPEAT_MARK":
                record.instruction = LUT_REPEAT_MARK_INSTR
                if field1 == "START":
                    record.field1 = LUT_REPEAT_MARK_F1_START
                elif field1 == "END":
                    record.field1 = LUT_REPEAT_MARK_F1_END
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
             
            elif instruction == "LIN_RAMP_TIME":
                record.instruction = LUT_LIN_RAMP_TIME_INSTR
                f1_temp = int(field1)
                if 10 >= f1_temp >= 16_777_216:
                    record.field1 = f1_temp
                record.field2_float = float(field2)
            
            elif instruction == "STATUS":
                record.instruction = LUT_STATUS_INSTR
                if field1 == "DISABLE":
                    record.field1 = LUT_STATUS_F1_DISABLE
                elif field1 == "ENABLE":
                    record.field1 = LUT_STATUS_F1_ENABLE
                else:
                    raise LutException(f"Error in Field1 Enumeration : {field1}")
            
            elif instruction == "WAIT":
                record.instruction = LUT_WAIT_INSTR
                if field1 == "FOREVER":
                    record.field1 = LUT_WAIT_F1_FOREVER
                elif field1 == "TIME":
                    record.field1 = LUT_WAIT_F1_TIME
                    f2_temp = int(field2)
                    if f2_temp >= 0:
                        record.field2_int = f2_temp
            
            elif instruction == "SET_FLOAT":
                record.instruction = LUT_SET_FLOAT_INSTR
                f1temp_1 = int(field1)  # need to confirm operation
                if 0 <= f1temp_1 <= 16_777_216:
                    record.field1 = f1temp_1  # need to confirm operation
                record.field2_int = int(field2)  # need to confirm operation
            
            elif instruction == "SET_INT":
                record.instruction = LUT_SET_INT_INSTR
                f1temp_2 = int(field1)  # need to confirm operation
                if 0 <= f1temp_2 <= 16_777_216:
                    record.field1 = f1temp_2  # need to confirm operation
                record.field2_int = int(field2)  # need to confirm operation
                
            elif instruction == "TILL_TEMP_STABLE":
                record.instruction = LUT_WAIT_TILL_STABLE_INSTR
                
            elif instruction == "SET_TARGET_INST":
                record.instruction = LUT_CHANGE_TARGET_INST_INSTR
                record.field2_int = int(field2)  # need to confirm operation
                
            elif instruction == "EOF":
                record.instruction = LUT_EOF_INSTR
                
            else:
                raise LutException(f"Error in Instruction Enumeration : {instruction}")
        
        except LutException as e:
            raise LutException("Error on line {have to implement}")  # need to fully implement
            
        finally:
            return record


if __name__ == "__main__":
    phy_com = MeComPhySerialPort()
    phy_com.connect(port_name="COM9")

    mequery_set = MeComQuerySet(phy_com=phy_com)

    lut_cmd = LutCmd(mecom_query_set=mequery_set)

    lut_cmd.download_lookup_table(address=2, filepath="LookupTable Sine ramp_0.1_degC_per_sec.csv")

    lut_status_query = lut_cmd.get_lut_status_query(address=2)
    print(f"lut_status_query : {lut_status_query}")

    status_: LutStatus = lut_cmd.get_status(address=2, instance=1)
    print(f"status_ : {status_}")

    phy_com.tear()
