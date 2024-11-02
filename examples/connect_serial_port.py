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
    # Start logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    # initialize controller
    mc: MeerstetterTEC = MeerstetterTEC()

    # mc.connect_serial_port(port="COM9")
    mc.connect_serial_port(port="/dev/ttyUSB9")

    identity: str = mc.get_id()
    logger.info(f"identity: {identity}")

    mc.tear()


if __name__ == '__main__':
    main()
