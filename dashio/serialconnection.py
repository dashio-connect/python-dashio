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
import json
import logging
import socket
import threading
import time

import shortuuid
import zmq
import serial

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL
from .device import Device

class SerialControl():
    """A CFG control class to store SerialCFG connection information
    """

    def get_state(self) -> str:
        """Returns controls state. Not used for this control

        Returns
        -------
        str
            Not used in this control
        """
        return ""

    def get_cfg(self, data) -> str:
        """Returns the CFG string for this Serial control

        Returns
        -------
        str
            The CFG string for this control
        """
        try:
            dashboard_id = data[2]
        except IndexError:
            return ""
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def get_cfg64(self, data) -> dict:
        """Returns the CFG dict for this SerialCFG control

        Returns
        -------
        dict
            The CFG string for this control
        """
        return self._cfg

    def __init__(self, control_id, serial_port, baud_rate):
        self._cfg = {}
        self.cntrl_type = "Serial"
        self._cfg["controlID"] = control_id
        self.control_id = control_id
        self.serial_port = serial_port
        self.baud_rate = baud_rate

    @property
    def serial_port(self) -> str:
        """serial_port of serial connection

        Returns
        -------
        str
            The serial port
        """
        return self._cfg["serialPort"]

    @serial_port.setter
    def serial_port(self, val: str):
        self._cfg["serialPort"] = val

    @property
    def baud_rate(self) -> int:
        """The baud rate of the current connection

        Returns
        -------
        int
            The baud rate used by the serial connection
        """
        return self._cfg["baudRate"]

    @baud_rate.setter
    def baud_rate(self, val: int):
        self._cfg["baudRate"] = val


class SerialConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        device._add_connection(self)
        self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_pub_id))
        #self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)


    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=38400, context: zmq.Context=None):
        """TCP Connection

        Parameters
        ---------
            serial_port : str, optional
                Serial port to use. Defaults to "/dev/ttyUSB0".
            baud_rate : int, optional
                Baud rate to use. Defaults to 38400.
            context : optional
                ZMQ context. Defaults to None.
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode()

        self.running = True

        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"
        self.serial_com = serial.Serial(serial_port, baud_rate, timeout=1.0)
        self.serial_com.flush()
        self.connection_control = SerialControl(self.connection_id, serial_port, baud_rate)
        self.start()
        time.sleep(1)

    def close(self):
        """Close the connection."""
        self.running = False

    def run(self):
        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_id)
        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                try:
                    [_, _, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    # If there aren't three parts continue.
                    continue
                if not data:
                    continue
                logging.debug("SERIAL Tx:\n%s", data.decode().rstrip())
                self.serial_com.write(data)
            if self.serial_com.in_waiting > 0:
                message = self.serial_com.readline()
                if message:
                    try:
                        logging.debug("SERIAL Rx:\n%s", message.decode())
                        tx_zmq_pub.send_multipart([self.b_connection_id, b'', message])
                    except UnicodeDecodeError:
                        logging.debug("SERIAL DECODE ERROR Rx:\n%s", message.hex())

        self.serial_com.close()
        tx_zmq_pub.close()
        self.rx_zmq_sub.close()
