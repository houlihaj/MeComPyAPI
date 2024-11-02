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
    mc: MeerstetterTEC = MeerstetterTEC()

    mc.connect_serial_port(port="COM13")

    identity: str = mc.get_id()
    logger.info(f"identity: {identity}\n")

    logger.info(f"status: {mc.get_device_status()}\n")

    mc.reset()
    logger.info(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    logger.info(f"status: {mc.get_device_status()}\n")

    # Have to wait for a short period after resetting
    # to get readings successfully
    time.sleep(1.0)

    data_log: str = mc.get_monitor_data_logger(header=True)
    logger.info(data_log)

    mc.tear()


if __name__ == '__main__':
    # start logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    main()
