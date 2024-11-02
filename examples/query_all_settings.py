import time
import logging
from mecompyapi.tec import MeerstetterTEC


# Create and configure logger object
logger: logging.Logger = (
    logging.getLogger(name=__name__)
)


def main():
    """

    :return: None
    """
    # initialize controller
    mc = MeerstetterTEC()

    # mc.connect_serial_port(port="COM9")
    mc.connect_serial_port(port="/dev/ttyUSB9")

    identity = mc.get_id()
    logger.info(f"identity: {identity}\n")

    logger.info(f"status: {mc.get_device_status()}\n")

    mc.reset()
    logger.info(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    logger.info(f"status: {mc.get_device_status()}\n")

    settings = mc.get_all_settings()
    logger.info(f"settings:\n")
    for key in settings:
        logger.info(f"{key} : {settings[key]}")

    mc.tear()


if __name__ == "__main__":
    # Start logging
    logging.basicConfig(
        # level=logging.DEBUG,
        level=logging.INFO,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    main()
