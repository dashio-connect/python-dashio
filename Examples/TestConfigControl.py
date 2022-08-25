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
        parser.add_argument("-s", "--server", help="Server URL.", dest="server", default="mqtt://localhost")
        parser.add_argument(
            "-p", "--port", type=int, help="Port number.", default=1883, dest="port",
        )
        parser.add_argument(
            "-c", "--connection_name", dest="connection", default="TestMQTT", help="IotDashboard Connection name"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="00001", help="IotDashboard Device ID.")
        parser.add_argument("-n", "--device_name", dest="device_name", default="TestConfig", help="IotDashboard Device name alias.")
        parser.add_argument("-u", "--username", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def selector_ctrl_handler(self, msg):
        self.selector_ctrl.position = int(msg[3])

    def __init__(self):

        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("Connecting to server: %s", args.server)
        logging.info("       Connection ID: %s", args.connection)
        logging.info("       Control topic: %s/%s/%s/control", args.username, args.connection, args.device_id)
        logging.info("          Data topic: %s/%s/%s/data", args.username, args.connection, args.device_id)

        device = dashio.Device(args.connection, args.device_id, args.device_name)
        dash_conn = dashio.DashConnection(args.username, args.password)
        dash_conn.add_device(device)

        self.tmpage = dashio.DeviceView("tmpage", "Test Alarm")
        self.test_menu = dashio.Menu("TestTheMenu", control_position=dashio.ControlPosition(0.3, 0.5, 0.5, 0.5))
        self.test_page = dashio.DeviceView("TestCFG", "Test the Menus")
        device.add_control(self.test_page)

        self.up_btn = dashio.Button("UP_BTN")
        self.up_btn.btn_state = dashio.ButtonState.OFF
        self.up_btn.icon_name = dashio.Icon.UP
        self.up_btn.on_color = dashio.Color.GREEN
        self.up_btn.text = "Up Button"
        self.up_btn.title = "Up"
        device.add_control(self.up_btn)
        self.test_menu.add_control(self.up_btn)

        self.down_btn = dashio.Button("DOWN_BTN")
        self.down_btn.btn_state = dashio.ButtonState.OFF
        self.down_btn.icon_name = dashio.Icon.DOWN
        self.down_btn.on_color = dashio.Color.GREEN
        self.down_btn.text = ""
        self.down_btn.title = "Down"
        device.add_control(self.down_btn)
        self.test_menu.add_control(self.down_btn)

        self.sldr_cntrl = dashio.Slider("SLDR")
        self.sldr_cntrl.title = "Slider"
        self.sldr_cntrl.bar_max = 10
        self.sldr_cntrl.slider_enabled = True
        device.add_control(self.sldr_cntrl)
        self.test_menu.add_control(self.sldr_cntrl)

        self.text_cntrl1 = dashio.TextBox("TXT1")
        self.text_cntrl1.text = "Test box1"
        self.text_cntrl1.title = "TextBx1"
        self.text_cntrl1.keyboard_type = dashio.Keyboard.ALL
        device.add_control(self.text_cntrl1)
        self.test_menu.add_control(self.text_cntrl1)

        self.text_cntrl2 = dashio.TextBox("TXT2")
        self.text_cntrl2.text = "Test box2"
        self.text_cntrl2.title = "TextBx2"
        self.text_cntrl2.keyboard_type = dashio.Keyboard.ALL
        device.add_control(self.text_cntrl2)
        self.test_menu.add_control(self.text_cntrl2)

        self.selector_ctrl = dashio.Selector("TestSelector", "A Selector")
        self.selector_ctrl.message_rx_event += self.selector_ctrl_handler
        self.selector_ctrl.add_selection("First")
        self.selector_ctrl.add_selection("Second")
        self.selector_ctrl.add_selection("Third")
        self.selector_ctrl.add_selection("Forth")
        self.selector_ctrl.add_selection("Fifth")
        device.add_control(self.selector_ctrl)
        self.test_menu.add_control(self.selector_ctrl)
        self.test_page.add_control(self.test_menu)
        self.button_group_test = dashio.ButtonGroup("TestButtonGRP", "A group of buttons")
        self.test_page.add_control(self.button_group_test)
        self.button_group_test.add_button(self.up_btn)
        self.button_group_test.add_button(self.down_btn)
        device.add_control(self.test_menu)
        device.add_control(self.button_group_test)

        while not self.shutdown:
            time.sleep(5)

        device.close()


def main():
    tc = TestControls()


if __name__ == "__main__":
    main()
