#!/bin/python3

from dashio.iotcontrol.enums import SoundName
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
            "-t", "--device_type", dest="device_type", default="TestAlarms", help="IotDashboard device type"
        )
        parser.add_argument(
            "-p", "--port", type=int, help="Port number.", default=5650, dest="port",
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="101010101010101", help="IotDashboard Device ID.")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="TestAlarms", help="Alias name for device."
        )
        parser.add_argument("-u", "--user_name", help="MQTT Username", dest="username", default="")
        parser.add_argument("-w", "--password", help="MQTT Password", default="")
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def alarm_btn1_handler(self, msg):
        logging.debug(msg)
        self.alarm1_ctrl.send("Alarm1", "Hello from alarm1")

    def alarm_btn2_handler(self, msg):
        logging.debug(msg)
        self.alarm2_ctrl.send("Alarm2", "Hello from alarm2")

    def alarm_btn3_handler(self, msg):
        logging.debug(msg)
        self.alarm3_ctrl.send("Alarm3", "Hello from alarm3")

    def __init__(self):
        self.shutdown = False

        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        args = self.parse_commandline_arguments()

        self.init_logging(args.logfilename, args.verbose)

        logging.info("Connecting to server: %s", args.server)
        logging.info("           Device ID: %s", args.device_id)
        logging.info("       Control topic: %s/%s/control", args.username, args.device_id)
        logging.info("          Data topic: %s/%s/data", args.username, args.device_id)

        device = dashio.DashDevice(args.device_type, args.device_id, args.device_name)
        dash_conn = dashio.DashConnection(args.username, args.password)
        dash_conn.add_device(device)

        self.tapage = dashio.Page("testAlarm", "Test Alarm")
        self.alarm_btn1 = dashio.Button("ALARM_BTN1")
        self.tapage.add_control(self.alarm_btn1)
        self.alarm_btn1.title = "A1"
        self.alarm_btn1.btn_state = dashio.ButtonState.OFF
        self.alarm_btn1.icon_name = dashio.Icon.BELL
        self.alarm_btn1.on_color = dashio.Color.RED
        self.alarm_btn1.message_rx_event += self.alarm_btn1_handler
        device.add_control(self.alarm_btn1)

        self.alarm_btn2 = dashio.Button("ALARM_BTN2")
        self.alarm_btn2.title = "A2"
        self.alarm_btn2.btn_state = dashio.ButtonState.OFF
        self.alarm_btn2.icon_name = dashio.Icon.BELL
        self.alarm_btn2.on_color = dashio.Color.RED
        self.alarm_btn2.message_rx_event += self.alarm_btn2_handler
        device.add_control(self.alarm_btn2)
        self.tapage.add_control(self.alarm_btn2)

        self.alarm_btn3 = dashio.Button("ALARM_BTN3")
        self.alarm_btn3.title = "A3"
        self.alarm_btn3.btn_state = dashio.ButtonState.OFF
        self.alarm_btn3.icon_name = dashio.Icon.BELL
        self.alarm_btn3.on_color = dashio.Color.RED
        self.alarm_btn3.message_rx_event += self.alarm_btn3_handler
        device.add_control(self.alarm_btn3)
        self.tapage.add_control(self.alarm_btn3)

        self.alarm1_ctrl = dashio.Alarm("TestingAlarms1", "A plop form Alarm1", SoundName.PLOP)
        self.alarm2_ctrl = dashio.Alarm("TestingAlarms2", "Squeaky from Alarm2", SoundName.SQUEAKY)
        self.alarm3_ctrl = dashio.Alarm("TestingAlarms3", "Whoosh from Alarm3", SoundName.WHOOSH)
        device.add_control(self.alarm1_ctrl)
        device.add_control(self.alarm2_ctrl)
        device.add_control(self.alarm3_ctrl)
        self.tapage.add_control(self.alarm1_ctrl)
        self.tapage.add_control(self.alarm2_ctrl)
        self.tapage.add_control(self.alarm3_ctrl)
        device.add_control(self.tapage)

        while not self.shutdown:
            time.sleep(1)

        device.close()


def main():
    tc = TestControls()


if __name__ == "__main__":
    main()
