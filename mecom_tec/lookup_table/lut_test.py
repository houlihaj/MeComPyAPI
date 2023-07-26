import time

from lut_cmd import LutCmd
from lut_exception import LutException
from lut_status import LutStatus

from mecom_core.com_command_exception import ComCommandException


class LutTest(object):
    def __init__(self):
        self.mecom_lut_cmd = LutCmd(mecom_instance=)

    def sub_loop(self) -> None:
        """
        :return: None
        """
        self._download_lookup_table()
        self._start_lookup_table()
        time.sleep(secs=30)
        self._stop_lookup_table()

    def _download_lookup_table(self) -> None:
        """
        :return: None
        """
        filepath = "LookupTable Sine ramp_0.1_degC_per_sec.csv"

        # Enter the path to the lookup table file (*.csv)
        try:
            self.mecom_lut_cmd.download_lookup_table(address=Null, filepath=filepath)
            status = LutStatus.NO_INIT
            timeout: int = 0
            while True:
                status = self.mecom_lut_cmd.get_status(address=Null, instance=1)
                print(f"LutCmd status : {status.get_description()}")
                if status == LutStatus.NO_INIT or status == LutStatus.ANALYZING:
                    timeout += 1
                    if timeout < 50:
                        time.sleep(0.010)
                    else:
                        raise LutException("Timeout while trying to get Lookup Table status!")
                else:
                    break
            print(f"Lookup Table Status (52002): {status.get_description()}")
        except LutException as e:
            raise LutException(f"Error while trying to download lookup table: {e}")

    def _start_lookup_table(self) -> None:
        """

        :return: None
        """
        try:
            self.mecom_lut_cmd.start_lookup_table(address=Null, instance=1)
        except LutException as e:
            raise ComCommandException(f"start_lookup_table failed: Detail: {e}")

    def _stop_lookup_table(self) -> None:
        """

        :return: None
        """
        try:
            self.mecom_lut_cmd.stop_lookup_table(address=Null, instance=1)
        except LutException as e:
            raise ComCommandException(f"stop_lookup_table failed: Detail: {e}")
