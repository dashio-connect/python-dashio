#!/bin/python3

import time
import datetime
import random
import argparse
import signal
import dashio
import logging


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
        parser.add_argument("-n", "--device_name", dest="device_name", default="TestGraphs", help="IotDashboard Device name alias.")
        parser.add_argument("-u", "--username", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def gph_15_minutes_event_handler(self, msg):
        self.gph_15_minutes.send_graph()

    def __init__(self):
        self.bttn1_value = False
        LOGGER_PERIOD = 5
        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("Connecting to server: %s", args.server)
        logging.info("       Connection ID: %s", args.connection)
        logging.info("       Control topic: %s/%s/%s/control", args.username, args.connection, args.device_id)
        logging.info("          Data topic: %s/%s/%s/data", args.username, args.connection, args.device_id)

        device = dashio.dashDevice(args.connection, args.device_id, args.device_name)
        dash_conn = dashio.dashConnection(args.username, args.password)
        dash_conn.add_device(device)

        self.gph_15_minutes = dashio.TimeGraph("TestGraph")
        self.gph_15_minutes.title = "Test: {}".format(args.connection)
        self.gph_15_minutes.time_scale = dashio.TimeGraphTimeScale.FIFTEENMINS
        self.gph_15_minutes.y_axis_label = "Units"
        self.gph_15_minutes.y_axis_min = -10.0
        self.gph_15_minutes.y_axis_max = 10.0
        self.gph_15_minutes.y_axis_num_bars = 9
        self.line_15_minutes = dashio.TimeGraphLine(
            "Line", dashio.TimeGraphLineType.LINE, Color=dashio.Color.BLACK, max_data_points=15 * 60 / LOGGER_PERIOD
        )
        self.bar_15_minutes = dashio.TimeGraphLine(
            "Bar",
            dashio.TimeGraphLineType.BAR,
            transparency=0.45,
            Color=dashio.Color.ORANGE,
            max_data_points=15 * 60 / LOGGER_PERIOD,
        )
        self.bin_15_minutes = dashio.TimeGraphLine(
            "Bin",
            dashio.TimeGraphLineType.BOOL,
            transparency=0.45,
            Color=dashio.Color.YELLOW,
            max_data_points=15 * 60 / LOGGER_PERIOD,
        )
        self.am_pm_15_minutes = dashio.TimeGraphLine(
            "Hour",
            dashio.TimeGraphLineType.BOOL,
            transparency=0.30,
            Color=dashio.Color.SILVER,
            max_data_points=15 * 60 / LOGGER_PERIOD,
        )
        self.gph_15_minutes.add_line("line", self.line_15_minutes)
        self.gph_15_minutes.add_line("Bar", self.bar_15_minutes)
        self.gph_15_minutes.add_line("Bin", self.bin_15_minutes)
        self.gph_15_minutes.add_line("Hour", self.am_pm_15_minutes)
        self.gph_15_minutes.message_rx_event += self.gph_15_minutes_event_handler
        device.add_control(self.gph_15_minutes)

        line_data = 0
        bar_data = 0
        line_dir_up = True
        bar_dir_up = False
        bin_data = False
        am_pm_data = True
        t = datetime.datetime.now()
        if (t.hour % 2) == 0:
            am_pm_data = True
        else:
            am_pm_data = False
        while not self.shutdown:
            if line_data > 9.5:
                line_dir_up = False
            elif line_data < -9.5:
                line_dir_up = True
            if line_dir_up:
                line_data += random.random()
            else:
                line_data -= random.random()
            if bar_data > 9.5:
                bar_dir_up = False
            elif bar_data < -9.5:
                bar_dir_up = True
            if bar_dir_up:
                bar_data += random.random()
            else:
                bar_data -= random.random()
            if line_data > bar_data:
                bin_data = True
            else:
                bin_data = False
            if (t.hour % 2) == 0:
                am_pm_data = True
            else:
                am_pm_data = False
            self.am_pm_15_minutes.add_data_point(am_pm_data)
            self.line_15_minutes.add_data_point(line_data)
            self.bar_15_minutes.add_data_point(bar_data)
            self.bin_15_minutes.add_data_point(bin_data)
            self.gph_15_minutes.send_data()

            tstamp = datetime.datetime.now()
            seconds_left = tstamp.second + tstamp.microsecond / 1000000.0
            div, sleep_time = divmod(seconds_left, LOGGER_PERIOD)
            sleep_time = LOGGER_PERIOD - sleep_time
            time.sleep(sleep_time)

        device.close()


def main():
    tc = TestControls()


if __name__ == "__main__":
    main()
