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
