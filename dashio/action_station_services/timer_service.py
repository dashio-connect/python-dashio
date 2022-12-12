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
import logging
import threading

import zmq

from ..constants import CONNECTION_PUB_URL, TASK_PULL
from .action_station_service_config import (ActionServiceCFG, IntParameterSpec,
                                            SelectorParameterSpec)


# This defines the provisioning for the TIMER
def make_timer_config(num_timers):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec("Timer Type",["Repeat", "OneShot"], "Repeat"),
        IntParameterSpec("Timeout", 100, 600000, "ms", 1000)
    ]
    parameter_in_list = []
    #parameter_out_list = []

    timer_cfg = ActionServiceCFG(
        "TMR",
        "Timer",
        "A timer control.",
        "TMR",
        num_timers,
        True,
        True,
        provisioning_list,
        parameter_in_list
        #parameter_out_list
    )
    return timer_cfg.__json__()


class RepeatTimer(threading.Timer):
    """The timer"""
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


# The app returns the edited provisioning with enough info to instantiate this class:
# With controlID, timer_type(from provisioning), timeout(from provisioning)
# THe device knows the rest (device_id, push_url, context)

# parameter_in_list would be used by the TIMER to parse the incoming message.
# paramiter_out_list is how to format the output message 
class TimerService(threading.Thread):
    """Timer Class"""

    def timer_message(self):
        """Send the message"""
        self.send_message(out_message=self.control_msg + "\n")

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send_multipart([b"ALL", out_message.encode('utf-8')])

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, action_station_id: str, control_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = context
        self.running = True
        self.timer_type = None

        self.control_id = control_config_dict['controlID']
        self.name = control_config_dict['name']
        self.control_type = control_config_dict['objectType']
        provision_list = control_config_dict['provisioning']
        
        self.sub_url = CONNECTION_PUB_URL.format(id=action_station_id)

        self.push_url = TASK_PULL.format(id=action_station_id)
        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)

        self.timer_time = int(provision_list[1]['value'])/1000.0
        self.timer_type = provision_list[0]['value']

        self.control_msg = f"\t{device_id}\t{self.control_type}\t{self.control_id}"
        
        logging.debug("Init Class: %s, %s", self.control_type, self.name)

        if self.timer_type == 'Repeat':
            self.timer_type = RepeatTimer(self.timer_time, self.timer_message)
            self.timer_type.start()
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
                    logging.debug("%s\t%s RX:\n%s", self.control_type, self.control_id, message.decode())
                    if self.timer_type == 'OneShot':
                        self.timer_type = threading.Timer(self.timer_time, self.timer_message)
                        self.timer_type.start()
        self.timer_type.cancel()
        self.task_sender.close()
        receiver.close()
