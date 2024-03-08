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
import datetime
import logging
import platform
import signal
import time

from sense_hat import SenseHat  # type: ignore

import dashio


class TestColorPicker:
    def signal_cntrl_c(self, os_signal, os_frame):
        self.shutdown = True

    def init_logging(self, logfilename, level):
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

    def parse_commandline_arguments(self):
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
        parser.add_argument(
            "-c", "--connection_name", dest="connection", default="TestBLE", help="IotDashboard Connection name"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="00011000", help="IotDashboard Device ID.")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="ColorPicker", help="Alias name for device."
        )
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def color_picker_handler(self, msg):
        print(msg)
        self.c_picker.color_value = msg[3]
        try:
            self.sense.clear(self.color_to_rgb(msg[3]))
        except ValueError:
            pass

    def color_to_rgb(self, color_value):
        """Return (red, green, blue) for the color."""
        clr = color_value.lstrip('#')
        lv = len(clr)
        return tuple(int(clr[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def __init__(self):

        # Catch CNTRL-C signal
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("   Serving on: TCP")
        logging.info("Connection ID: %s", args.connection)
        logging.info("    Device ID: %s", args.device_id)
        logging.info("  Device Name: %s", args.device_name)

        self.sense = SenseHat()
        self.tcp_con = dashio.TCPConnection()
        self.device = dashio.Device(args.connection, args.device_id, args.device_name)
        self.tcp_con.add_device(self.device)

        self.connection = args.connection
        self.page_name = "Color Picker: " + platform.node()

        self.page_test = dashio.DeviceView("Color Picker", self.page_name)
        self.c_picker = dashio.ColorPicker("CPKR1", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.45))
        self.c_picker.add_receive_message_callback(self.color_picker_handler)
        self.page_test.add_control(self.c_picker)
        self.device.add_control(self.c_picker)
        self.device.add_control(self.page_test)

        self.page_thp = dashio.DeviceView("THPView", "Temperature Humidity Pressure")
        self.temperature_dial = dashio.Dial(
            "tempC",
            "Temperature",
            dial_max=50,
            red_value=50,
            units="C"
        )

        self.humidity_dial = dashio.Dial(
            "Hum",
            "Humidity",
            dial_max=100,
            red_value=100,
            units="%"
        )
        self.pressure_dial = dashio.Dial(
            "pres",
            "Pressure",
            dial_max=1100,
            red_value=1100,
            units="mb"
        )

        self.page_thp.add_control(self.temperature_dial)
        self.page_thp.add_control(self.humidity_dial)
        self.page_thp.add_control(self.pressure_dial)
        self.device.add_control(self.temperature_dial)
        self.device.add_control(self.humidity_dial)
        self.device.add_control(self.pressure_dial)
        self.device.add_control(self.page_thp)

        INTERVAL = 10
        time_now = datetime.datetime.utcnow()
        while not self.shutdown:
            self.humidity_dial.dial_value = self.sense.get_humidity()
            self.temperature_dial.dial_value = self.sense.get_temperature()
            self.pressure_dial.dial_value = self.sense.get_pressure()
            time_now = datetime.datetime.utcnow()
            seconds_left = time_now.second + time_now.microsecond / 1000000.0
            div, sleep_time = divmod(seconds_left, INTERVAL)
            sleep_time = INTERVAL - sleep_time
            # print ("Div: %.2f, sleep_time: %.2f" % (div, sleep_time))
            time.sleep(sleep_time)
        self.tcp_con.close()
        self.device.close()


if __name__ == "__main__":
    TestColorPicker()
