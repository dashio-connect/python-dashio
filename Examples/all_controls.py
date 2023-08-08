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

DEVICE_CFG64 = "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"\
    "r38B"


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
