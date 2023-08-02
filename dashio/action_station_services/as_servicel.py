"""Memory Class"""
import logging
import threading
import zmq
import shortuuid

from ..constants import TASK_CONN_PORT_OFFSET, TASK_PULL_PORT_OFFSET, TCP_URL
from .action_station_service_config import (ActionServiceCFG,
                                            BoolParameterSpec,
                                            FloatParameterSpec,
                                            IntParameterSpec,
                                            ListParameterSpec,
                                            SelectorParameterSpec,
                                            SliderParameterSpec,
                                            StringParameterSpec)


def make_test_config(num_tests):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec(name="A Selector", selection=["Selection1", "Selection2", "Selection3"], value="Selection1", uuid=shortuuid.uuid()),
        IntParameterSpec(name="An Int", min=0, max=100, units="jiggers", value=42, uuid=shortuuid.uuid()),
        StringParameterSpec(name="A String", value="Little Bo Peep....", uuid=shortuuid.uuid()),
        FloatParameterSpec(name="A Float", min=2.71828, max=299792458.0, units="jiffies", value=1.4142, uuid=shortuuid.uuid()),
        BoolParameterSpec(name="A bool", value=True, uuid=shortuuid.uuid()),
        SliderParameterSpec(name="A Slider", min=1.0, max=10.0, step=1.0, value=5.0, uuid=shortuuid.uuid()),
        ListParameterSpec(
            name="List of Things",
            text="Create a list",
            uuid=shortuuid.uuid(),
            param_list=[
                IntParameterSpec(
                    name="Add a uint_16",
                    min=0,
                    max=65535,
                    units="",
                    value=0,
                    uuid=shortuuid.uuid()
                ),
                SelectorParameterSpec(
                    name="Choose a thing",
                    selection=[
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
                    value="Horton",
                    uuid=shortuuid.uuid()
                )
            ]
        )

    ]
    parameter_list = []

    timer_cfg = ActionServiceCFG(
        objectName="TST",
        name="Test",
        text="Test with all provisioning types",
        uuid=shortuuid.uuid(),
        controlID="TST",
        numAvail=num_tests,
        isTrigger=True,
        isIO=True,
        provisioning=provisioning_list,
        parameters=parameter_list
        #  parameter_list_out
    )
    return timer_cfg


class ASService(threading.Thread):
    """Action Station Template Class"""

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send_multipart([b"ALL", out_message.encode('utf-8')])

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, local_port: int, control_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = context
        self.running = True

        self.control_id = control_config_dict['controlID']
        self.name = control_config_dict['name']
        self.control_type = control_config_dict['objectType']
        # provision_list = control_config_dict['provisioning']

        self.sub_url = TCP_URL.format(port=local_port + TASK_CONN_PORT_OFFSET)
        self.push_url = TCP_URL.format(port=local_port + + TASK_PULL_PORT_OFFSET)
        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)

        self.control_msg = f"\t{device_id}\t{self.control_type}\t{self.control_id}"
        logging.debug("Init Class: %s, %s", self.control_type, self.name)

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

        self.task_sender.close()
        receiver.close()
