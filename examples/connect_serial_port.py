import logging
from mecompyapi.tec1090series import MeerstetterTEC


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_serial_port(port="COM9")

    identity = mc.get_id()
    logging.info(f"identity: {identity}")

    mc.tear()
