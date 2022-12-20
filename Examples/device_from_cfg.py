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

cfg = "tZdbc6pIEID/SorX48kKxkvyxk1zQUFATbm7lUIYlQgDgSFeUue/bw+gohhj6px9SY09PdPdX/d0kw9GERTm7u8PZq0FsUvcAOsW"\
"/GXuqhVm6Tpknv9kKwxxiYe2WswdI6imqXaZChOTtYdA0NHVgQa/QytCmDxIIDJRTEyRCpPEdUCg6OLSMb1VX/MfyTiy0eRHrdaH"\
"fTvAJAq89JRiTRBd5TZBwl95VJbqeUFErXsJgp+rsttz5M7mZOv3r38rzFNPFdIgcyeMSf9mFNUWxsrYxKyshXPU3SwLkfRUvcsr"\
"R1499QSqgrCjYm+tYh15yIpBnUQJqjC+tQJz1U/Cj5AztKjLqco+rCccTJgjn6vX3Fnc82DZdXGX2ptaXgy2S8m7Zm8qzALuFnNc"\
"OnLgqONaXjvwvGAZp4a356lcPARbTH71un5zAvU1B1LfBeeqlLKhSHqRsv1a695M48ggVkIGosaPO7JCUx17roMiGVsTD7zK8RVJ"\
"05teJEH5Enf9S9r1PWwjNXslBQnYLTO/bf0u8yp7ivnEinLkmQO7C2DjLHPuFPJmKz1o5IVqyB1ml4PKDn3z7b7Vb99z/Q03Rg8b"\
"acHzzdvlpei/xP7NKs/jLhFv1n6XOFv7s8RPIq9ynyOHsjflZ7NY9tN11Kk+rlmTJM+qpT86HVnUZke9xHw22U87JXZJDJKD9kfQ"\
"ilzlN5RJstwZkvQo77kzKlTktgmiaRD5FkkbXU9mTpFtwdMOI2S7cXobZHMxccx1mHqjKN9oELYXxOhpAuVkQFFldUS5SQ+H3eKt"\
"ObXWGjaXjfaPTbhWubcmSrtFzl2SO5pxhFFUu9qnHI97KlfkKbkQHPW1ANW2PB7PqEL1DM5terB/ElwNHmgYuJigXa11IoQwc8CT"\
"u5QfJdXlNSBFF3JvkK0UtZMt+KGULTq6dp+tDEU09dMzPW1RZcOfxnpukpvNgT0zycicWjXhvbWptpWnGX9c53DKgA5ikyA6qOeC"\
"8HTZHFd4jZIQFT2LURoOR2mI2+oQeONBpMZJ5EHPaIMPhruBHQ5yOYtcB5KR+BgSR+sgnkNgmWTb2HDi71TYchBZ6PR2IYicfW5H"\
"c5egK8MPFmi7v5hhZ99mLHuRb3xxxIwsHKfA7XVagfbRHVt4uTt3V6+Wj+Kf/iRkGz+5ay+A+s0vNKmqEKxOubHdK9mjlHRomsxd"\
"jSuo7lGyjQrjApge2KWN8C2B00z2lnml+JhHxJ5i+8fSiPyB02rf3LND9MQXHrPA66UHUUROL6QP+9Jx06wfPm7rRJM8+1GVfhm5"\
"3i5J2SQpP6BGrfS881ECBTRBUeFuUe6ZcjpMy6Pssse/bzb+P3/FzMHU2b93wTR7RfhCVXzAtx3dCBvimKsPiDmYm3T4B9PpYXgH"\
"xNVR70WAm2DYJYQE+OgjIcBH8V7Sc9lCz5WCJWbOZODEDGpkw4tJZ+Glo7pQob0AQ33uP4saQ8t/7upOfzjajJO6+Mqtxhr/FZmB"\
"9r9yGYTfo0Jb+B+gkhZOJx8sYhvGyQfjoHfXRgYiSQh6GNQrS3fqVogdvoRBRCpZMFDpUqo5dNEyb5fTmY7e6b9bv/4D"

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
        controls = dashio.load_all_controls_from_config(device, config_dict)
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
