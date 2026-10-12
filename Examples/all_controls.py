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
    "+et/"


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
                            No number means info. Default is info.""",
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
        self.selector_ctrl: dashio.Selector = self.device.get_control(dashio.ControlName.SLCTR, "testSel")
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
