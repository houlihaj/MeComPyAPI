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
    mc = MeerstetterTEC()

    mc.connect_serial_port(port="/dev/tec")

    identity = mc.get_id()
    logger.info(f"identity: {identity}")

    mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.ENABLED)

    mc.set_integration_time(int_time_sec=4.8)

    logger.info(f"get_proportional_gain : {mc.get_proportional_gain()}")

    mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.DISABLED)

    mc.tear()


if __name__ == '__main__':
    # start logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    main()
