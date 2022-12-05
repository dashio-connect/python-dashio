"""Modbus"""
import glob
import logging
import sys
import threading

import serial
import zmq

from ..constants import TASK_PULL
from .action_control_config import (ActionControlCFG, IntParameterSpec,
                                    ListParameterSpec, SelectorParameterSpec)




def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def make_modbus_config(num_tests):
    """Make a timer config"""
    s_ports = serial_ports()
    provisioning_list = [
        SelectorParameterSpec("Serial Port", s_ports, s_ports[0]),
        SelectorParameterSpec("Baud", ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"], "9600"),
        SelectorParameterSpec("Modbus Type", ["RTU", "ASCII"], "RTU"),
        ListParameterSpec(
            "Read Registers",
            "Create a list of registers to read data from.",
            [
                IntParameterSpec(
                    "Read Register Base Address",
                    0,
                    65535,
                    "",
                    0
                ),
                SelectorParameterSpec(
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
