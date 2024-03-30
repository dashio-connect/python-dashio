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
import logging
import signal
import time

import dashio


class TestControls:
    def signal_cntrl_c(self, os_signal, os_frame):
        self.shutdown = True

    def init_logging(self, logfilename, level):
        log_level = logging.WARN
        if level == 1:
            log_level = logging.INFO
        elif level == 2:
            log_level = logging.DEBUG
        if not logfilename:
            formatter = logging.Formatter("[%(asctime)s][%(module)20s] -- %(message)s")
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
        parser.add_argument("-s", "--server", help="Server URL.", dest="server", default="dash.dashio.io")
        parser.add_argument("-q", "--hostname", help="Host URL.", dest="hostname", default="tcp://*")
        parser.add_argument(
            "-t", "--device_type", dest="device_type", default="TestAlarms", help="IotDashboard device type"
        )
        parser.add_argument(
            "-p", "--port", type=int, help="Port number.", default=5650, dest="port",
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="101010101010101", help="IotDashboard Device ID.")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="TestAlarms", help="Alias name for device."
        )
        parser.add_argument("-u", "--user_name", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def alarm_btn1_handler(self, msg):
        logging.debug(msg)
        self.alarm1_ctrl.send("Alarm1", "Hello from alarm1")

    def alarm_btn2_handler(self, msg):
        logging.debug(msg)
        self.alarm2_ctrl.send("Alarm2", "Hello from alarm2")

    def alarm_btn3_handler(self, msg):
        logging.debug(msg)
        self.alarm3_ctrl.send("Alarm3", "Hello from alarm3")

    def __init__(self):
        self.shutdown = False

        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        args = self.parse_commandline_arguments()

        self.init_logging(args.logfilename, args.verbose)

        logging.info("Connecting to server: %s", args.server)
        logging.info("           Device ID: %s", args.device_id)
        logging.info("       Control topic: %s/%s/control", args.username, args.device_id)
        logging.info("          Data topic: %s/%s/data", args.username, args.device_id)

        device = dashio.Device(args.device_type, args.device_id, args.device_name)
        dash_conn = dashio.DashConnection(args.username, args.password)
        dash_conn.add_device(device)

        self.tadevice_view = dashio.DeviceView("testAlarm", "Test Alarm")
        self.alarm_btn1 = dashio.Button(
            "ALARM_BTN1",
            title="A1",
            icon_name=dashio.Icon.BELL,
            on_color=dashio.Color.RED,
            control_position=dashio.ControlPosition(0.0, 0.03125, 0.2727272727272, 0.1875)
        )
        self.tadevice_view.add_control(self.alarm_btn1)
        self.alarm_btn1.add_receive_message_callback(self.alarm_btn1_handler)
        device.add_control(self.alarm_btn1)

        self.alarm_btn2 = dashio.Button(
            "ALARM_BTN2",
            title="A2",
            icon_name=dashio.Icon.BELL,
            on_color=dashio.Color.RED,
            control_position=dashio.ControlPosition(0.3636363636363636, 0.03125, 0.2727272727272, 0.1875)
        )
        self.alarm_btn2.add_receive_message_callback(self.alarm_btn2_handler)
        device.add_control(self.alarm_btn2)
        self.tadevice_view.add_control(self.alarm_btn2)

        self.alarm_btn3 = dashio.Button(
            "ALARM_BTN3",
            title="A3",
            icon_name=dashio.Icon.BELL,
            on_color=dashio.Color.RED,
            control_position=dashio.ControlPosition(0.7272727272727, 0.03125, 0.2727272727272, 0.1875)
        )
        self.alarm_btn3.add_receive_message_callback(self.alarm_btn3_handler)
        device.add_control(self.alarm_btn3)
        self.tadevice_view.add_control(self.alarm_btn3)

        self.alarm1_ctrl = dashio.Alarm("TestingAlarms1")
        self.alarm2_ctrl = dashio.Alarm("TestingAlarms2")
        self.alarm3_ctrl = dashio.Alarm("TestingAlarms3")
        device.add_control(self.alarm1_ctrl)
        device.add_control(self.alarm2_ctrl)
        device.add_control(self.alarm3_ctrl)
        device.add_control(self.tadevice_view)

        while not self.shutdown:
            time.sleep(1)

        device.close()


if __name__ == "__main__":
    TestControls()
