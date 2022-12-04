"""Memory Class"""
import threading
import time

import zmq
import logging


from .action_control_config import SelectorParameterSpec, IntParameterSpec, StringParameterSpec, FloatParameterSpec, BoolParameterSpec, SliderParameterSpec, ActionControlCFG, ListParameterSpec
from ..constants import TASK_PULL

def make_test_config(num_tests):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec( "A Selector",["Selection 1", "Selection2", "Selection3"], "Selection 1"),
        IntParameterSpec("An Int", 0, 100, "jiggers", 42),
        StringParameterSpec("A String", "Little Bo Peep...."),
        FloatParameterSpec("A Float", 2.71828, 299792458.0, "jiffies", 1.4142),
        BoolParameterSpec("A bool", True),
        SliderParameterSpec("A Slider", 1.0, 10.0, 1.0, 5.0),
        ListParameterSpec(
            "List of Things",
            "Create a list",
            [
                IntParameterSpec(
                    "Add a uint_16",
                    0,
                    65535,
                    "",
                    0
                ),
                SelectorParameterSpec(
                    "Choose a thing", [
                        "Thing One",
                        "Thing Two",
                        "The Lorax",
                        "The Grinch",
                        "Horton",
                        "Sam-I-Am",
                        "Thidwick",
                        "Yertle the Turtle",
                        "Lord Droon"
                    ],
                     "Horton",
                )
            ]
        )

    ]
    parameter_list = []

    timer_cfg = ActionControlCFG(
        "TST",
        "Test",
        "Test with all provisioning types",
        "TST",
        num_tests,
        True,
        True,
        provisioning_list,
        parameter_list
        #parameter_list_out
    )
    return timer_cfg.__json__()

class ASControl(threading.Thread):
    """Action Station Template Class"""

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send_multipart([b"ALL", b"0", out_message.encode('utf-8')])

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, action_station_id: str, control_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = context
        self.running = True

        self.control_id = control_config_dict['controlID']
        self.name = control_config_dict['name']
        self.control_type = control_config_dict['objectType']
        provision_list = control_config_dict['provisioning']

        self.push_url = TASK_PULL.format(id=action_station_id)
        self.pull_url = TASK_PULL.format(id=self.control_id)

        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)

        self.control_msg = f"\t{device_id}\t{self.control_type}\t{self.control_id}"
        logging.debug("Init Class: %s, %s", self.control_type, self.name)

        self.start()


    def run(self):
        receiver = self.context.socket(zmq.PULL)
        receiver.bind( self.pull_url)
        poller = zmq.Poller()
        poller.register(receiver, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(15))
            except zmq.error.ContextTerminated:
                break
            if receiver in socks:
                message = receiver.recv()
                if message:
                    logging.debug("%s\t%s RX:\n%s", self.control_type, self.control_id, message.decode())


        self.task_sender.close()
        receiver.close()
