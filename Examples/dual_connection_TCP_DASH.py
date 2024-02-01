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
import platform
import random
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
        parser.add_argument("-s", "--server", help="Server URL.", dest="server", default="dash.dashio.io")
        parser.add_argument("-q", "--hostname", help="Host URL.", dest="hostname", default="tcp://*")
        parser.add_argument(
            "-t", "--device_type", dest="device_type", default="TestDualTCPDash", help="IotDashboard device type"
        )
        parser.add_argument(
            "-p", "--port", type=int, help="Port number.", default=5650, dest="port",
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="00001", help="IotDashboard Device ID.")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="DualTCPDash-Name", help="Alias name for device."
        )
        parser.add_argument("-u", "--user_name", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def up_btn_event_handler(self, msg):
        if self.sldr_cntrl.bar1_value < self.sldr_cntrl.bar_max:
            self.sldr_cntrl.bar1_value += 1.0
            self.sldr_dbl_cntrl.bar1_value += 1.0

    def down_btn_event_handler(self, msg):
        if self.sldr_cntrl.bar1_value > self.sldr_cntrl.bar_min:
            self.sldr_cntrl.bar1_value -= 1.0
            self.sldr_dbl_cntrl.bar1_value -= 1.0

    def slider_event_handler(self, msg):
        self.sldr_cntrl.slider_value = float(msg[3])
        self.knb_control.knob_dial_value = float(msg[3])

    def slider_dbl_event_handler(self, msg):
        self.sldr_dbl_cntrl.slider_value = float(msg[3])
        self.selector_ctrl.position = int(float(msg[3]))

    def knob_event_handler(self, msg):
        self.knb_control.knob_value = float(msg[3])
        self.dl_control.dial_value = float(msg[3])
        self.sldr_dbl_cntrl.bar2_value = float(msg[3])

    def text_cntrl_message_handler(self, msg):
        self.alarm_ctrl.send("Text Box", msg[3])
        self.text_cntrl.text = "Alarm sent: " + msg[3]
        logging.info(msg)

    def selector_ctrl_handler(self, msg):
        print(self.selector_ctrl.selection_list[int(msg[3])])

    def name_handler(self, msg):
        print(msg)
        return msg[2]

    def wifi_handler(self, msg):
        print(msg)
        return True

    def dashio_handler(self, msg):
        print(msg)
        return True

    def tcp_handler(self, msg):
        print(msg)
        return True

    def mqtt_handler(self, msg):
        print(msg)
        return True

    def __init__(self):

        # Catch CNTRL-C signal
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("   Serving on: %s", args.server)
        logging.info("  Device Type: %s", args.device_type)
        logging.info("    Device ID: %s", args.device_id)
        logging.info("  Device Name: %s", args.device_name)

        self.device = dashio.Device(args.device_type, args.device_id, args.device_name, add_actions=True)

        self.device.set_dashio_callback(self.dashio_handler)
        self.device.set_wifi_callback(self.wifi_handler)
        self.device.set_name_callback(self.name_handler)
        self.device.set_tcp_callback(self.tcp_handler)
        self.device.set_mqtt_callback(self.mqtt_handler)
        self.device.use_cfg64()
        self.dash_con = dashio.DashConnection(args.username, args.password)
        self.tcp_con = dashio.TCPConnection()
        self.tcp_con.add_device(self.device)
        self.dash_con.add_device(self.device)

        self.page_name = "TestTCP: " + platform.node()

        self.page_test = dashio.DeviceView("TestTCP", self.page_name)
        self.up_btn = dashio.Button(
            "UP_BTN",
            title="Up",
            icon_name=dashio.Icon.UP,
            on_color=dashio.Color.GREEN,
            control_position=dashio.ControlPosition(0.02, 0.01, 0.22, 0.12)
        )
        self.up_btn.btn_state = dashio.ButtonState.OFF
        self.up_btn.add_receive_message_callback(self.up_btn_event_handler)
        self.page_test.add_control(self.up_btn)

        self.down_btn = dashio.Button(
            "DOWN_BTN",
            on_color=dashio.Color.GREEN,
            title="Down",
            text="",
            icon_name=dashio.Icon.DOWN,
            control_position=dashio.ControlPosition(0.02, 0.86, 0.22, 0.12)
        )
        self.down_btn.add_receive_message_callback(self.down_btn_event_handler)
        self.page_test.add_control(self.down_btn)

        self.sldr_cntrl = dashio.Slider(
            "SLDR",
            title="Slider",
            bar_max=10,
            slider_enabled=True,
            red_value=10,
            control_position=dashio.ControlPosition(0.02, 0.13, 0.22, 0.73)
        )
        self.sldr_cntrl.add_receive_message_callback(self.slider_event_handler)
        self.page_test.add_control(self.sldr_cntrl)

        self.sldr_dbl_cntrl = dashio.Slider(
            "SLDR_DBL",
            bar_max=5,
            slider_enabled=True,
            red_value=5,
            title="Slider Double",
            control_position=dashio.ControlPosition(0.78, 0.01, 0.2, 0.98)
        )
        self.sldr_dbl_cntrl.add_receive_message_callback(self.slider_dbl_event_handler)
        self.sldr_dbl_cntrl.bar2_value = 0
        self.page_test.add_control(self.sldr_dbl_cntrl)

        self.knb_control = dashio.Knob(
            "KNB",
            title="A Knob",
            dial_max=10,
            red_value=10,
            control_position=dashio.ControlPosition(0.24, 0.14, 0.54, 0.21)
        )
        self.knb_control.add_receive_message_callback(self.knob_event_handler)
        self.page_test.add_control(self.knb_control)

        self.dl_control = dashio.Dial(
            "DIAL1",
            title="A Dial",
            dial_max=10,
            control_position=dashio.ControlPosition(0.24, 0.63, 0.54, 0.21)
        )
        self.page_test.add_control(self.dl_control)

        self.text_cntrl = dashio.TextBox(
            "TXT1",
            title="A text control",
            text="Hello",
            keyboard_type=dashio.Keyboard.ALL,
            close_keyboard_on_send=True,
            control_position=dashio.ControlPosition(0.24, 0.84, 0.54, 0.12)
        )
        self.text_cntrl.add_receive_message_callback(self.text_cntrl_message_handler)
        self.page_test.add_control(self.text_cntrl)

        self.alarm_ctrl = dashio.Alarm("alarm1")
        self.device.add_control(self.alarm_ctrl)
        self.comp_control = dashio.Direction(
            "COMP1",
            title="A Direction control",
            control_position=dashio.ControlPosition(0.24, 0.38, 0.54, 0.22)
        )
        self.page_test.add_control(self.comp_control)

        self.selector_ctrl = dashio.Selector(
            "TestSelector",
            "A Selector",
            control_position=dashio.ControlPosition(0.24, 0.01, 0.54, 0.13)
        )
        self.selector_ctrl.add_receive_message_callback(self.selector_ctrl_handler)
        self.selector_ctrl.add_selection("First")
        self.selector_ctrl.add_selection("Second")
        self.selector_ctrl.add_selection("Third")
        self.selector_ctrl.add_selection("Forth")
        self.selector_ctrl.add_selection("Fifth")

        self.page_test.add_control(self.selector_ctrl)

        self.label_ctrl = dashio.Label(
            "LabelID",
            "A label",
            style=dashio.LabelStyle.GROUP,
            color=dashio.Color.BLUE,
            control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 1.0),
        )
        self.page_test.add_control(self.label_ctrl)

        self.device.add_control(self.label_ctrl)
        self.device.add_control(self.page_test)
        self.device.add_control(self.selector_ctrl)
        self.device.add_control(self.comp_control)
        self.device.add_control(self.text_cntrl)
        self.device.add_control(self.dl_control)
        self.device.add_control(self.knb_control)
        self.device.add_control(self.sldr_dbl_cntrl)
        self.device.add_control(self.sldr_cntrl)
        self.device.add_control(self.down_btn)
        self.device.add_control(self.up_btn)
        self.device.add_control(self.alarm_ctrl)

        while not self.shutdown:
            time.sleep(5)
            self.comp_control.direction_value = random.random() * 360

        self.device.close()


if __name__ == "__main__":
    TestControls()
