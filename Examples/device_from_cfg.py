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

cfg = "tVfbbts4EP0VY561ruTEjq033xIE8SWwlXaBoigoibGJUKSXohqnQf59MRQpX6I08bb7JpEUOXPmnDnUMxBOVJZD+PWbB3GhtRRX"\
"ShabgxF8ebazY0FiTlMItSqoB4kUWkl+PYIQRvMvs++DaAYerClbrfWCaCYh9JtB0Gt32h6wRIoZySgulo8CPJD390PJpYIQFjTF"\
"AeHerxSluGRDFBXanBDRXEfDW/BAM833tjGvtzJnmkkBIQzmUTSfggePLNXrKo5W0Ds/P/dg65ZWM37Lg6dXo93Oi/eBxO9uP5z2"\
"3eYPJG02+Z9S9oOXb1hWLgtlSZDSHyyhQynu2QrCZxBFNjJDnxl9zCEMXjwo19iBr89mAyzqgJPkAQ55sqtiohUfPKxE6mpeLXcT"\
"kSIiNwxIniD0PTCfSJVS5b75smaaNpaZfKB4EH5p5ucCwnvCc2SpVvzt5VOyvZRCL9lPCmHLnhEhwQZy6z7bj8zN1QZnJnf7BZ0D"\
"2i//KYjCOEWRDSUvMoEAepCviaLlgJOWo7iFK2xk8Sbo/HXW5DIhHLBMKSO8FOeBDq/7kwDK2UvGq8xLgR1Js+X3LrpnHmRkC2Hg"\
"N30PMiZQtL4JMqbKyQJCGI5n0Xjxlig3kgm9K8yAF5jpRtGE5UaXLQ8UTT8TnAgv2nhEvpaPUyameLytVq6fjLYHfTzJwdBvjBjh"\
"bmAvpkrrhWA6hxCyT/kr5bfPet2gXaf81nmd8jtnJb6KJthSLMiE98UKY0OS7HW+4Xx6i4gfY2vbXm0HOwKr6nYHaDkobqXSn5aa"\
"qFgShW1yHxUbY8NG5GZ/BZHIfhuhsy4iRH9QoSdyZVvFSpHN2j4/CBm/JufNbGCpuVOWoQly+VJyLh/zGyHjig3HmFq+4u5uh5LY"\
"tQyuhX7HwZLwORXpXPCnuVhQTklOnQR/Qc7ZfDHtTxzWEEK/YcK2pakD/9CLTmVkcI54cxLTSvKlb1qZ7fNxgquuR8eMDFBwtYg4"\
"nl0t5nf79tpvmANdmu9lZQ6oMdc6hfmYTkZFYemSU04TLY3poH/s7hXYAJd29jglvxm0et1e8EZeO5nsbWAG30vFb55aoNI5c85S"\
"apOISWVStkgxUZbjS7OuYnlM1NK2veX46sgwl5PR4vtogGw7UkPvokz+DTWYDrtr57Wl34mh7MenaMHkcHQjdJCXCTZGsog52sAH"\
"UW/V9eiLbi2DAnM7+4Mgvwb4wrLrDYCPDfMdhP9Du3kf4hOwPfH6GxgT1MlmKIUojRDvf2zTT1NFc/TaoNdqBp1uM2gGLR/NXioN"\
"YbvT9l880HSrB3JLrQtwmdObOJ2LJRW1PxDR3xG66L1UGdEQwmw+G78uifuZeIjT6GmDPwH9CUqjFvu9y4dfBtTnbIW/CJPxZeSg"\
"M+0boz3FQ3/bQbumo2uW0avKNl/+BQ=="


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

    config_dict = dashio.decode_cfg64(cfg)
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
        logging.debug("%s",controls)

    controls['TestSelector'].add_selection("First")
    controls['TestSelector'].add_selection("Second")
    controls['TestSelector'].add_selection("Third")
    controls['TestSelector'].add_selection("Forth")
    controls['TestSelector'].add_selection("Fifth")

    global SHUTDOWN
    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
