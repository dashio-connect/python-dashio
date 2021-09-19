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


class TestEventLog:
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
            "-c", "--connection_name", dest="connection", default="TestEventLog", help="IotDashboard Connection name"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="00001", help="IotDashboard Device ID.")
        parser.add_argument("-n", "--device_name", dest="device_name", default="SystemMon", help="IotDashboard Device name alias.")
        parser.add_argument("-u", "--username", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def __init__(self):
        self.bttn1_value = False

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

        event_l = dashio.EventLog("ELTest")
        el_page = dashio.DeviceView("el_page", "Event Log Test")
        el_page.add_control(event_l)
        device.add_control(event_l)
        device.add_control(el_page)

        self.connection = args.connection
        count = 1
        while not self.shutdown:
            time.sleep(5)
            event_l.add_event_data("Hello:{}".format(count))
            count += 1
        device.close()


def main():
    tc = TestEventLog()


if __name__ == "__main__":
    main()
