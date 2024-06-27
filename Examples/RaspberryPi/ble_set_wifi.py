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
import os
import signal
import time
import uuid

import shortuuid

import dashio
from dashio import ble_connection

shutdown = False


def signal_cntrl_c(os_signal, os_frame):
    global shutdown
    shutdown = True


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
    parser.add_argument("-n", "--device_name", dest="device_name", default="SetWifiName", help="IotDashboard Device name alias.")
    parser.add_argument("-i", "--inifile", help="ini filename", dest="ini_file", default="set_wifi.ini")
    parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args


def CreateWifiConfig(country, SSID, password):
    config_lines = [
        'country={}'.format(country),
        'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
        'update_config=1',
        '\n',
        'network={',
        '    ssid="{}"'.format(SSID),
        '    psk="{}"'.format(password),
        '}'
    ]
    config = '\n'.join(config_lines)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as wifi:
        wifi.write(config)
    os.system("systemctl restart networking.service")


def set_wifi_callback(msg):
    try:
        CreateWifiConfig(msg[2], msg[3], msg[4])
    except KeyError:
        return False
    return True


def main():
    # Catch CNTRL-C signal
    global shutdown
    signal.signal(signal.SIGINT, signal_cntrl_c)

    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)

    new_ini_file = False
    ini_file = args.ini_file
    config_file_parser = configparser.ConfigParser()
    config_file_parser.defaults()

    try:
        ini_f = open(ini_file)
        ini_f.close()
    except FileNotFoundError:
        default = {
            'DeviceID': shortuuid.uuid(),
            'DeviceName': args.device_name,
            'DeviceType': 'SetWifi',
            'BLE_UUID': str(uuid.uuid4())
        }
        config_file_parser['DEFAULT'] = default
        with open(ini_file, 'w') as configfile:
            config_file_parser.write(configfile)
        new_ini_file = True

    if not new_ini_file:
        config_file_parser.read(ini_file)

    device = dashio.Device(
        config_file_parser.get('DEFAULT', 'DeviceType'),
        config_file_parser.get('DEFAULT', 'DeviceID'),
        config_file_parser.get('DEFAULT', 'DeviceName')
    )

    def set_name_callback(msg):
        config_file_parser.set('DEFAULT', 'DeviceName', msg[2])
        with open(ini_file, 'w') as configfile:
            config_file_parser.write(configfile)
        return msg[2]

    device.set_wifi_callback(set_wifi_callback)
    device.set_name_callback(set_name_callback)

    dash_conn = ble_connection.BLEConnection(ble_uuid=config_file_parser.get('DEFAULT', 'BLE_UUID'))
    dash_conn.add_device(device)

    while not shutdown:
        time.sleep(1)
    dash_conn.close()
    device.close()


if __name__ == "__main__":
    main()
