import time
import logging
from mecompyapi.tec import MeerstetterTEC, SaveToFlashState


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect_serial_port(port="COM13")

    identity = mc.get_id()
    logging.info(f"identity: {identity}\n")

    logging.info(f"status: {mc.get_device_status()}\n")

    mc.reset()
    logging.info(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    logging.info(f"status: {mc.get_device_status()}\n")

    mc.set_automatic_save_to_flash(save_to_flash=SaveToFlashState.DISABLED)

    save_to_flash_state: SaveToFlashState = mc.get_automatic_save_to_flash()
    logging.info("save_to_flash_state: {}".format(mc.get_automatic_save_to_flash()))

    mc.tear()
