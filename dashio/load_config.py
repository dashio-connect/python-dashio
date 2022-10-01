import json
import base64
import zlib
from enum import Enum
from .iotcontrol import Label, DeviceView, Menu, ButtonGroup, Button, TextBox, Graph, Dial, ColorPicker, TimeGraph, Selector, Slider, Direction, EventLog, Knob


class ControlTitleJSON(Enum):
    """
    Enum to map control type to json header
    """
    CLR = "colours"
    ALRM = "alarm"
    AVD = "audioVisuals"
    DVCE = "deviceConfig"
    DVVW = "deviceViews"
    DIAL = "dials"
    DIR = "directions"
    LOG = "eventLogs"
    GRPH = "graph"
    KNOB = "knobs"
    LBL = "labels"
    MENU = "menus"
    SLCTR = "selectors"
    SLDR = "sliders"
    TEXT = "textBoxes"
    TGRPH = "timeGraphs"
    MAP = "maps"
    BTGP = "buttonGroups"
    BTTN = "buttons"
    TCP = "tcpConnection"


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


def load_controls_from_config(device, cfg_dict) -> dict:
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
        device.add_control(controls_dict[device_view["controlID"]])
    for menu in cfg_dict["MENU"]:
        controls_dict[menu["controlID"]] = Menu.from_cfg_dict(menu)
        controls_dict[menu["parentID"]].add_control(controls_dict[menu["controlID"]])
        device.add_control(controls_dict[menu["controlID"]])
    for button_g in cfg_dict["BTGP"]:
        controls_dict[button_g["controlID"]] = ButtonGroup.from_cfg_dict(button_g)
        controls_dict[button_g["parentID"]].add_control(controls_dict[button_g["controlID"]])
        device.add_control(controls_dict[button_g["controlID"]])
    for button in cfg_dict["BTTN"]:
        controls_dict[button["controlID"]] = Button.from_cfg_dict(button)
        controls_dict[button["parentID"]].add_control(controls_dict[button["controlID"]])
        device.add_control(controls_dict[button["controlID"]])
    for text_box in cfg_dict["TEXT"]:
        controls_dict[text_box["controlID"]] = TextBox.from_cfg_dict(text_box)
        controls_dict[text_box["parentID"]].add_control(controls_dict[text_box["controlID"]])
        device.add_control(controls_dict[text_box["controlID"]])
    for graph in cfg_dict["GRPH"]:
        controls_dict[graph["controlID"]] = Graph.from_cfg_dict(graph)
        controls_dict[graph["parentID"]].add_control(controls_dict[graph["controlID"]])
        device.add_control(controls_dict[graph["controlID"]])
    for dial in cfg_dict["DIAL"]:
        controls_dict[dial["controlID"]] = Dial.from_cfg_dict(dial)
        controls_dict[dial["parentID"]].add_control(controls_dict[dial["controlID"]])
        device.add_control(controls_dict[dial["controlID"]])
    for color_p in cfg_dict["CLR"]:
        controls_dict[color_p["controlID"]] = ColorPicker.from_cfg_dict(color_p)
        controls_dict[color_p["parentID"]].add_control(controls_dict[color_p["controlID"]])
        device.add_control(controls_dict[color_p["controlID"]])
    for knob in cfg_dict["KNOB"]:
        controls_dict[knob["controlID"]] = Knob.from_cfg_dict(knob)
        controls_dict[knob["parentID"]].add_control(controls_dict[knob["controlID"]])
        device.add_control(controls_dict[knob["controlID"]])
    for time_graph in cfg_dict["TGRPH"]:
        controls_dict[time_graph["controlID"]] = TimeGraph.from_cfg_dict(time_graph)
        controls_dict[time_graph["parentID"]].add_control(controls_dict[time_graph["controlID"]])
        device.add_control(controls_dict[time_graph["controlID"]])
    for selector in cfg_dict["SLCTR"]:
        controls_dict[selector["controlID"]] = Selector.from_cfg_dict(selector)
        controls_dict[selector["parentID"]].add_control(controls_dict[selector["controlID"]])
        device.add_control(controls_dict[selector["controlID"]])
    for slider in cfg_dict["SLDR"]:
        controls_dict[slider["controlID"]] = Slider.from_cfg_dict(slider)
        controls_dict[slider["parentID"]].add_control(controls_dict[slider["controlID"]])
        device.add_control(controls_dict[slider["controlID"]])
    for direction in cfg_dict["DIR"]:
        controls_dict[direction["controlID"]] = Direction.from_cfg_dict(direction)
        controls_dict[direction["parentID"]].add_control(controls_dict[direction["controlID"]])
        device.add_control(controls_dict[direction["controlID"]])
    for event_log in cfg_dict["LOG"]:
        controls_dict[event_log["controlID"]] = EventLog.from_cfg_dict(event_log)
        controls_dict[event_log["parentID"]].add_control(controls_dict[event_log["controlID"]])
        device.add_control(controls_dict[event_log["controlID"]])
    for label in cfg_dict["LBL"]:
        controls_dict[label["controlID"]] = Label.from_cfg_dict(label)
        controls_dict[label["parentID"]].add_control(controls_dict[label["controlID"]])
        device.add_control(controls_dict[label["controlID"]])

    #  for audio_visual in cfg_dict["audioVisuals"]:
        # TODO
    #    pass
    #
    return controls_dict

