#!/bin/python3
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
import signal
import time

import Adafruit_BBIO.ADC as ADC  # type: ignore

import dashio


class BBB_Temperature:
    def signal_cntrl_c(self, os_signal, os_frame):
        self.shutdown = True

    def init_logging(self, logfilename, level):
        log_level = logging.WARN
        if level == 1:
            log_level = logging.INFO
        elif level == 2:
            log_level = logging.DEBUG
        if not logfilename:
            formatter = logging.Formatter("%(asctime)s.%(msecs)03d, %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger = logging.getLogger()
            logger.addHandler(handler)
            logger.setLevel(log_level)
        else:
            logging.basicConfig(
                filename=logfilename,
                level=log_level,
                format="%(asctime)s.%(msecs)03d, %(message)s",
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
        parser.add_argument("-s", "--server", help="Server URL.", dest="server", default="dash.dashio.io")
        parser.add_argument(
            "-p", "--port", type=int, help="Port number.", default=1883, dest="port",
        )
        parser.add_argument(
            "-c", "--device_type", dest="device_type", default="Temperature", help="Device type"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="1234567890", help="IotDashboard Device ID.")
        parser.add_argument("-n", "--device_name", dest="device_name", default="Temps", help="IotDasboard name alias.")
        parser.add_argument("-u", "--username", help="dash Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="dash Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def read_sensor(self) -> float:
        ain_value = ADC.read("P9_39")
        ain_voltage = 1.8 * ain_value
        sensor_output_voltage = ain_voltage * 2
        f = sensor_output_voltage * 100
        c = (f - 32) * 5 / 9
        return c

    def __init__(self):
        LOGGER_PERIOD = 15

        ADC.setup()

        # Catch CNTRL-C signal
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("Connecting to server: %s", args.server)
        logging.info("       Device ID: %s", args.device_id)
        logging.info("       Control topic: %s/%s/control", args.username, args.device_id)
        logging.info("          Data topic: %s/%s/data", args.username, args.device_id)

        dash_con = dashio.DashConnection(args.username, args.password)
        device = dashio.Device(args.device_type, args.device_id, args.device_name)
        dash_con.add_device(device)

        gph_15_minutes = dashio.TimeGraph(
            "Temperature15M",
            title=f"Temp15M:{args.device_name}",
            y_axis_label="Degrees C",
            y_axis_min=0.0,
            y_axis_max=50.0,
            y_axis_num_bars=5
        )
        line_15_minutes = dashio.TimeGraphLine(
            "DegC",
            dashio.TimeGraphLineType.LINE,
            color=dashio.Color.BLACK,
            max_data_points=int(15 * 60 / LOGGER_PERIOD)
        )
        gph_15_minutes.add_line("DegC", line_15_minutes)

        gph_1_day = dashio.TimeGraph(
            "Temperature1D",
            title=f"Temp1D:{args.device_name}",
            y_axis_label="Degrees C",
            y_axis_min=0.0,
            y_axis_max=50.0,
            y_axis_num_bars=5
        )
        line_1_day = dashio.TimeGraphLine(
            "DegC", dashio.TimeGraphLineType.LINE, color=dashio.Color.BLACK, max_data_points=24 * 4
        )
        gph_1_day.add_line("DegC", line_1_day)

        gph_1_week = dashio.TimeGraph(
            "Temperature1W",
            title=f"Temp1W:{args.device_name}",
            y_axis_label="Degrees C",
            y_axis_min=0.0,
            y_axis_max=50.0,
            y_axis_num_bars=5
        )
        line_1_week = dashio.TimeGraphLine(
            "DegC", dashio.TimeGraphLineType.LINE, color=dashio.Color.BLACK, max_data_points=24 * 4 * 7
        )
        gph_1_week.add_line("DegC", line_1_week)

        gph_1_year = dashio.TimeGraph(
            "Temperature1Y",
            title=f"Temp1Y:{args.device_name}",
            y_axis_label="Degrees C",
            y_axis_min=0.0,
            y_axis_max=50.0,
            y_axis_num_bars=5
        )
        line_1_year = dashio.TimeGraphLine(
            "DegC", dashio.TimeGraphLineType.LINE, color=dashio.Color.BLACK, max_data_points=360
        )
        gph_1_year.add_line("DegC", line_1_year)

        dl_temperature_ctrl = dashio.Dial(
            "TemperatureDial",
            title="Temperature",
            dial_max=50
        )
        dl_daily_max_ctrl = dashio.Dial(
            "TemperatureMaxDial",
            title="Daily Max",
            dial_max=50
        )

        dl_daily_min_ctrl = dashio.Dial(
            "TemperatureMinDial",
            title="Daily Min",
            dial_max=50
        )
        self.page = dashio.DeviceView("tmppage", "Temperatures")
        device.add_control(self.page)
        device.add_control(dl_temperature_ctrl)
        self.page.add_control(dl_temperature_ctrl)
        device.add_control(dl_daily_max_ctrl)
        self.page.add_control(dl_daily_max_ctrl)
        device.add_control(dl_daily_min_ctrl)
        self.page.add_control(dl_daily_min_ctrl)
        device.add_control(gph_15_minutes)
        self.page.add_control(gph_15_minutes)
        device.add_control(gph_1_day)
        self.page.add_control(gph_1_day)
        device.add_control(gph_1_week)
        self.page.add_control(gph_1_week)
        device.add_control(gph_1_year)
        self.page.add_control(gph_1_year)

        temperature = self.read_sensor()
        daily_temperature_max = temperature
        daily_temperature_min = temperature

        while not self.shutdown:
            temperature = self.read_sensor()
            if temperature < daily_temperature_min:
                daily_temperature_min = temperature
                dl_daily_min_ctrl.dial_value = temperature
            if temperature > daily_temperature_max:
                daily_temperature_max = temperature
                dl_daily_max_ctrl.dial_value = temperature
            dl_temperature_ctrl.dial_value = temperature
            line_15_minutes.add_data_point(temperature)
            gph_15_minutes.send_data()
            t_now = datetime.datetime.now()
            if (t_now.minute == 0 or t_now.minute == 15 or t_now.minute == 30 or t_now.minute == 45) and (t_now.second < 5):
                total = 0
                for d in line_15_minutes.data.data:
                    temps = d.data_point
                    total += float(temps)
                avg = total / len(line_15_minutes.data.data)
                avg_str = f"{avg:.2f}"
                line_1_day.add_data_point(avg_str)
                line_1_week.add_data_point(avg_str)
                gph_1_day.send_data()
                gph_1_week.send_data()
                if t_now.hour == 12 and t_now.minute == 0 and t_now.second < 10:
                    daily_temperature_max = temperature
                    daily_temperature_min = temperature
                    line_1_year.add_data_point(avg_str)
                    gph_1_year.send_data()
            t_now = datetime.datetime.now()

            seconds_left = t_now.second + t_now.microsecond / 1000000.0
            _, sleep_time = divmod(seconds_left, LOGGER_PERIOD)
            sleep_time = LOGGER_PERIOD - sleep_time
            time.sleep(sleep_time)
        device.close()


if __name__ == "__main__":
    BBB_Temperature()
