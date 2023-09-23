import time
import logging
from mecompyapi.tec1090series import MeerstetterTEC


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc = MeerstetterTEC()

    mc.connect(port="COM13")

    identity = mc.get_id()
    print(f"identity: {identity}")
    print("\n", end="")

    print(f"status: {mc.get_device_status()}")
    print("\n", end="")

    mc.reset()
    print(f"status: {mc.get_device_status()}")
    time.sleep(2.0)  # Wait time of 2 seconds is required to maintain connection.
    print(f"status: {mc.get_device_status()}")
    print("\n", end="")

    settings = mc.get_all_settings()
    print(f"settings:\n", end="")
    for key in settings:
        print(f"{key} : {settings[key]}")

    mc.tear()
