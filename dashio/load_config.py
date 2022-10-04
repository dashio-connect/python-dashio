import json
import base64
import zlib

from .iotcontrol import Label, DeviceView, Menu, ButtonGroup, Button, TextBox, Graph, Dial, ColorPicker, TimeGraph, Selector, Slider, Direction, EventLog, Knob, AudioVisualDisplay


CONTROL_INSTANCE_DICT = {
    "AVD": AudioVisualDisplay,
    "DVVW": DeviceView,
    "MENU": Menu,
    "BTGP": ButtonGroup,
    "BTTN": Button,
    "TEXT": TextBox,
    "GRPH": Graph,
    "DIAL": Dial,
    "CLR": ColorPicker,
    "TGRPH": TimeGraph,
    "KNOB": Knob,
    "SLCTR": Selector,
    "SLDR": Slider,
    "DIR": Direction,
    "LOG": EventLog,
    "LBL": Label
}


def decode_cfg64(cfg: str) -> dict:
    """decodes a CFG from iotdasboard app

    Parameters
    ----------
    cfg : str
        A base64 zipped json

    Returns
    -------
    dict
        A dictionary representing the cfg.
    """

    ztmp_b = base64.b64decode(cfg)
    tmp_b = zlib.decompress(ztmp_b, wbits=-9)  # Deal with missing header
    try:
        cfg_dict = json.loads(tmp_b)
    except json.JSONDecodeError:
        return ""
    return cfg_dict


def encode_cfg64(cfg: dict) -> str:
    """Encodes cfg dictionary into C64 string

    Args:
        cfg (dict): the config as sent to the IoTDashboard app

    Returns:
        str: the cfg encoded as C64 format
    """
    cfg_json = json.dumps(cfg)
    compress = zlib.compressobj(6, zlib.DEFLATED, -9, zlib.DEF_MEM_LEVEL, zlib.Z_DEFAULT_STRATEGY)
    tmp_z = compress.compress(cfg_json.encode())
    tmp_z += compress.flush()
    return base64.b64encode(tmp_z).decode()

def load_control_from_config(control_id: str, cfg_dict: dict):
    """Returns a control object instantiated from cfg_dict

    Parameters
    ----------
    control_id : str
        The control_id of the control within the dict to instantiate
    cfg_dict : dict
        dictionary of the CFG loaded by decode_cfg from a CFG64 or json

    Returns
    -------
        A control object.
    """
    for control_type, control_list in cfg_dict.items():
        if isinstance(control_list, list):
            for control in control_list:
                if control["controlID"] == control_id:
                    return CONTROL_INSTANCE_DICT[control_type].from_cfg_dict(control)
    raise Exception(f"Control with control_id: {control_id} not found")


def load_all_controls_from_config(device, cfg_dict) -> dict:
    """Loads all the controls in cfg_dict into device and returns a dictionary of the control objects

    Parameters
    ----------
    device : Dashio.Device
        The device to attach the controls to
    cfg_dict : Dict
        dictionary of the CFG loaded by decode_cfg from a CFG64 or json

    Returns
    -------
    dict
        Dictionary of the control objects
    """
    controls_dict = {}
    for control_type, control_list in cfg_dict.items():
        if isinstance(control_list, list):
            for control in control_list:
                controls_dict[control["controlID"]] = CONTROL_INSTANCE_DICT[control_type].from_cfg_dict(control)
                device.add_control(controls_dict[control["controlID"]])
    return controls_dict
