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

    mc.connect_ftdi(id_str="DK0E1IDC")

    fw_id_string: str = (
        mc.get_firmware_identification_string()
    )  # response is always 20 char long; padded with spaces if needed
    logger.info(f"FW Identification String : {fw_id_string}\n")

    identity: str = mc.get_id()
    logger.info(f"identity: {identity}")

    mc.tear()


if __name__ == '__main__':
    # Start logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    main()
