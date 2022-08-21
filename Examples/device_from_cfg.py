"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import argparse
import configparser
import logging
import signal
import time

import dashio
import shortuuid
import json

cfg = "pVXfT9swEH7nr4jyTFhCm5LubW1ZhQYUQWFI2x4c59JYOHbnOLQM8b/PTto4vzo2rZYi1Z999919d+fXI8uyU2B5ZlsfrW9H6u+PY71HUQi0vSlhKyd8C7t9S/1ei6/CMGdScHox05i9nNjHe2SNBDC5A27mrmegnBFZGLPNniSSQrE341yY/QTIKpG3SBKuUffEC5p3bnhGFMhKAnxdM6l4f6JkVUJTxQZqhmMuUiQL6JozMMDL3mLNqT9UyzexCcAk2zl1q+2nMFq+rMsorvMUBMHG7IZEMqmZHFfItseha5xhyjP4EkYLdgcs0rAUORToW6VRitZt2cJcSs7mgucHoD49eRxPOVUC6BhuITL8m0o/XsweDVbaO2copFAwjBHNoII5Mza/JkTWkv2HKukoPwz06qmYxRrY9w9TnadWQR0ujj6V3YFe/68YUbm6RqkpZ0sztFuSrQRaJx1lKEw5Y4D3rEtlbAEour/f5SmE0B8GA3AGI/Cc4SgInPAs9h1A7tlg5IWnIxTsIrUzEM8EQ3V3GKMYn7qe48Wh7wz9MThBjLGDfTzGg4E39obh/u5GKK3+zau6+FYE8sR42A4u/Sllb3QJz+T97WXhJkJZcqI/hJ+o3O6o5CqOKqVYILIyriKCOjMLq4LLRXsXUSTSzngjKcz7tIhAZ04RjpU3Q5bl6axAHghsijueodIE2sNSCnqFtp9VJ92RX0UsAzM9skT1gmqUPC1So5u8wpTPEin9HWjKZv9ob5OnFYtM801oDq0DXEQgFl2PBjzYu/rIYbACrpDgSu2evp0jgVZgNQd+RXspEMuK+YBf9PHAbZxZajPqWTIMFuqCMtecWrWTbYN+j8G6Nt6ov6OL56JATDNnQFVV807FZZSoFHYqi4iyB9oAPKtpeMlXfdXTN7HOfLUMzcMT672nsvH6WueaRvZXU7pZgeeXdeydMdkZ8KdeK6sojwh/IFneaPCjt98="

cfg_json = """
{
"menus" : [

],
"labels" : [
{
"yPositionRatio" : 0,
"widthRatio" : 1,
"titlePosition" : "Bottom",
"style" : "Group",
"title" : "A label",
"parentID" : "TestTCP",
"controlID" : "LabelID",
"color" : "Blue",
"xPositionRatio" : 0,
"heightRatio" : 1
}
],
"textBoxes" : [
{
"controlID" : "TXT1",
"parentID" : "TestTCP",
"units" : "",
"title" : "A text control",
"heightRatio" : 0.12,
"titlePosition" : "Bottom",
"textAlign" : "Left",
"format" : "None",
"yPositionRatio" : 0.84,
"precision" : 0,
"kbdType" : "All Characters",
"widthRatio" : 0.54,
"xPositionRatio" : 0.24,
"closeKbdOnSend" : true
}
],
"maps" : [

],
"buttonGroups" : [

],
"buttons" : [
{
"offColor" : "Red",
"controlID" : "DOWN_BTN",
"buttonEnabled" : true,
"onColor" : "Green",
"parentID" : "TestTCP",
"heightRatio" : 0.12,
"title" : "Down",
"titlePosition" : "Bottom",
"yPositionRatio" : 0.86,
"widthRatio" : 0.22,
"xPositionRatio" : 0.02,
"iconName" : "Down"
},
{
"offColor" : "Red",
"controlID" : "UP_BTN",
"buttonEnabled" : true,
"onColor" : "Green",
"parentID" : "TestTCP",
"heightRatio" : 0.12,
"title" : "Up",
"titlePosition" : "Bottom",
"yPositionRatio" : 0.01,
"widthRatio" : 0.22,
"xPositionRatio" : 0.02,
"iconName" : "Up"
}
],
"graphs" : [

],
"knobs" : [
{
"style" : "Normal",
"controlID" : "KNB",
"sendOnlyOnRelease" : true,
"max" : 10,
"parentID" : "TestTCP",
"redValue" : 10,
"title" : "A Knob",
"heightRatio" : 0.21,
"titlePosition" : "Bottom",
"showMinMax" : false,
"yPositionRatio" : 0.14,
"knobColor" : "Red",
"dialFollowsKnob" : false,
"dialColor" : "Blue",
"widthRatio" : 0.54,
"xPositionRatio" : 0.24,
"min" : 0
}
],
"dials" : [
{
"precision" : 2,
"style" : "Bar",
"controlID" : "DIAL1",
"max" : 10,
"parentID" : "TestTCP",
"redValue" : 75,
"title" : "A Dial",
"heightRatio" : 0.21,
"dialFillColor" : "Red",
"titlePosition" : "Bottom",
"yPositionRatio" : 0.63,
"pointerColor" : "Blue",
"numberPosition" : "Center",
"showMinMax" : false,
"widthRatio" : 0.54,
"xPositionRatio" : 0.24,
"units" : "m\/s",
"min" : 0
}
],
"colours" : [

],
"tcpConnection" : {
"port" : 5650,
"ipAddress" : "192.168.1.120"
},
"alarms" : [

],
"deviceViews" : [
{
"ctrlMaxFontSize" : 20,
"shareColumn" : true,
"numColumns" : 1,
"controlID" : "TestTCP",
"ctrlBkgndColor" : "Black",
"ctrlBorderOn" : false,
"ctrlBorderColor" : "White Smoke",
"ctrlColor" : "White Smoke",
"color" : "Black",
"title" : "TestTCP: mbp16-3.local",
"ctrlBkgndTransparency" : 0,
"ctrlTitleBoxColor" : "Black",
"ctrlTitleBoxTransparency" : 0,
"ctrlTitleFontSize" : 16,
"iconName" : "Square"
}
],
"deviceConfig" : {
"numDeviceViews" : 1
},
"timeGraphs" : [

],
"selectors" : [
{
"yPositionRatio" : 0.01,
"widthRatio" : 0.54,
"titlePosition" : "Bottom",
"title" : "A Selector",
"parentID" : "TestTCP",
"controlID" : "TestSelector",
"xPositionRatio" : 0.24,
"heightRatio" : 0.13
}
],
"sliders" : [
{
"sliderEnabled" : true,
"controlID" : "SLDR_DBL",
"sendOnlyOnRelease" : true,
"max" : 5,
"parentID" : "TestTCP",
"redValue" : 5,
"title" : "Slider Double",
"heightRatio" : 0.98,
"titlePosition" : "Bottom",
"showMinMax" : false,
"yPositionRatio" : 0.01,
"knobColor" : "Red",
"barFollowsSlider" : false,
"barColor" : "Blue",
"widthRatio" : 0.2,
"xPositionRatio" : 0.78,
"barStyle" : "Segmented",
"min" : 0
},
{
"sliderEnabled" : true,
"controlID" : "SLDR",
"sendOnlyOnRelease" : true,
"max" : 10,
"parentID" : "TestTCP",
"redValue" : 10,
"title" : "Slider",
"heightRatio" : 0.73,
"titlePosition" : "Bottom",
"showMinMax" : false,
"yPositionRatio" : 0.13,
"knobColor" : "Red",
"barFollowsSlider" : false,
"barColor" : "Blue",
"widthRatio" : 0.22,
"xPositionRatio" : 0.02,
"barStyle" : "Segmented",
"min" : 0
}
],
"directions" : [
{
"style" : "DEGPS",
"controlID" : "COMP1",
"parentID" : "TestTCP",
"units" : "nm",
"title" : "A Direction control",
"calAngle" : 0,
"titlePosition" : "Bottom",
"heightRatio" : 0.22,
"yPositionRatio" : 0.38,
"pointerColor" : "Green",
"precision" : 2,
"widthRatio" : 0.54,
"xPositionRatio" : 0.24
}
],
"audioVisuals" : [

],
"eventLogs" : [

]
}
"""

SHUTDOWN = False
COUNTER = 0


def signal_cntrl_c(os_signal, os_frame):
    global SHUTDOWN
    print("Shutdown")
    SHUTDOWN = True


def init_logging(logfilename, level):
    log_level = logging.WARN
    if level == 1:
        log_level = logging.INFO
    elif level == 2:
        log_level = logging.DEBUG
    if not logfilename:
        formatter = logging.Formatter("%(asctime)s, %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(log_level)
    else:
        logging.basicConfig(
            filename=logfilename,
            level=log_level,
            format="%(asctime)s, %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    logging.info("==== Started ====")


def parse_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        const=1,
        default=1,
        type=int,
        nargs="?",
        help="""increase verbosity:
                        0 = only warnings, 1 = info, 2 = debug.
                        No number means info. Default is no verbosity.""",
    )
    parser.add_argument("-u", "--username", help="Dashio Username", dest="username", default="")
    parser.add_argument("-w", "--password", help="DashIO Password", dest="password", default="")
    parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args

def load_controls_from_config(device, cfg_dict) -> dict:
    controls_dict = {}
    for device_view in cfg_dict["deviceViews"]:
        controls_dict[device_view["controlID"]] = dashio.DeviceView.from_cfg_dict(device_view)
        device.add_control(controls_dict[device_view["controlID"]])
    for menu in cfg_dict["menus"]:
        controls_dict[menu["controlID"]] = dashio.Menu.from_cfg_dict(menu)
        controls_dict[menu["parentID"]].add_control(controls_dict[menu["controlID"]])
        device.add_control(controls_dict[menu["controlID"]])
    for button_g in cfg_dict["buttonGroups"]:
        controls_dict[button_g["controlID"]] = dashio.ButtonGroup.from_cfg_dict(button_g)
        controls_dict[button_g["parentID"]].add_control(controls_dict[button_g["controlID"]])
        device.add_control(controls_dict[button_g["controlID"]])
    for button in cfg_dict["buttons"]:
        controls_dict[button["controlID"]] = dashio.Button.from_cfg_dict(button)
        controls_dict[button["parentID"]].add_control(controls_dict[button["controlID"]])
        device.add_control(controls_dict[button["controlID"]])
    for text_box in cfg_dict["textBoxes"]:
        controls_dict[text_box["controlID"]] = dashio.TextBox.from_cfg_dict(text_box)
        controls_dict[text_box["parentID"]].add_control(controls_dict[text_box["controlID"]])
        device.add_control(controls_dict[text_box["controlID"]])
    for graph in cfg_dict["graphs"]:
        controls_dict[graph["controlID"]] = dashio.Graph.from_cfg_dict(graph)
        controls_dict[graph["parentID"]].add_control(controls_dict[graph["controlID"]])
        device.add_control(controls_dict[graph["controlID"]])
    for dial in cfg_dict["dials"]:
        controls_dict[dial["controlID"]] = dashio.Dial.from_cfg_dict(dial)
        controls_dict[dial["parentID"]].add_control(controls_dict[dial["controlID"]])
        device.add_control(controls_dict[dial["controlID"]])
    for color_p in cfg_dict["colours"]:
        controls_dict[color_p["controlID"]] = dashio.ColorPicker.from_cfg_dict(color_p)
        controls_dict[color_p["parentID"]].add_control(controls_dict[color_p["controlID"]])
        device.add_control(controls_dict[color_p["controlID"]])
    for alarm in cfg_dict["alarms"]:
        # TODO
        pass
    for time_graph in cfg_dict["timeGraphs"]:
        controls_dict[time_graph["controlID"]] = dashio.TimeGraph.from_cfg_dict(time_graph)
        controls_dict[time_graph["parentID"]].add_control(controls_dict[time_graph["controlID"]])
        device.add_control(controls_dict[time_graph["controlID"]])
    for selector in cfg_dict["selectors"]:
        controls_dict[selector["controlID"]] = dashio.Selector.from_cfg_dict(selector)
        controls_dict[selector["parentID"]].add_control(controls_dict[selector["controlID"]])
        device.add_control(controls_dict[selector["controlID"]])
    for slider in cfg_dict["sliders"]:
        controls_dict[slider["controlID"]] = dashio.Slider.from_cfg_dict(slider)
        controls_dict[slider["parentID"]].add_control(controls_dict[slider["controlID"]])
        device.add_control(controls_dict[slider["controlID"]])
    for direction in cfg_dict["directions"]:
        controls_dict[direction["controlID"]] = dashio.Direction.from_cfg_dict(direction)
        controls_dict[direction["parentID"]].add_control(controls_dict[direction["controlID"]])
        device.add_control(controls_dict[direction["controlID"]])
    for even_log in cfg_dict["eventLogs"]:
        controls_dict[even_log["controlID"]] = dashio.EventLog.from_cfg_dict(even_log)
        controls_dict[even_log["parentID"]].add_control(controls_dict[even_log["controlID"]])
        device.add_control(controls_dict[even_log["controlID"]])
        pass
    for audio_visual in cfg_dict["audioVisuals"]:
        # TODO
        pass
    
    return controls_dict




def main():


    signal.signal(signal.SIGINT, signal_cntrl_c)
    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)

    new_ini_file = False
    ini_file = "load_cfg.ini"
    config_file_parser = configparser.ConfigParser()
    config_file_parser.defaults()

    try:
        ini_f = open(ini_file)
        ini_f.close()
    except FileNotFoundError:
        default = {
            'DeviceID': shortuuid.uuid(),
            'DeviceName': 'Load CFG Test',
            'DeviceType': 'DashIOTest',
            'username': args.username,
            'password': args.password
        }
        config_file_parser['DEFAULT'] = default
        with open(ini_file, 'w') as configfile:
            config_file_parser.write(configfile)
        new_ini_file = True

    if not new_ini_file:
        config_file_parser.read(ini_file)
    config_file_parser.get('DEFAULT', 'username')
    device = dashio.Device(
        config_file_parser.get('DEFAULT', 'DeviceType'),
        config_file_parser.get('DEFAULT', 'DeviceID'),
        config_file_parser.get('DEFAULT', 'DeviceName')
    )
    dash_conn = dashio.DashConnection(
        config_file_parser.get('DEFAULT', 'username'),
        config_file_parser.get('DEFAULT', 'password')
    )
    dash_conn.add_device(device)

    #config_dict = dashio.decode_cfg(cfg)
    config_dict = json.loads(cfg_json)
    controls = load_controls_from_config(device, config_dict)

    global SHUTDOWN
    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
