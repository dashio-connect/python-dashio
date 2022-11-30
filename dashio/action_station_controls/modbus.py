"""Memory Class"""
import threading
import time

import zmq
import logging


from .action_control_config import *

def make_modbus_config(num_tests):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec("PORT_SLCTR", "Serial Port",["uart1", "uart2", "uart4"], "uart1"),
        SelectorParameterSpec("BAUD_SLCTR", "Baud", ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"], 9600),
        SelectorParameterSpec("RTYPE_SLCTR", "Modbus Type", ["RTU", "ASCII"], "RTU"),
        ListParameterSpec(
            "RDREG_SLCTR",
            "Registers To Read",
            "Create a list of registers to read data from.",
            [
                IntParameterSpec(
                    "READ_REG_INT",
                    "Read Register Base Address",
                    0,
                    65535,
                    "",
                    0
                ),
                SelectorParameterSpec(
                    "REGTYPR_SLCTR",
                    "Register Type", [
                        "char",
                        "int_8",
                        "uint_8",
                        "int_16",
                        "uint_16",
                        "int_32",
                        "uint_32",
                        "int_64",
                        "uint_64"
                    ],
                     "uint_16",
                ),
                IntParameterSpec(
                    "READ_LEN_INT",
                    "Number of register to read from base address (Optional).",
                    0,
                    65535,
                    "",
                    2
                )
            ]
        )
    ]
    parameter_list_in = []
    parameter_list_out = []
    timer_cfg = ActionControlCFG(
        "MDBS",
        "Modbus Test",
        "Modbus - Test provisioning of list",
        "TST$",
        num_tests,
        True,
        True,
        provisioning_list,
        parameter_list_in
        #parameter_list_out
    )
    return timer_cfg.__json__()

class ModbusControl(threading.Thread):
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
