import logging
from mecompyapi.tec import MeerstetterTEC


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_ftdi(id_str="DK0E1IDC")

    fw_id_string = (
        mc.get_firmware_identification_string()
    )  # response is always 20 char long; padded with spaces if needed
    logging.info(f"FW Identification String : {fw_id_string}\n")

    identity = mc.get_id()
    logging.info(f"identity: {identity}")

    mc.tear()
