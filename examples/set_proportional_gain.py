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

    mc.connect_serial_port(port="/dev/tec")

    identity: str = mc.get_id()
    logger.info(f"identity: {identity}")

    mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.ENABLED)

    mc.set_proportional_gain(prop_gain=8.1)

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
