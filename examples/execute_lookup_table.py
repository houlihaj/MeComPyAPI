import os
import time
import logging
from pathlib import Path

from mecompyapi.mecom_tec.lookup_table.lut_status import LutStatus
from mecompyapi.tec import MeerstetterTEC, SaveToFlashState


# Create and configure logger object
logger: logging.Logger = (
    logging.getLogger(name=__name__)
)


def main():
    """

    :return: None
    """
    path: Path = Path(
        os.path.dirname(os.path.abspath(__file__))
    )

    filepath_: str = os.path.join(
        path.parents[0],
        r"src\mecompyapi\mecom_tec\lookup_table\csv\LookupTable Sine ramp_0.1_degC_per_sec.csv"
    )

    # initialize controller
    mc: MeerstetterTEC = MeerstetterTEC()

    try:
        mc.connect_serial_port(port="COM13")

        if mc.get_lookup_table_status() == LutStatus.EXECUTING:
            mc.stop_lookup_table()
            logger.info("Lookup Table was stopped...")

        identity: str = mc.get_id()
        logger.info(f"identity: {identity}\n")

        logger.info(f"status: {mc.get_device_status()}\n")

        mc.reset()
        logger.info(f"status: {mc.get_device_status()}")
        time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
        logger.info(f"status: {mc.get_device_status()}\n")

        mc.download_lookup_table(filepath=filepath_)

        mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.DISABLED)

        mc.set_coarse_temperature_ramp(temp_ramp_degc_per_sec=0.1)

        mc.execute_lookup_table(timeout=300)

    except Exception as e:
        raise e

    finally:
        logger.info("Disconnect from the TEC controller...")
        mc.tear()


if __name__ == "__main__":
    # start logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    main()
