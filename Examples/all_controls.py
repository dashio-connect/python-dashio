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

        # Catch CNTRL-C signel
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
