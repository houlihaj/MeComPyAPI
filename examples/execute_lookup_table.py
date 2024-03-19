import os
import time
import logging
from pathlib import Path

from mecompyapi.mecom_tec.lookup_table.lut_status import LutStatus
from mecompyapi.tec1090series import MeerstetterTEC, SaveToFlashState


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    path = Path(
        os.path.dirname(os.path.abspath(__file__))
    )

    filepath_ = os.path.join(
        path.parents[0],
        r"src\mecompyapi\mecom_tec\lookup_table\csv\LookupTable Sine ramp_0.1_degC_per_sec.csv"
    )

    # initialize controller
    mc = MeerstetterTEC()

    try:
        mc.connect_serial_port(port="COM13")

        if mc.get_lookup_table_status() == LutStatus.EXECUTING:
            mc.stop_lookup_table()
            print("Lookup Table was stopped...")

        identity = mc.get_id()
        print("identity: {}".format(identity))
        print("\n", end="")

        print("status: {}".format(mc.get_device_status()))
        print("\n", end="")

        mc.reset()
        print("status: {}".format(mc.get_device_status()))
        time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
        print("status: {}".format(mc.get_device_status()))
        print("\n", end="")

        mc.download_lookup_table(filepath=filepath_)

        mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.DISABLED)

        # mc.set_coarse_temperature_ramp(temp_ramp_degc_per_sec=0.1)
        mc.set_coarse_temperature_ramp(temp_ramp_degc_per_sec=0.2)

        mc.execute_lookup_table(timeout=300)

    except Exception as e:
        raise e

    finally:
        print("Disconnect from the TEC controller...")
        mc.tear()
