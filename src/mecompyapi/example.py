from phy_wrapper.mecom_phy_serial_port import MeComPhySerialPort
from mecom_core.mecom_basic_cmd import MeComBasicCmd
from mecom_core.mecom_query_set import MeComQuerySet


if __name__ == "__main__":
    phy_com = MeComPhySerialPort()
    phy_com.connect(port_name="COM9")

    mequery_set = MeComQuerySet(phy_com=phy_com)

    mecom_basic_cmd = MeComBasicCmd(mequery_set=mequery_set)

    identify = mecom_basic_cmd.get_ident_string(address=2, channel=1)
    print(f"identify : {identify}")

    device_type = mecom_basic_cmd.get_int32_value(address=2, parameter_id=100,
                                                  instance=1)  # parameter_name : "Device Type"
    print(f"device_type : {device_type}")

    target_object_temperature = (
        mecom_basic_cmd.get_float_value(address=2, parameter_id=1010, instance=1)
    )  # parameter_name : "Target Object Temperature"
    print(f"target_object_temperature : {target_object_temperature}")

    object_temperature = mecom_basic_cmd.get_float_value(address=2, parameter_id=1000,
                                                         instance=1)  # parameter_name : "Object Temperature"
    print(f"object_temperature : {object_temperature}")

    rx_frame = mecom_basic_cmd.set_float_value(address=2, parameter_id=3000,
                                               instance=1, value=27.0)  # parameter_name : "Target Object Temp (Set)"
    print(f"{rx_frame.receive_type}")

    phy_com.tear()
    print("Done...")
