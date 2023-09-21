import time
import logging
from mecompyapi.tec1090series import MeerstetterTEC, SaveToFlashState


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect(port="COM9")

    identity = mc.get_id()
    print("identity: {}".format(identity))
    print("\n", end="")

    print("status: {}".format(mc.get_device_status()))
    print("\n", end="")

    mc.reset()
    print("status: {}".format(mc.get_device_status()))
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    print("status: {}".format(mc.get_device_status()))
    print("\n", end="")

    mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.DISABLED)

    save_to_flash_state: SaveToFlashState = mc.get_automatic_save_to_flash()
    print("save_to_flash_state: {}".format(mc.get_automatic_save_to_flash()))

    mc.tear()
