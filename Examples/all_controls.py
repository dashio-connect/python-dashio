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
import platform
import random
import signal
import time
import json
import dashio

DEVICE_CFG64 = "zVhRc+I2EP4rHj27KSYHDbzZ4HA3AczYPnKdtnNjbAGaCInaJsBl8t+7km2wjQGT9mY6eYml3dXut9/uSrwh1/zmou4fb8jnLA45"\
"/dJHXeR+czWkorUXYhbLFZ3SXiIQwcaGkTiCVfg3JjHFQkCJ8S5WUiuwscRksYxtLyYcdRt391qzlUpPeERglYGWYbmuNRJmQFmn"\
"ZCEWh+ajC0tzHq68GL7H1tiE732md7DZfvgNbK5D7JNI2muo6GUWuPu19Gg4BK0tCeJlqqGpaFc2oiKf8gg/zQKLOZgFqBuHG/z+"\
"l4r60+mzRCaK9zJEw7L7pu2AUT8O6cjbPUKwDvkBe02wswhJ0ON0s2IATbOpomgJ+CUriVUVsc3qIHKvFjAvIixOMHgY4BDkeQj7"\
"z0sSY8VZ8Rec7b8sWJBtG9TzX9KNKypu6LFI5tbfJwiUbBxySqmS+dRVVrO11v7l/o5y36OpPVdIGnxX5UW2d3KcAMrmWwFBMyd6"\
"RFNrq4gANmNvJdxw/t6ANhI5MVx3LHPC5/PsTBsHqAjlCLONAYIqmm3imDOTeTOKgywJnB3d3eAiz0fm+OspeZtHTIRtJTGLLvD5"\
"hKwJxZOayXNSGq9gZS7+MWcQvXolaAj4+8CefCRoA/S0i1HrivH/DPl6uIMQY3apmZWj1mRX+VeRH4ycif9To9PoVHWjO+1B/BWw"\
"MDClkvxPY8soNKSxZY/0YQmUp7EBKxG0MovRvcVsTLEX4QyYlbeDAmtcwCPEwdQTHJFiRxyeGJ9dhqsKm2jJtyPCRuLYuUcjXEmU"\
"F7BdzHNAPPrIKYU+IQ/OlMV6icl1sW11xBZAQMSoEIgOjaEE9DSBD5/uRVil6XE+yjQjA9v6OkF51Kg3w/QS/fK5G6bCfjHAcija"\
"SRa0VrvZEhGN9AlEBP84w76dkIUSmCKl8sgfKiV/AmMcefApY9o/hzAzL0z5kh6cacPGRcJkJVfRkUDVSTPrmAOUpw60zM8Jd/Qd"\
"iUYkuX3sxIfMYpQpWuNSkqVmKprpJUYSoC8hvSvKHWk2CL31EuUdQMfrWRXMpaS0KlHel6zJ7/FmZXghTO9Welx+4cp1qymg04ej"\
"hKP9L3pSf7krXPNYTIZul6ATCmJQ3ULJYjPvE6/icpo2MdlzCKVFYt3e9tecsBiXWQd3vxkOc4Z65tg17WrK39rTshv56s9fowJP"\
"nWHPtc80ufvbmtwRRQc6hB/zsG5fc3EU53Su97NGBzyTHdoanHH+g74zxXwFh5UhX9T13hRO1PH60IX1af+M163OR932NgHhyiuJ"\
"Nh7NPbNqRaBPtVoBJN4b7mBSG3QYlaJ9Ni8EkbvLiNtzgUnJ5QraF9+s60aTXVfT29XByEIYUbYkXiqu2EpeGlOCt9koO3/fKmcy"\
"QaI3PFM6H8igItuBMiH+C65dOL3vkyfRIdZSKxspz59NU1z7zo7s65mWpS9CdKsHWaF604lVd0idjpYjCC5Z4cOwKoyX3xUPvm7r"\
"t62KkVRnAslX3pkCbTf/W4anC7XSnb4+D8SWj808oW8m8CO0zzcU4FfiYwfHUGRdxMBTdUvmRI19UXQwmPpSQJRK+sPEfGHjVzFC"\
"xJS2C6+OvjmYOGWeWqNJrV+M2KoATp/A5Bfx5Dqa71GdLYRA4wLk1RO8olBLw/jwHCxcOeqO2wRtWTe9iUB2zUNIVavdEu/XtR4E"\
"IY5EnFqneae1H+40yEQDvb//Aw=="


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
        self.comp_control.direction_text = msg[3]

    def text_cntrl_message_handler(self, msg):
        self.text_cntrl.text = msg[3]
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
        logging.info("    Device ID: %s", args.device_id)
        logging.info("  Device Name: %s", args.device_name)
        
        config_dict = dashio.decode_cfg64(DEVICE_CFG64)
        logging.debug("CFG: %s", json.dumps(config_dict, indent=4))
        
        self.tcp_con = dashio.TCPConnection()
        self.device = dashio.Device("AllControlsTest", args.device_id, args.device_name, config_dict)
        self.tcp_con.add_device(self.device)

        self.page_name = "All Controls: " + platform.node()
        self.page_test = dashio.get_control_from_config("AllControls", config_dict)
        self.avd = dashio.get_control_from_config("AV1", config_dict)
        self.avd.url = "https://bit.ly/swswift"
        self.btn_group = dashio.get_control_from_config("BGRP1", config_dict)
        self.group_btn = dashio.get_control_from_config("BTN_GRP", config_dict)
        self.btn = dashio.get_control_from_config("BTN", config_dict)
        self.clr_picker = dashio.get_control_from_config("C_PKR", config_dict)
        self.comp_control = dashio.get_control_from_config("COMP1", config_dict)
        self.dl_control = dashio.get_control_from_config("DIAL1", config_dict)
        self.event_log = dashio.get_control_from_config("ELOG", config_dict)
        self.graph = dashio.get_control_from_config("GRPH", config_dict)
        self.knb_control = dashio.get_control_from_config("KNB", config_dict)
        self.label_ctrl = dashio.get_control_from_config("Label", config_dict)
        self.menu = dashio.get_control_from_config("MENU", config_dict)
        self.menu_btn = dashio.get_control_from_config("MenuBTN", config_dict)
        self.selector_ctrl = dashio.get_control_from_config("TestSelector", config_dict)
        self.selector_ctrl.add_selection("First")
        self.selector_ctrl.add_selection("Second")
        self.selector_ctrl.add_selection("Third")
        self.selector_ctrl.add_selection("Forth")
        self.selector_ctrl.add_selection("Fifth")

        self.sldr_cntrl = dashio.get_control_from_config("SLDR", config_dict)
        self.text_cntrl = dashio.get_control_from_config("TXT1", config_dict)
        self.t_graph = dashio.get_control_from_config("TGRPH", config_dict)

        self.device.add_control(self.avd)
        self.device.add_control(self.btn_group)
        self.device.add_control(self.group_btn)
        self.device.add_control(self.btn)
        self.device.add_control(self.clr_picker)
        self.device.add_control(self.dl_control)
        self.device.add_control(self.comp_control)
        self.device.add_control(self.event_log)
        self.device.add_control(self.graph)
        self.device.add_control(self.knb_control)
        self.device.add_control(self.label_ctrl)
        self.device.add_control(self.menu)
        self.device.add_control(self.menu_btn)
        self.device.add_control(self.selector_ctrl)
        self.device.add_control(self.sldr_cntrl)
        self.device.add_control(self.text_cntrl)
        self.device.add_control(self.t_graph)

        self.device.add_control(self.page_test)

        while not self.shutdown:
            time.sleep(5)
            self.comp_control.direction_value = random.random() * 360

        self.tcp_con.close()
        self.device.close()


def main():
    ac = AllControls()


if __name__ == "__main__":
    main()
