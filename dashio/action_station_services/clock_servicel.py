"""clock.py

Copyright (c) 2022, DashIO-Connect

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
import datetime
import logging
import threading
import time

import zmq
from astral import LocationInfo
from astral.sun import sun
from dateutil import tz

from ..constants import TASK_PULL, CONNECTION_PUB_URL
from .action_station_service_config import ActionServiceCFG, FloatParameterSpec


def make_clock_config(num_tests):
    """Make a timer config"""
    provisioning_list = [
        FloatParameterSpec("Latitude", -90.0, 90.0, "degs", -43.5256),
        FloatParameterSpec("Longitude", -180.0, 180.0, "degs", 172.6398),
    ]
    parameter_list = []

    clock_cfg = ActionServiceCFG(
        "CLK",
        "Local Clock",
        "Send local time and SunUp or SunDown every minute.",
        "CLK1",
        num_tests,
        True,
        True,
        provisioning_list,
        parameter_list
        #parameter_list_out
    )
    return clock_cfg.__json__()


class ClockThread(threading.Thread):
    """Watch keeping thread returns every minute"""
    def __init__(self, callback) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.running = True
        self.callback = callback
        self.logger_interval = 60
        self.start()

    def close(self):
        """Stop the thread"""
        self.running = False

    def run(self):
        while self.running:
            tstamp = datetime.datetime.now()
            tstamp = tstamp.replace(tzinfo=tz.tzlocal())
            self.callback(tstamp)
            seconds_left = tstamp.second + tstamp.microsecond / 1000000.0
            _, sleep_time = divmod(seconds_left, self.logger_interval)
            sleep_time = self.logger_interval - sleep_time
            time.sleep(sleep_time)


class ClockService(threading.Thread):
    """Action Station Template Class"""

    def clock_message(self, tstamp: datetime.datetime):
        """Send the message"""
        if tstamp.day != self.day:
            self.sun_time = sun(self.location_info.observer, date=tstamp)
            self.day = tstamp.day
        daylight = "SunDown"
        if self.sun_time['sunrise'] < tstamp < self.sun_time['sunset']:
            daylight = "SunUp"
        msg = f"{self.control_msg}\t{daylight}\t{tstamp.year}\t{tstamp.month}\t{tstamp.day}\t{tstamp.hour}\t{tstamp.minute}\n"
        self.send_message(out_message=msg)

    def send_message(self, out_message=""):
        """Send the message"""
        logging.debug("Clock TX: %s", out_message)
        self.task_sender.send_multipart([b"ALL", out_message.encode('utf-8')])

    def close(self):
        """Close the thread"""
        self.clock.close()
        self.running = False

    def __init__(self, device_id: str, action_station_id: str, control_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = context
        self.running = True

        self.control_id = control_config_dict['controlID']
        self.name = control_config_dict['name']
        self.control_type = control_config_dict['objectType']
        provision_list = control_config_dict['provisioning']

        self.control_msg = f"\t{device_id}\t{self.control_type}\t{self.control_id}"

        latitude = provision_list[0]['value']
        longitude = provision_list[1]['value']
        self.location_info = LocationInfo('name', 'region', 'timezone/name', latitude, longitude)
        tstamp = datetime.datetime.now()
        self.day =  tstamp.day
        self.sun_time = sun(self.location_info.observer, date=datetime.datetime.now(tz=tz.tzlocal()))

        self.push_url = TASK_PULL.format(id=action_station_id)

        self.sub_url = CONNECTION_PUB_URL.format(id=action_station_id)

        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)
        self.clock = ClockThread(self.clock_message)
        logging.debug("Clock Started")
        self.start()

    def run(self):
        receiver = self.context.socket(zmq.SUB)
        receiver.connect(self.sub_url)
        receiver.setsockopt_string(zmq.SUBSCRIBE, self.control_msg)
        poller = zmq.Poller()
        poller.register(receiver, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(15))
            except zmq.error.ContextTerminated:
                break
            if receiver in socks:
                message, _ = receiver.recv()
                if message:
                    self.clock_message(datetime.datetime.now())

        self.task_sender.close()
        receiver.close()
