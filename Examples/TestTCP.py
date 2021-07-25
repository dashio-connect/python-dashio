#!/bin/python3
from dashio.iotcontrol.enums import DialNumberPosition, DialStyle, DirectionStyle, Precision
import time
import random
import argparse
import signal
import dashio
import logging
import platform


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
        parser.add_argument("-u", "--url", help="Host URL.", dest="url", default="tcp://*")
        parser.add_argument(
            "-c", "--connection_name", dest="connection", default="TestTCP", help="IotDashboard Connection name"
        )
        parser.add_argument("-d", "--device_id", dest="device_id", default="00001", help="IotDashboard Device ID.")
        parser.add_argument("-p", "--port", dest="port", type=int, default=5650, help="Port number")
        parser.add_argument(
            "-n", "--device_name", dest="device_name", default="TCPTest", help="Alias name for device."
        )
        parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
        args = parser.parse_args()
        return args

    def up_btn_event_handler(self, msg):
        if self.sldr_cntrl.bar1_value < self.sldr_cntrl.bar_max:
            self.sldr_cntrl.bar1_value += 1
            self.sldr_dbl_cntrl.bar1_value += 0.5

    def down_btn_event_handler(self, msg):
        if self.sldr_cntrl.bar1_value > self.sldr_cntrl.bar_min:
            self.sldr_cntrl.bar1_value -= 1
            self.sldr_dbl_cntrl.bar1_value -= 0.5

    def slider_event_handler(self, msg):
        self.sldr_cntrl.slider_value = float(msg[3])
        self.knb_control.knob_dial_value = float(msg[3])

    def slider_dbl_event_handler(self, msg):
        self.sldr_dbl_cntrl.slider_value = float(msg[3])
        self.selector_ctrl.position = int(float(msg[3]))

    def knob_event_handler(self, msg):
        self.knb_control.knob_value = float(msg[3])
        self.dl_control.dial_value = float(msg[3])
        self.sldr_dbl_cntrl.bar2_value = float(msg[3])
        self.comp_control.direction_text = float(msg[3])

    def text_cntrl_message_handler(self, msg):
        self.device.send_popup_message("TCPTest", "Text Box message", msg[3])
        self.text_cntrl.text = "Popup sent: " + msg[3]
        logging.info(msg)

    def selector_ctrl_handler(self, msg):
        print(self.selector_ctrl.selection_list[int(msg[3])])

    def __init__(self):

        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info("   Serving on: %s:%s", args.url, str(args.port))
        logging.info("Connection ID: %s", args.connection)
        logging.info("    Device ID: %s", args.device_id)
        logging.info("  Device Name: %s", args.device_name)
        self.tcp_con = dashio.TCPConnection()
        self.device = dashio.Device(args.connection, args.device_id, args.device_name)
        self.tcp_con.add_device(self.device)

        self.connection = args.connection
        self.page_name = "TestTCP: " + platform.node()

        self.page_test = dashio.DeviceView("TestTCP", self.page_name)
        self.up_btn = dashio.Button("UP_BTN", control_position=dashio.ControlPosition(0.02, 0.01, 0.22, 0.12))
        self.up_btn.btn_state = dashio.ButtonState.OFF
        self.up_btn.icon_name = dashio.Icon.UP
        self.up_btn.on_color = dashio.Color.GREEN
        self.up_btn.text = ""
        self.up_btn.title = "Up"
        self.up_btn.message_rx_event = self.up_btn_event_handler
        self.page_test.add_control(self.up_btn)

        self.down_btn = dashio.Button(
            "DOWN_BTN", control_position=dashio.ControlPosition(0.02, 0.86, 0.22, 0.12)
        )
        self.down_btn.btn_state = dashio.ButtonState.OFF
        self.down_btn.icon_name = dashio.Icon.DOWN
        self.down_btn.on_color = dashio.Color.GREEN
        self.down_btn.text = ""
        self.down_btn.title = "Down"
        self.down_btn.message_rx_event = self.down_btn_event_handler
        self.page_test.add_control(self.down_btn)

        self.sldr_cntrl = dashio.SliderSingleBar(
            "SLDR", control_position=dashio.ControlPosition(0.02, 0.13, 0.22, 0.73)
        )
        self.sldr_cntrl.title = "Slider"
        self.sldr_cntrl.bar_max = 10
        self.sldr_cntrl.slider_enabled = True
        self.sldr_cntrl.red_value = 10
        self.sldr_cntrl.message_rx_event += self.slider_event_handler
        self.page_test.add_control(self.sldr_cntrl)

        self.sldr_dbl_cntrl = dashio.SliderDoubleBar(
            "SLDR_DBL", control_position=dashio.ControlPosition(0.78, 0.01, 0.2, 0.98)
        )
        self.sldr_dbl_cntrl.title = "Slider Double"
        self.sldr_dbl_cntrl.bar_max = 5
        self.sldr_dbl_cntrl.slider_enabled = True
        self.sldr_dbl_cntrl.red_value = 5
        self.sldr_dbl_cntrl.message_rx_event += self.slider_dbl_event_handler
        self.page_test.add_control(self.sldr_dbl_cntrl)

        self.knb_control = dashio.Knob("KNB", control_position=dashio.ControlPosition(0.24, 0.14, 0.54, 0.21))
        self.knb_control.title = "A Knob"
        self.knb_control.dial_max = 10
        self.knb_control.red_value = 10
        self.knb_control.message_rx_event += self.knob_event_handler
        self.page_test.add_control(self.knb_control)

        self.dl_control = dashio.Dial(
            "DIAL1",
            style=DialStyle.BAR,
            units="m/s",
            number_position=DialNumberPosition.CENTER,
            precision=Precision.TWO,
            control_position=dashio.ControlPosition(0.24, 0.63, 0.54, 0.21)
        )
        self.dl_control.title = "A Dial"
        self.dl_control.dial_max = 10
        self.page_test.add_control(self.dl_control)

        self.text_cntrl = dashio.TextBox(
            "TXT1", control_position=dashio.ControlPosition(0.24, 0.84, 0.54, 0.12)
        )
        self.text_cntrl.text = "Hello"
        self.text_cntrl.title = "A text control"
        self.text_cntrl.keyboard_type = dashio.Keyboard.ALL_CHARS
        self.text_cntrl.close_keyboard_on_send = True
        self.text_cntrl.message_rx_event += self.text_cntrl_message_handler
        self.page_test.add_control(self.text_cntrl)

        self.alarm_ctrl = dashio.Alarm("TestingAlarms", "Test Alarms")
        self.device.add_control(self.alarm_ctrl)
        self.comp_control = dashio.Direction(
            "COMP1",
            style=DirectionStyle.DEGPS,
            units="nm",
            precision=Precision.TWO,
            control_position=dashio.ControlPosition(0.24, 0.38, 0.54, 0.22)
        )
        self.comp_control.title = "A Direction control"
        self.comp_control.direction_text = "00"
        self.page_test.add_control(self.comp_control)

        self.selector_ctrl = dashio.Selector(
            "TestSelector", "A Selector", control_position=dashio.ControlPosition(0.24, 0.01, 0.54, 0.13)
        )
        self.selector_ctrl.message_rx_event += self.selector_ctrl_handler
        self.selector_ctrl.add_selection("First")
        self.selector_ctrl.add_selection("Second")
        self.selector_ctrl.add_selection("Third")
        self.selector_ctrl.add_selection("Forth")
        self.selector_ctrl.add_selection("Fifth")

        self.page_test.add_control(self.selector_ctrl)

        self.label_ctrl = dashio.Label(
            "LabelID",
            "A label",
            style=dashio.LabelStyle.GROUP,
            color=dashio.Color.BLUE,
            control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 1.0),
        )
        self.page_test.add_control(self.label_ctrl)

        self.device.add_control(self.label_ctrl)
        self.device.add_control(self.page_test)
        self.device.add_control(self.selector_ctrl)
        self.device.add_control(self.comp_control)
        self.device.add_control(self.text_cntrl)
        self.device.add_control(self.dl_control)
        self.device.add_control(self.knb_control)
        self.device.add_control(self.sldr_dbl_cntrl)
        self.device.add_control(self.sldr_cntrl)
        self.device.add_control(self.down_btn)
        self.device.add_control(self.up_btn)

        while not self.shutdown:
            time.sleep(5)
            self.comp_control.direction_value = random.random() * 360

        self.device.send_popup_message("TestControls", "Shutting down", "Goodbye")
        self.tcp_con.close()
        self.device.close()


def main():
    tc = TestControls()


if __name__ == "__main__":
    main()
