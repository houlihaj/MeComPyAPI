import time
import logging
from mecompyapi.tec import MeerstetterTEC, SaveToFlashState


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

    identity = mc.get_id()
    logger.info(f"identity: {identity}\n")

    logger.info(f"status: {mc.get_device_status()}\n")

    mc.reset()
    logger.info(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    logger.info(f"status: {mc.get_device_status()}\n")

    mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.DISABLED)

    save_to_flash_state: SaveToFlashState = mc.get_automatic_save_to_flash()
    logger.info(f"save_to_flash_state: {save_to_flash_state}")

    mc.tear()


if __name__ == '__main__':
    # Start logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    main()
