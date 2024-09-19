import logging
from mecompyapi.tec import MeerstetterTEC, SaveToFlashState


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_serial_port(port="/dev/tec")

    identity = mc.get_id()
    logging.info(f"identity: {identity}")

    logging.info(f"get_temperature : {mc.get_temperature()}")

    mc.tear()
