import os
import time
import logging
from pathlib import Path
from mecompyapi.tec1090series import MeerstetterTEC


if __name__ == "__main__":
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    path = Path(
        os.path.dirname(os.path.abspath(__file__))
    )

    filepath_ = os.path.join(
        path.parents[0],
        r"src\mecompyapi\mecom_tec\lookup_table\csv\LookupTable Sine ramp_0.1_degC_per_sec.csv"
    )

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_serial_port(port="COM13")

    identity = mc.get_id()
    logging.info(f"identity: {identity}\n")

    logging.info(f"status: {mc.get_device_status()}\n")

    mc.reset()
    logging.info(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    logging.info(f"status: {mc.get_device_status()}\n")

    mc.download_lookup_table(filepath=filepath_)

    mc.tear()
