import time
import logging
from mecompyapi.tec import MeerstetterTEC


if __name__ == "__main__":
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_serial_port(port="COM9")

    identity = mc.get_id()
    logging.info(f"identity: {identity}\n")

    logging.info(f"status: {mc.get_device_status()}\n")

    mc.reset()
    logging.info(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    logging.info(f"status: {mc.get_device_status()}\n")

    settings = mc.get_all_settings()
    logging.info(f"settings:\n")
    for key in settings:
        logging.info(f"{key} : {settings[key]}")

    mc.tear()
