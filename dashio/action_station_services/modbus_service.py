"""Modbus"""
import glob
import logging
import sys
import threading
import shortuuid
import serial
import zmq

from ..constants import TASK_PULL_PORT_OFFSET, TASK_CONN_PORT_OFFSET, TCP_URL
from .action_station_service_config import (
    ActionServiceCFG,
    IntParameterSpec,
    ListParameterSpec,
    SelectorParameterSpec
)


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
    default = ""
    if len(s_ports) > 0:
        default = s_ports[0]
    provisioning_list = [
        SelectorParameterSpec(name="Serial Port", selection=s_ports, value=default, uuid=shortuuid.uuid()),
        SelectorParameterSpec(name="Baud", selection=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"], value="9600", uuid=shortuuid.uuid()),
        SelectorParameterSpec(name="Modbus Type", selection=["RTU", "ASCII"], value="RTU", uuid=shortuuid.uuid()),
        ListParameterSpec(
            name="Read Registers",
            text="Create a list of registers to read data from.",
            uuid=shortuuid.uuid(),
            param_list=[
                IntParameterSpec(
                    name="Read Register Base Address",
                    min=0,
                    max=65535,
                    units="",
                    value=0,
                    uuid=shortuuid.uuid()
                ),
                SelectorParameterSpec(
                    name="Register Type",
                    selection=[
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
                    value="uint_16",
                    uuid=shortuuid.uuid()
                ),
                IntParameterSpec(
                    name="Number of register to read from base address (Optional).",
                    min=0,
                    max=65535,
                    units="",
                    value=2,
                    uuid=shortuuid.uuid()
                )
            ]
        ),
        ListParameterSpec(
            name="Read a Bit",
            text="Create a list of registers to read data from.",
            uuid=shortuuid.uuid(),
            param_list=[
                IntParameterSpec(
                    name="Read Register Base Address",
                    min=0,
                    max=65535,
                    units="",
                    value=0,
                    uuid=shortuuid.uuid()
                ),
                IntParameterSpec(
                    name="Bit Mask",
                    min=0,
                    max=65535,
                    units="",
                    value=0,
                    uuid=shortuuid.uuid()
                )
            ]
        )

    ]
    parameter_list_in = []
    # parameter_list_out = []
    timer_cfg = ActionServiceCFG(
        objectName="MDBS",
        name="Modbus Test",
        uuid=shortuuid.uuid(),
        text="Modbus - Test provisioning of list",
        controlID="TST",
        num_tests=num_tests,
        numAvail=1,
        isTrigger=True,
        isIO=True,
        provisioning=provisioning_list,
        parameters=parameter_list_in
        #  parameter_list_out
    )
    return timer_cfg


class ModbusService(threading.Thread):
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
        self.push_url = TCP_URL.format(port=local_port + TASK_PULL_PORT_OFFSET)

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
