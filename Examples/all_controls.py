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
import random
import signal
import time
import json
import dashio

DEVICE_CFG64 = "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"


class AllControls:
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
        parser.add_argument("-u", "--url", help="Host URL.", dest="url", default="tcp://*")
        parser.add_argument("-d", "--device_id", dest="device_id", default="12345678987654321", help="IotDashboard Device ID.")
        parser.add_argument("-p", "--port", dest="port", type=int, default=5650, help="Port number")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="AllControls", help="Alias name for device."
        )
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    config_dict = dashio.decode_cfg64(DEVICE_CFG64)

    def selector_ctrl_handler(self, msg):
        print(self.selector_ctrl.selection_list[int(msg[3])])

    def __init__(self):

        # Catch CNTRL-C signal
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("   Serving on: %s:%s", args.url, str(args.port))
        logging.info("    Device ID: %s", args.device_id)
        logging.info("  Device Name: %s", args.device_name)

        config_dict = dashio.decode_cfg64(DEVICE_CFG64)
        logging.debug("CFG: %s", json.dumps(config_dict, indent=4))

        self.tcp_con = dashio.TCPConnection()
        self.device = dashio.Device("AllControlsTest", args.device_id, args.device_name, cfg_dict=config_dict)
        self.device.use_cfg64()
        self.device.config_revision = 5
        self.tcp_con.add_device(self.device)

        self.avd: dashio.AudioVisualDisplay = self.device.get_control(dashio.ControlName.AVD, "AV1")
        self.avd.url = "https://bit.ly/swswift"
        self.comp_control: dashio.Direction = self.device.get_control(dashio.ControlName.DIR, "COMP1")
        self.selector_ctrl: dashio.Selector = self.device.get_control(dashio.ControlName.SLCTR, "TestSelector")
        self.selector_ctrl.add_selection("First")
        self.selector_ctrl.add_selection("Second")
        self.selector_ctrl.add_selection("Third")
        self.selector_ctrl.add_selection("Forth")
        self.selector_ctrl.add_selection("Fifth")

        while not self.shutdown:
            time.sleep(5)
            self.comp_control.direction_value = random.random() * 360

        self.tcp_con.close()
        self.device.close()


if __name__ == "__main__":
    AllControls()
