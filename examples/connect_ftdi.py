import logging
from mecompyapi.tec1090series import MeerstetterTEC


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_ftdi(id_str="DK0E1IDC")

    identity = mc.get_id()
    print(f"identity: {identity}")
    print("\n", end="")

    mc.tear()
