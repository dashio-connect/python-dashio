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
        parser.add_argument("-d",
                            "--device_id",
                            dest="device_id",
                            default='00001',
                            help="IotDashboard Device ID.")
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

    def __init__(self):
        self.bttn1_value = False

        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info('Connecting to server: %s', args.server)
        logging.info('       Connection ID: %s', args.connection)
        logging.info('       Control topic: %s/%s/%s/control', args.username, args.connection, args.device_id)
        logging.info('          Data topic: %s/%s/%s/data', args.username, args.connection, args.device_id)


        self.ic = dashio.iotConnectionThread(args.connection, args.device_id, args.server, args.port, args.username, args.password, use_ssl=True)
        self.ic.start()

        self.connection = args.connection

        while not self.shutdown:
            time.sleep(5)

        self.ic.running = False


def main():
    tc = TestControls()


if __name__ == '__main__':
    main()
