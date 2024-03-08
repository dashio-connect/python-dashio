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
import platform
import signal
import time
from datetime import datetime

import shortuuid
import zmq
from sense_hat import SenseHat  # type: ignore

import dashio


class SenseGraphTS:

    def color_to_rgb(self, color_value):
        """Return (red, green, blue) for the color."""
        clr = color_value.lstrip('#')
        lv = len(clr)
        return tuple(int(clr[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def __init__(self, config, context):

        # Catch CNTRL-C signal
        self.shutdown = False
        self.tcp_con = dashio.TCPConnection()
        self.dash_con = dashio.DashConnection(username=config['DEFAULT']['DashUsername'], password=config['DEFAULT']['DashPassword'], context=context)
        self.device = dashio.Device(config['DEFAULT']['DeviceType'], config['DEFAULT']['DeviceID'], config['DEFAULT']['DeviceName'], context=context)
        self.tcp_con.add_device(self.device)
        self.dash_con.add_device(self.device)

        self.page_name = "SenseHat: " + platform.node()
        self.page1_thp = dashio.DeviceView("SHDials", "SenseHat Dials", icon=dashio.Icon.WEATHER)
        self.page2_thp = dashio.DeviceView("SHTemperature", "Temperature Humidity", icon=dashio.Icon.TEMPERATURE)
        self.page3_thp = dashio.DeviceView("SHPressure", "SenseHat Pressure", icon=dashio.Icon.FAN)
        self.temperature_dial = dashio.Dial(
            "tempC",
            "Temperature",
            dial_max=50,
            red_value=50,
            units="C",
            precision=dashio.Precision.FOUR,
            control_position=dashio.ControlPosition(0, 0, 0.3, 0.2)
        )

        self.humidity_dial = dashio.Dial(
            "Hum",
            "Humidity",
            dial_max=100,
            red_value=100,
            units="%",
            precision=dashio.Precision.FOUR,
            control_position=dashio.ControlPosition(0.35, 0, 0.3, 0.2)
        )
        self.pressure_dial = dashio.Dial(
            "pres",
            "Pressure",
            dial_max=1100,
            red_value=1100,
            units="mb",
            precision=dashio.Precision.FOUR,
            control_position=dashio.ControlPosition(0.7, 0, 0.3, 0.2)
        )

        self.page1_thp.add_control(self.temperature_dial)
        self.page1_thp.add_control(self.humidity_dial)
        self.page1_thp.add_control(self.pressure_dial)
        self.g_line_temperature = dashio.TimeGraphLine(
            "Temperature",
            dashio.TimeGraphLineType.LINE,
            color=dashio.Color.RED,
            max_data_points=100
        )
        self.temp_hum = dashio.TimeGraph(
            "temp_hum",
            "Temperature Humidity",
            control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.4),
            y_axis_label='Temperature',
            y_axis_label_rt='Humidity',
            y_axis_min=10,
            y_axis_max=40,
            y_axis_min_rt=0,
            y_axis_max_rt=100,

        )
        self.temp_hum.add_line("temp_line", self.g_line_temperature)
        self.page2_thp.add_control(self.temp_hum)

        self.g_line_humidity = dashio.TimeGraphLine(
            "Humidity",
            dashio.TimeGraphLineType.LINE,
            color=dashio.Color.BLUE,
            max_data_points=100,
            right_axis=True
        )
        self.temp_hum.add_line("humidity_line", self.g_line_humidity)

        self.g_line_pressure = dashio.TimeGraphLine(
            "Pressure",
            dashio.TimeGraphLineType.LINE,
            color=dashio.Color.RED,
            max_data_points=100
        )
        self.pressure_graph = dashio.TimeGraph(
            "shpress_graph",
            "SenseHat Pressure",
            control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.4),
            y_axis_min=900,
            y_axis_max=1100
        )
        self.pressure_graph.add_line("pressure_line", self.g_line_pressure)
        self.page3_thp.add_control(self.pressure_graph)

        self.device.add_control(self.temperature_dial)
        self.device.add_control(self.humidity_dial)
        self.device.add_control(self.pressure_dial)

        self.device.add_control(self.temp_hum)
        self.device.add_control(self.pressure_graph)

        self.device.add_control(self.page1_thp)
        self.device.add_control(self.page2_thp)
        self.device.add_control(self.page3_thp)


SHUTDOWN = False

_graph = False
_dial = False


def signal_cntrl_c(os_signal, os_frame):
    global SHUTDOWN
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
    parser.add_argument("-i", "--inifile", help="ini filename", dest="ini_file", default="sense_hat.ini")
    parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args


def parse_config(filename: str) -> dict:

    config_dict = {
        'changed': False,
        'filename': filename
    }
    new_ini_file = False

    config_file_parser = configparser.ConfigParser()
    config_file_parser.defaults()

    try:
        ini_f = open(filename)
        ini_f.close()
    except FileNotFoundError:
        default = {
            'DeviceID': shortuuid.uuid(),
            'DeviceName': "TestSenseHatGraphs",
            'DeviceType': "SenseHatGraphs",
            'DashUsername': 'username',
            'DashPassword': 'password'
        }
        config_file_parser['DEFAULT'] = default
        with open(filename, 'w') as configfile:
            config_file_parser.write(configfile)
        new_ini_file = True

    if not new_ini_file:
        config_file_parser.read(filename)
        default = {
            'DeviceID': config_file_parser.get('DEFAULT', 'DeviceID'),
            'DeviceName': config_file_parser.get('DEFAULT', 'DeviceName'),
            'DeviceType': config_file_parser.get('DEFAULT', 'DeviceType'),
            'DashUsername': config_file_parser.get('DEFAULT', 'DashUsername'),
            'DashPassword': config_file_parser.get('DEFAULT', 'DashPassword')

        }
    config_dict['DEFAULT'] = default
    return config_dict


def main():

    # Catch CNTRL-C signal
    global SHUTDOWN
    signal.signal(signal.SIGINT, signal_cntrl_c)

    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)
    config_dict = parse_config(args.ini_file)
    context = zmq.Context.instance()
    dash_sense_hat = SenseGraphTS(config_dict, context)

    sense_hat = SenseHat()

    def _get_data():
        humidity = sense_hat.get_humidity()
        temperature = sense_hat.get_temperature()
        pressure = sense_hat.get_pressure()
        return humidity, temperature, pressure

    def _send_graph_data():
        dash_sense_hat.pressure_graph.send_data()
        dash_sense_hat.temp_hum.send_data()

    def get_graph_data(humidity, temperature, pressure):
        dash_sense_hat.g_line_humidity.add_data_point(humidity)
        dash_sense_hat.g_line_pressure.add_data_point(pressure)
        dash_sense_hat.g_line_temperature.add_data_point(temperature)

    def send_dial_data(humidity, temperature, pressure):
        dash_sense_hat.humidity_dial.dial_value = humidity
        dash_sense_hat.temperature_dial.dial_value = temperature
        dash_sense_hat.pressure_dial.dial_value = pressure

    minute_counter = 0
    # Start the background thread
    now = datetime.now()
    while not SHUTDOWN:
        delta = datetime.now() - now
        _, minute_remainder = divmod(delta.seconds, 60)
        if minute_remainder == 0:
            minute_counter += 1
            logging.debug("Sending Dial data")
            h, t, p = _get_data()
            send_dial_data(h, t, p)

            if minute_counter == 15:
                minute_counter = 0
                logging.debug("Sending Graph data")
                get_graph_data(h, t, p)
                _send_graph_data()

        tstamp = datetime.now()
        seconds_left = tstamp.second + tstamp.microsecond / 1000000.0
        _, sleep_time = divmod(seconds_left, 1)
        sleep_time = 1 - sleep_time
        time.sleep(sleep_time)

    # Stop the background thread
    dash_sense_hat.tcp_con.close()
    dash_sense_hat.device.close()


if __name__ == "__main__":
    main()
