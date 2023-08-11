import logging

from tec1090series import MeerstetterTEC


class MeerstetterTEC1092(MeerstetterTEC):
    """
    Controlling TEC devices via serial.
    """

    def __init__(self, *args, **kwars):
        MeerstetterTEC().__init__()


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC1092()

    mc.connect(port="COM17", channel=1)

    # get the values from DEFAULT_QUERIES
    print(mc.get_data())

    mc.tear()
