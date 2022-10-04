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
    for device_view in cfg_dict["DVVW"]:
        controls_dict[device_view["controlID"]] = DeviceView.from_cfg_dict(device_view)
    for menu in cfg_dict["MENU"]:
        controls_dict[menu["controlID"]] = Menu.from_cfg_dict(menu)
        device.add_control(controls_dict[menu["controlID"]])
    for button_g in cfg_dict["BTGP"]:
        controls_dict[button_g["controlID"]] = ButtonGroup.from_cfg_dict(button_g)
        device.add_control(controls_dict[button_g["controlID"]])
    for button in cfg_dict["BTTN"]:
        controls_dict[button["controlID"]] = Button.from_cfg_dict(button)
        device.add_control(controls_dict[button["controlID"]])
    for text_box in cfg_dict["TEXT"]:
        controls_dict[text_box["controlID"]] = TextBox.from_cfg_dict(text_box)
        device.add_control(controls_dict[text_box["controlID"]])
    for graph in cfg_dict["GRPH"]:
        controls_dict[graph["controlID"]] = Graph.from_cfg_dict(graph)
        device.add_control(controls_dict[graph["controlID"]])
    for dial in cfg_dict["DIAL"]:
        controls_dict[dial["controlID"]] = Dial.from_cfg_dict(dial)
        device.add_control(controls_dict[dial["controlID"]])
    for color_p in cfg_dict["CLR"]:
        controls_dict[color_p["controlID"]] = ColorPicker.from_cfg_dict(color_p)
        device.add_control(controls_dict[color_p["controlID"]])
    for knob in cfg_dict["KNOB"]:
        controls_dict[knob["controlID"]] = Knob.from_cfg_dict(knob)
        device.add_control(controls_dict[knob["controlID"]])
    for time_graph in cfg_dict["TGRPH"]:
        controls_dict[time_graph["controlID"]] = TimeGraph.from_cfg_dict(time_graph)
        device.add_control(controls_dict[time_graph["controlID"]])
    for selector in cfg_dict["SLCTR"]:
        controls_dict[selector["controlID"]] = Selector.from_cfg_dict(selector)
        device.add_control(controls_dict[selector["controlID"]])
    for slider in cfg_dict["SLDR"]:
        controls_dict[slider["controlID"]] = Slider.from_cfg_dict(slider)
        device.add_control(controls_dict[slider["controlID"]])
    for direction in cfg_dict["DIR"]:
        controls_dict[direction["controlID"]] = Direction.from_cfg_dict(direction)
        device.add_control(controls_dict[direction["controlID"]])
    for event_log in cfg_dict["LOG"]:
        controls_dict[event_log["controlID"]] = EventLog.from_cfg_dict(event_log)
        device.add_control(controls_dict[event_log["controlID"]])
    for label in cfg_dict["LBL"]:
        controls_dict[label["controlID"]] = Label.from_cfg_dict(label)
        device.add_control(controls_dict[label["controlID"]])

    #  for audio_visual in cfg_dict["audioVisuals"]:
        # TODO
    #    pass
    #
    return controls_dict

