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
import Adafruit_BBIO.ADC as ADC


class BBB_Temperature():

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

    def read_sensor(self):
        ain_value = ADC.read("P9_39")
        ain_voltage = 1.8 * ain_value
        sensor_output_voltage = ain_voltage * 2
        f = sensor_output_voltage * 100
        c = (f - 32) * 5 / 9
        c_str = "{:.2f}".format(c)
        return c_str

    def __init__(self):
        LOGGER_PERIOD = 15
        DIV = 1.0

        ADC.setup()

        # Catch CNTRL-C signel
        signal.signal(signal.SIGINT, self.signal_cntrl_c)
        self.shutdown = False
        args = self.parse_commandline_arguments()
        self.init_logging(args.logfilename, args.verbose)

        logging.info('Connecting to server: %s', args.server)
        logging.info('       Connection ID: %s', args.connection)
        logging.info('       Control topic: %s/%s/%s/control', args.username, args.connection, args.device_id)
        logging.info('          Data topic: %s/%s/%s/data', args.username, args.connection, args.device_id)


        ic = dashio.iotconnection.iotConnectionThread(args.connection,
                                                      args.device_id, 
                                                      args.server,
                                                      args.port,
                                                      args.username,
                                                      args.password,
                                                      use_ssl=True)

        gph_15_minutes = dashio.TimeGraph('Temperature15M')
        gph_15_minutes.title = 'Temp15M:{}'.format(args.connection)
        gph_15_minutes.timeScale = '15 minutes'
        gph_15_minutes.y_axis_label = 'Degrees C'
        gph_15_minutes.y_axis_min = 0.0
        gph_15_minutes.y_axis_max = 50.0
        gph_15_minutes.y_axis_num_bars = 5
        line_15_minutes = dashio.TimeGraphLine('DegC', 
                                               dashio.TimeGraphLineType.LINE,
                                               colour=dashio.Colour.BLACK,
                                               max_data_points=15 * 60 / LOGGER_PERIOD)
        gph_15_minutes.add_line('DegC', line_15_minutes)

        gph_1_day = dashio.TimeGraph('Temperature1D')
        gph_1_day.title = 'Temp1D:{}'.format(args.connection)
        gph_1_day.timeScale = '1 day'
        gph_1_day.y_axis_label = 'Degrees C'
        gph_1_day.y_axis_min = 0.0
        gph_1_day.y_axis_max = 50.0
        gph_1_day.y_axis_num_bars = 5
        line_1_day = dashio.TimeGraphLine('DegC',
                                          dashio.TimeGraphLineType.LINE,
                                          colour=dashio.Colour.BLACK,
                                          max_data_points=24 * 4)
        gph_1_day.add_line('DegC', line_1_day)

        gph_1_week = dashio.TimeGraph('Temperature1W')
        gph_1_week.title = 'Temp1W:{}'.format(args.connection)
        gph_1_week.timeScale = '1 week'
        gph_1_week.y_axis_label = 'Degrees C'
        gph_1_week.y_axis_min = 0.0
        gph_1_week.y_axis_max = 50.0
        gph_1_week.y_axis_num_bars = 5
        line_1_week = dashio.TimeGraphLine('DegC',
                                           dashio.TimeGraphLineType.LINE,
                                           colour=dashio.Colour.BLACK,
                                           max_data_points=24 * 4 * 7)
        gph_1_week.add_line('DegC', line_1_week)

        gph_1_year = dashio.TimeGraph('Temperature1Y')
        gph_1_year.title = 'Temp1Y:{}'.format(args.connection)
        gph_1_year.timeScale = '1 year'
        gph_1_year.y_axis_label = 'Degrees C'
        gph_1_year.y_axis_min = 0.0
        gph_1_year.y_axis_max = 50.0
        gph_1_year.y_axis_num_bars = 5
        line_1_year = dashio.TimeGraphLine('DegC',
                                           dashio.TimeGraphLineType.LINE,
                                           colour=dashio.Colour.BLACK,
                                           max_data_points=360)
        gph_1_year.add_line('DegC', line_1_year)

        dl_temperature_ctrl = dashio.Dial('TemperatureDial')
        dl_temperature_ctrl.title = 'Temperature'
        dl_temperature_ctrl.max = 50

        dl_daily_max_ctrl = dashio.Dial('TemperatureMaxDial')
        dl_daily_max_ctrl.title = 'Daily Max'
        dl_daily_max_ctrl.max = 50

        dl_daily_min_ctrl = dashio.Dial('TemperatureMinDial')
        dl_daily_min_ctrl.title = 'Daily Min'
        dl_daily_min_ctrl.max = 50

        ic.add_control(dl_temperature_ctrl)
        ic.add_control(dl_daily_max_ctrl)
        ic.add_control(dl_daily_min_ctrl)
        ic.add_control(gph_15_minutes)
        ic.add_control(gph_1_day)
        ic.add_control(gph_1_week)
        ic.add_control(gph_1_year)
        ic.start()
        self.connection = args.connection
        count = 0
        reset_daily = False

        temperature = self.read_sensor()
        daily_temperature_max = temperature
        daily_temperature_min = temperature

        while not self.shutdown:
            temperature = self.read_sensor()
            if temperature < daily_temperature_min:
                daily_temperature_min = temperature
                dl_daily_min_ctrl.dial_value = temperature
            if temperature > daily_temperature_max:
                daily_temperature_max = temperature
                dl_daily_max_ctrl.dial_value = temperature
            dl_temperature_ctrl.dial_value = temperature
            line_15_minutes.add_data_point(temperature)
            gph_15_minutes.send_data()
            t = datetime.datetime.now()
            if (t.minute == 0 or t.minute == 15 or t.minute == 30 or t.minute == 45) and (t.second < 5):
                total = 0
                for d in line_15_minutes.data:
                    temps = d.split(",")
                    total += float(temps[1])
                avg = total / len(line_15_minutes.data)
                avg_str = "{:.2f}".format(avg)
                line_1_day.add_data_point(avg_str)
                line_1_week.add_data_point(avg_str)
                gph_1_day.send_data()
                gph_1_week.send_data()
                if (t.hour == 12 and t.minute == 0 and t.second < 10):
                    daily_temperature_max = temperature
                    daily_temperature_min = temperature
                    line_1_year.add_data_point(avg_str)
                    gph_1_year.send_data()
            t = datetime.datetime.now()

            seconds_left = t.second + t.microsecond / 1000000.0
            div, sleep_time = divmod(seconds_left, LOGGER_PERIOD)
            sleep_time = LOGGER_PERIOD - sleep_time
            time.sleep(sleep_time)
        ic.running = False


def main():
    tc = BBB_Temperature()


if __name__ == '__main__':
    main()
