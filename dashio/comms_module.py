"""Useful comms module message functions"""


def set_comms_module_passthough(coms_device_id: str) -> str:
    """Set the comms module to passthrough."""
    message = f"\t{coms_device_id}\tCTRL\tMODE\tPSTH\n"
    return message


def set_comms_module_normal(coms_device_id: str) -> str:
    """Set the comms module to normal mode."""
    message = f"\t{coms_device_id}\tCTRL\tMODE\tNML\n"
    return message


def enable_comms_module_ble(coms_device_id: str, enable: bool) -> str:
    """Enable/disable comms module BLE."""
    message = f"\t{coms_device_id}\tCTRL\tBLE"
    if not enable:
        message += "\tHLT"
    return message + '\n'


def enable_comms_module_tcp(coms_device_id: str, enable: bool) -> str:
    """Enable/disable comms module TCP."""
    message = f"\t{coms_device_id}\tCTRL\tTCP"
    if not enable:
        message += "\tHLT"
    return message + '\n'


def enable_comms_module_dash(coms_device_id: str, enable: bool) -> str:
    """Enable/Disable comms module DASH."""
    message = f"\t{coms_device_id}\tCTRL\tMQTT"
    if not enable:
        message += "\tHLT"
    return message + '\n'


def set_comms_module_dash(coms_device_id: str, user_name: str, password: str) -> str:
    """Set username and password for comms module DASH connection."""
    message = f"\t{coms_device_id}\tDASHIO\t{user_name}\t{password}\n"
    return message


def set_comms_module_tcp_port(coms_device_id: str, port: int) -> str:
    """Set the comms module TCP port."""
    message = f"\t{coms_device_id}\tTCP\t{port}\n"
    return message


def set_comms_module_name(coms_device_id: str, name: str) -> str:
    """Set the comms module NAME."""
    message = f"\t{coms_device_id}\tNAME\t{name}\n"
    return message


def set_comms_module_wifi(coms_device_id: str, country_code: str, ssid: str, password: str) -> str:
    """Set the comms module wifi country code, ssid, and password."""
    message = f"\t{coms_device_id}\tWIFI\t{country_code}\t{ssid}\t{password}\n"
    return message


def get_comms_module_active_connections(coms_device_id: str) -> str:
    """Get the active connections from the comms module."""
    message = f"\t{coms_device_id}\tCTRL\tCNCTN\n"
    return message


def reguest_comms_module_device_id(self) -> str:
    """Request the comms module DeviceID."""
    message = "\tCTRL\n"
    return message
