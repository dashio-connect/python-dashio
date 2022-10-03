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
import json
import logging
import signal
import time

import dashio
import shortuuid

cfg = "tVdbc+o2EP4rjJ7dFEMhHN4wJjQTYzO2Q85M2zljbAEaZIna8gGayX/vyhewMbdM2jch7fXbb9fLO3JH313U/+Md+ZyJiNNnHfWR"\
"+91VkYI2XoSZyG5wLNzhFC4TRkQMN3AURFAMx0FD4J1o5BbgYYXJciVsTxCO+s0HtZXLTnlM4I6Bjma5rjWRRkB1QMlSXhqjJxeu"\
"FjwKPQG/Tcscwe99oXew2PsNoouwT+LUWlNB63ng7jdpNIYBOlsSiNVBvgPyu5qVFtz6lMf4ZR5YzMEsQH0RJfjjLwXps9lbikss"\
"9mmS2sB5HoJhX0R04u2eIFmH/AMvLfC+jEgw5DQJGUDTgnTjFWCX3WQ2FcSS8CCiKlW8D+hK6xqPAhyBLI/g7W1FBG44IV/j4n29"\
"ZEHxrFHPX+cPN1TcyGNxWlN/n2Lmn9go6pmH02+E843a/aX9QLnv0dyUK4U0vjsXQPFW8yTxsfkWMm+3S6JHENWugghAYnqhjMD5"\
"OwFtJAuhua6ZFoIvFoVPGweoiqBuvZk/NJBU0DwRgrMR8+YUBwX4nBW64whjdoncl4grPfAtQ1d4fIak3YzdWbNUCSk5Uidks1VB"\
"IXX5odxI/XX6/yb+uvlc2k31i2mDQ1n4F9PSKh1oWvZkYJxk/2JqcBND71qM7i1mY4q9GBfph94OyNW8kHWEg5lHE5yJHMfZC+Pz"\
"Oigt9QoO8YpvJ4RNpL+FR2N8DhoVBs4abFeLGRCPPnFKoT9Sx4W+vD92WYI/MdVCIqeiRNHQjBTEWjBVY1dTy/Ef29brFJVxot4c"\
"00uUKlfJkIJwKs+cNKFa+CeoqzKHyWAKOcDBMXQ7owQlMCJPqF52KCV/6Jpxkxudm9ToHDN2UrcNnSfgt06Qb72vEkT2Tp0gcy/K"\
"+ZEFcDAAD1cJcrbbHnupopNX1RmN0YEwyp3Q3oT1ky2X51VD9LH9VUTV9n+L6MUBdglSoO3Ynv6eEXhgTLKD/jzI+rK0xbSU0rJh"\
"n3SQVJA72b3oPnbKjaoT78xeJgdaOnwIpVV8PjHuuwDwhhMm8ClysPDMcVSyMhyZ7sg+X7l7J1uxfoZ//hpXQHaMoWufH3VpW9Ud"\
"XF5JD7g5QG1f8OieGSdvS/Lnwz/9zrbTGW2Nc3rM9OygueN85A0NOzu4RxZNRuZr/voEmu8owD+Jjx0skg0EwuAzqmzJgijC32R1"\
"0FOBGcHbfPlcLG38M+14YJZd+czqo/HUOcltaE2mN/8RsBBVOQfUlgCU/hjAGjlgSynQvIL/KU1b53jX7tV4d9hwKj11H7NkHWQ6"\
"gOaGR7C8dLodiJFsBkEQ4Vjmp35rPajd3oMK61ETfXz8Cw=="

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
    device.use_cfg64()
    config_dict = dashio.decode_cfg64(cfg)
    logging.debug("CFG: %s", json.dumps(config_dict, indent=4))
    controls = {}

    def up_btn_event_handler(msg):
        if controls['SLDR'].bar1_value < controls['SLDR'].bar_max:
            controls['SLDR'].bar1_value += 1
            controls['SLDR_DBL'].bar1_value += 0.5

    def down_btn_event_handler( msg):
        if controls['SLDR'].bar1_value > controls['SLDR'].bar_min:
            controls['SLDR'].bar1_value -= 1
            controls['SLDR_DBL'].bar1_value -= 0.5

    def slider_event_handler(msg):
        controls['SLDR'].slider_value = float(msg[3])
        controls['KNB'].knob_dial_value = float(msg[3])

    def slider_dbl_event_handler( msg):
        controls['SLDR_DBL'].slider_value = float(msg[3])
        controls['TestSelector'].position = int(float(msg[3]))

    def knob_event_handler(msg):
        controls['KNB'].knob_value = float(msg[3])
        controls['DIAL1'].dial_value = float(msg[3])
        controls['SLDR_DBL'].bar2_value = float(msg[3])
        controls['COMP1'].direction_text = msg[3]

    def text_cntrl_message_handler(msg):
        controls['TXT1'].text = msg[3]
        logging.info(msg)

    def selector_ctrl_handler(msg):
        print(controls['TestSelector'].selection_list[int(msg[3])])

    try:
        controls = dashio.load_controls_from_config(device, config_dict)
        controls['UP_BTN'].message_rx_event = up_btn_event_handler
        controls['DOWN_BTN'].message_rx_event = down_btn_event_handler
        controls['SLDR'].message_rx_event = slider_event_handler
        controls['SLDR_DBL'].message_rx_event = slider_dbl_event_handler
        controls['KNB'].message_rx_event = knob_event_handler
        controls['TXT1'].message_rx_event = text_cntrl_message_handler
        controls['TestSelector'].message_rx_event = selector_ctrl_handler
    except KeyError:
        logging.debug("%s", controls)
    device.config_revision = 1
    controls['TestSelector'].add_selection("First")
    controls['TestSelector'].add_selection("Second")
    controls['TestSelector'].add_selection("Third")
    controls['TestSelector'].add_selection("Forth")
    controls['TestSelector'].add_selection("Fifth")

    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
