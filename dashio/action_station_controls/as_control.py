"""Memory Class"""
import threading
import time

import zmq
import logging


from .action_control_config import *

def make_test_config(num_tests):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec("SLCTR_PROV", "A Selector",["Selection 1", "Selection2", "Selection3"], "Selection 1"),
        IntParameterSpec("INT_PROV", "An Int", 0, 100, "jiggers", 42),
        StringParameterSpec("STR_PROV", "A String", "Little Bo Peep...."),
        FloatParameterSpec("FLT_PROV", "A Float", 2.71828, 299792458.0, "jiffies", 1.4142),
        BoolParameterSpec("BOOL_PROV", "A bool", True),
        SliderParameterSpec("SLDR_PROV", "A Slider", 1.0, 10.0, 1.0, 5.0)
    ]
    parameter_list_in = [
        StringParamValue("STR_IN", "A String"),
        FloatParamValue("FLT_IN", 3.141592654),
        IntParamValue("INT_IN", 17),
        BoolParamValue("BOOL_IN", True),
        SelectionParamValue("SLCT_IN", "Selected Value"),
        SliderParamValue("SLDR_IN", 10.0)
    ]
    parameter_list_out = [
        SliderParamValue("SLDR_OUT", 0.0),
        SelectionParamValue("SLCT_OUT", "Selected Value"),
        BoolParamValue("BOOL_OUT", True),
        IntParamValue("INT_OUT", 17),
        FloatParamValue("FLT_OUT", 3.141592654),
        StringParamValue("STR_OUT", "A String"),
    ]
    timer_cfg = ActionControlCFG(
        "TST",
        "Test",
        "Test with provisioning",
        "TST$",
        num_tests,
        True,
        True,
        provisioning_list,
        parameter_list_in
        #parameter_list_out
    )
    return timer_cfg.__json__()

class ASControl(threading.Thread):
    """AS Template Class"""

    def send_message(self):
        """Send the message"""
        task_sender = self.context.socket(zmq.PUSH)
        task_sender.connect(self.push_url)
        task_sender.send(self.control_msg.encode())

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, control_type: str, control_id: str, push_url: str, pull_url: str,context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.push_url = push_url
        self.pull_url = pull_url
        self.device_id = device_id
        self.control_type = control_type
        self.control_id = control_id
        self.control_msg = f"\t{device_id}\t{control_type}\t{control_id}\n"
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
