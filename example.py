from mecom_core.mecom_basic_cmd import MeComBasicCmd


if __name__ == "__main__":
    mecom_basic_cmd = MeComBasicCmd()

    # # "send_string" and "get_data_or_timeout" work
    # mecom_basic_cmd.phy_com.send_string(stream="#000008?IF018868\r")
    # rsp_frame = mecom_basic_cmd.phy_com.get_data_or_timeout()
    # print(rsp_frame)

    identify = mecom_basic_cmd.get_ident_string(address=2, channel=1)
    print(f"identify : {identify}")

    device_type = mecom_basic_cmd.get_int32_value(address=2, parameter_id=100,
                                                  instance=1)  # parameter_name : "Device Type"
    print(f"device_type : {device_type}")

    object_temperature = mecom_basic_cmd.get_float_value(address=2, parameter_id=1000,
                                                         instance=1)  # parameter_name : "Object Temperature"
    print(f"object_temperature : {object_temperature}")

    mecom_basic_cmd.phy_com.tear()
    print("Done...")
