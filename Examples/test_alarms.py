#!/bin/python3

import time
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
            formatter = logging.Formatter("%(asctime)s.%(msecs)03d, %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger = logging.getLogger()
            logger.addHandler(handler)
            logger.setLevel(log_level)
        else:
            logging.basicConfig(
                filename=logfilename,
                level=log_level,
                format="%(asctime)s.%(msecs)03d, %(message)s",
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
            "-c", "--connection_name", dest="connection", default="TestAlarms", help="IotDashboard Connection name"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="00001", help="IotDashboard Device ID.")
        parser.add_argument("-n", "--device_name", dest="device_name", default="TestAlarms", help="IotDashboard Device name alias.")
        parser.add_argument("-u", "--username", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def alarm_btn1_handler(self, msg):
        logging.debug(msg)
        self.alarm1_ctrl.send()

    def alarm_btn2_handler(self, msg):
        logging.debug(msg)
        self.alarm2_ctrl.send()

    def alarm_btn3_handler(self, msg):
        logging.debug(msg)
        self.alarm3_ctrl.send()

    def __init__(self):
        self.shutdown = False

        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        args = self.parse_commandline_arguments()

        self.init_logging(args.logfilename, args.verbose)

        logging.info("Connecting to server: %s", args.server)
        logging.info("       Connection ID: %s", args.connection)
        logging.info("       Control topic: %s/%s/%s/control", args.username, args.connection, args.device_id)
        logging.info("          Data topic: %s/%s/%s/data", args.username, args.connection, args.device_id)

        self.ic = dashio.mqttConnectionThread(
            args.connection, args.device_id, args.device_name, args.server, args.port, args.username, args.password, use_ssl=True
        )
        self.ic.start()
        self.tapage = dashio.Page("testAlarm", "Test Alarm")
        self.alarm_btn1 = dashio.Button("ALARM_BTN1")
        self.tapage.add_control(self.alarm_btn1)
        self.alarm_btn1.title = "A1"
        self.alarm_btn1.btn_state = dashio.ButtonState.OFF
        self.alarm_btn1.icon_name = dashio.Icon.BELL
        self.alarm_btn1.on_colour = dashio.Colour.RED
        self.alarm_btn1.text_colour = dashio.Colour.BLUE
        self.alarm_btn1.message_rx_event += self.alarm_btn1_handler
        self.ic.add_control(self.alarm_btn1)

        self.alarm_btn2 = dashio.Button("ALARM_BTN2")
        self.alarm_btn2.title = "A2"
        self.alarm_btn2.btn_state = dashio.ButtonState.OFF
        self.alarm_btn2.icon_name = dashio.Icon.BELL
        self.alarm_btn2.on_colour = dashio.Colour.RED
        self.alarm_btn2.text_colour = dashio.Colour.BLUE
        self.alarm_btn2.message_rx_event += self.alarm_btn2_handler
        self.ic.add_control(self.alarm_btn2)
        self.tapage.add_control(self.alarm_btn2)

        self.alarm_btn3 = dashio.Button("ALARM_BTN3")
        self.alarm_btn3.title = "A3"
        self.alarm_btn3.btn_state = dashio.ButtonState.OFF
        self.alarm_btn3.icon_name = dashio.Icon.BELL
        self.alarm_btn3.on_colour = dashio.Colour.RED
        self.alarm_btn3.text_colour = dashio.Colour.BLUE
        self.alarm_btn3.message_rx_event += self.alarm_btn3_handler
        self.ic.add_control(self.alarm_btn3)
        self.tapage.add_control(self.alarm_btn3)

        self.alarm1_ctrl = dashio.Alarm("TestingAlarms1", "Alarm1", "Hello from Alarm1", "Alarm1")
        self.alarm2_ctrl = dashio.Alarm("TestingAlarms2", "Alarm2", "Hello from Alarm2", "Alarm2")
        self.alarm3_ctrl = dashio.Alarm("TestingAlarms3", "Alarm3", "Hello from Alarm3", "Alarm3")
        self.ic.add_control(self.alarm1_ctrl)
        self.ic.add_control(self.alarm2_ctrl)
        self.ic.add_control(self.alarm3_ctrl)
        self.tapage.add_control(self.alarm1_ctrl)
        self.tapage.add_control(self.alarm2_ctrl)
        self.tapage.add_control(self.alarm3_ctrl)
        self.ic.add_control(self.tapage)

        while not self.shutdown:
            time.sleep(1)

        self.ic.running = False


def main():
    tc = TestControls()


if __name__ == "__main__":
    main()
