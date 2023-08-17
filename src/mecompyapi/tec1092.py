import logging

from tec1090series import MeerstetterTEC


class MeerstetterTEC1092(MeerstetterTEC):
    """
    Controlling TEC devices via serial.
    """

    def __init__(self, *args, **kwars):
        super().__init__()


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC1092()

    mc.connect(port="COM15", instance=1)

    identity = mc.get_id()
    print(f"identity : {identity} ; type {type(identity)}")
    print("\n", end="")

    mc.tear()
