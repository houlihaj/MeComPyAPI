import logging

from mecompyapi.mecom_core.mecom_basic_cmd import MeComBasicCmd
from mecompyapi.mecom_core.mecom_frame import MeComPacket
from mecompyapi.mecom_core.mecom_query_set import MeComQuerySet
from mecompyapi.phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort


if __name__ == "__main__":
    # Start logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    phy_com: MeComPhySerialPort = MeComPhySerialPort()
    phy_com.connect(port_name="COM9")

    mequery_set: MeComQuerySet = MeComQuerySet(phy_com=phy_com)

    mecom_basic_cmd: MeComBasicCmd = MeComBasicCmd(mequery_set=mequery_set)

    identify: str = mecom_basic_cmd.get_ident_string(address=2, channel=1)
    logging.info(f"identify : {identify}")

    device_type: int = (
        mecom_basic_cmd.get_int32_value(
            address=2, parameter_id=100, instance=1)
    )  # parameter_name : "Device Type"
    logging.info(f"device_type : {device_type}")

    target_object_temperature: float = (
        mecom_basic_cmd.get_float_value(address=2, parameter_id=1010, instance=1)
    )  # parameter_name : "Target Object Temperature"
    logging.info(f"target_object_temperature : {target_object_temperature}")

    object_temperature: float = (
        mecom_basic_cmd.get_float_value(
            address=2, parameter_id=1000, instance=1)
    )  # parameter_name : "Object Temperature"
    logging.info(f"object_temperature : {object_temperature}")

    rx_frame: MeComPacket = (
        mecom_basic_cmd.set_float_value(
            address=2, parameter_id=3000, instance=1, value=27.0)
    )  # parameter_name : "Target Object Temp (Set)"
    logging.info(f"{rx_frame.receive_type}")

    phy_com.tear()
    logging.info("Done...")
