#!/bin/python3

import time
import datetime
import random
import argparse
import sys
import signal
import dashio
import platform
import psutil
import logging

class TestControls():

    def signal_cntrl_c(self, os_signal, os_frame):
        self.shutdown = True

    def init_logging(self, logfilename, level):
        if level == 0:
            log_level = logging.WARN
        elif level == 1:
            log_level = logging.INFO
        elif level == 2:
            log_level = logging.DEBUG
        if not logfilename:
            formatter = logging.Formatter('%(asctime)s.%(msecs)03d, %(message)s')
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger = logging.getLogger()
            logger.addHandler(handler)
            logger.setLevel(log_level)
        else:
            logging.basicConfig(filename=logfilename,
                                level=log_level,
                                format='%(asctime)s.%(msecs)03d, %(message)s',
                                datefmt="%Y-%m-%d %H:%M:%S")
        logging.info('==== Started ====')

    def parse_commandline_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-v",
                            "--verbose",
                            const=1,
                            default=1,
                            type=int,
                            nargs="?",
                            help='''increase verbosity:
                            0 = only warnings, 1 = info, 2 = debug.
                            No number means info. Default is no verbosity.''')
        parser.add_argument("-s",
                            "--server",
                            help="Server URL.",
                            dest='server',
                            default='mqtt://localhost')
        parser.add_argument("-p",
                            "--port",
                            type=int,
                            help="Port number.",
                            default=1883,
                            dest='port',)
        parser.add_argument("-c",
                            "--connection_name",
                            dest="connection",
                            default='TestMQTT',
                            help="IotDashboard Connection name")
        parser.add_argument("-u",
                            "--username",
                            help="MQTT Username",
                            dest='username',
                            default='')
        parser.add_argument("-w",
                            "--password",
                            help='MQTT Password',
                            default='')
        parser.add_argument("-l",
                            "--logfile",
                            dest="logfilename",
                            default="",
                            help="logfile location",
                            metavar="FILE")
        args = parser.parse_args()
        return args

    def selector_ctrl_handler(self, msg):
        self.selector_ctrl.position = int(msg[1])

    def __init__(self):

        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info('Connecting to server: %s', args.server)
        logging.info('       Connection ID: %s', args.connection)
        logging.info('       Control topic: %s/%s/control', args.username, args.connection)
        logging.info('          Data topic: %s/%s/data', args.username, args.connection)

        self.ic = dashio.iotConnectionThread(args.connection, args.server, args.port, args.username, args.password, use_ssl=True)
        self.ic.start()

        self.test_menu = dashio.Menu("TestTheMenu")

        self.up_btn = dashio.Button('UP_BTN')
        self.up_btn.btn_state = dashio.ButtonState.OFF
        self.up_btn.icon_name = dashio.Icon.UP
        self.up_btn.on_colour = dashio.Colour.GREEN
        self.up_btn.text = 'Up Button'
        self.up_btn.text_colour = dashio.Colour.WHITE
        self.up_btn.title = 'Up'
        self.ic.add_control(self.up_btn)
        self.test_menu.add_control(self.up_btn)

        self.down_btn = dashio.Button('DOWN_BTN')
        self.down_btn.btn_state = dashio.ButtonState.OFF
        self.down_btn.icon_name = dashio.Icon.DOWN
        self.down_btn.on_colour = dashio.Colour.GREEN
        self.down_btn.text = ''
        self.down_btn.text_colour = dashio.Colour.WHITE
        self.down_btn.title = 'Down'
        self.ic.add_control(self.down_btn)
        self.test_menu.add_control(self.down_btn)

        self.sldr_cntrl = dashio.SliderSingleBar('SLDR')
        self.sldr_cntrl.title = 'Slider'
        self.sldr_cntrl.max = 10
        self.sldr_cntrl.slider_enabled = True
        self.sldr_cntrl.red_value
        self.ic.add_control(self.sldr_cntrl)
        self.test_menu.add_control(self.sldr_cntrl)

        self.text_cntrl1 = dashio.TextBox('TXT1')
        self.text_cntrl1.text = 'Test box1'
        self.text_cntrl1.title = 'TextBx1'
        self.text_cntrl1.keyboard_type = dashio.Keyboard.ALL_CHARS
        self.text_cntrl1.close_key_board_on_send = True
        self.ic.add_control(self.text_cntrl1)
        self.test_menu.add_control(self.text_cntrl1)

        self.text_cntrl2 = dashio.TextBox('TXT2')
        self.text_cntrl2.text = 'Test box2'
        self.text_cntrl2.title = 'TextBx2'
        self.text_cntrl2.keyboard_type = dashio.Keyboard.ALL_CHARS
        self.text_cntrl2.close_key_board_on_send = True
        self.ic.add_control(self.text_cntrl2)
        self.test_menu.add_control(self.text_cntrl2)

        self.selector_ctrl = dashio.Selector('TestSelector', 'A Selector')
        self.selector_ctrl.message_rx_event += self.selector_ctrl_handler
        self.selector_ctrl.add_selection('First')
        self.selector_ctrl.add_selection('Second')
        self.selector_ctrl.add_selection('Third')
        self.selector_ctrl.add_selection('Forth')
        self.selector_ctrl.add_selection('Fifth')
        self.ic.add_control(self.selector_ctrl)
        self.test_menu.add_control(self.selector_ctrl)
        self.ic.add_control(self.test_menu)

        while not self.shutdown:
            time.sleep(5)

        self.ic.running = False


def main():
    tc = TestControls()


if __name__ == '__main__':
    main()
