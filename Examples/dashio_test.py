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


def main():

    def up_btn_event_handler(msg):
        global COUNTER
        COUNTER += 1
        txt_box.text = f"{COUNTER}"

    def down_btn_event_handler(msg):
        global COUNTER
        COUNTER -= 1
        txt_box.text = f"{COUNTER}"

    signal.signal(signal.SIGINT, signal_cntrl_c)
    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)

    new_ini_file = False
    ini_file = "dash_test.ini"
    config_file_parser = configparser.ConfigParser()
    config_file_parser.defaults()

    try:
        ini_f = open(ini_file)
        ini_f.close()
    except FileNotFoundError:
        default = {
            'DeviceID': shortuuid.uuid(),
            'DeviceName': 'DashIO Test',
            'DeviceType': 'DashIOTests',
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
    dview = dashio.DeviceView('Dashio_pg1', 'DashIO Public Test')

    up_button = dashio.Button(
        'up',
        'UP',
        title_position=dashio.TitlePosition.NONE,
        icon_name=dashio.Icon.UP,
        control_position=dashio.ControlPosition(0.4, 0.22, 0.2, 0.2)
    )
    up_button.add_receive_message_callback(up_btn_event_handler)
    up_button.btn_state = dashio.ButtonState.OFF
    down_button = dashio.Button(
        'down',
        'DOWN',
        title_position=dashio.TitlePosition.NONE,
        icon_name=dashio.Icon.DOWN,
        control_position=dashio.ControlPosition(0.4, 0.53, 0.2, 0.2)
    )
    down_button.add_receive_message_callback(down_btn_event_handler)
    down_button.btn_state = dashio.ButtonState.OFF

    txt_box = dashio.TextBox(
        'txtbox1',
        'Counter',
        keyboard_type=dashio.Keyboard.NONE,
        text_align=dashio.TextAlignment.CENTER,
        text=f"{COUNTER}",
        control_position=dashio.ControlPosition(0.0, 0.43, 1.0, 0.1)
    )

    dview.add_control(up_button)
    dview.add_control(down_button)
    dview.add_control(txt_box)
    device.add_control(dview)
    device.add_control(up_button)
    device.add_control(down_button)
    device.add_control(txt_box)

    global SHUTDOWN
    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
