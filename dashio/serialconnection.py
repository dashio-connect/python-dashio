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
import socket
import threading
import time

import shortuuid
import zmq
import serial

from .constants import CONNECTION_PUB_URL
from .device import Device


class SerialConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        if device.device_id not in self.local_device_id_list:
            device.register_connection(self)
            self.local_device_id_list.append(device.device_id)


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
        self.zmq_connection_uuid = "SERIAL:" + shortuuid.uuid()
        self.b_connection_id = self.zmq_connection_uuid.encode()

        self.running = True
        self.local_device_id_list = []
        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"
        self.serial_com = serial.Serial(serial_port, baud_rate, timeout=1.0)
        self.serial_com.flush()
        self.start()
        time.sleep(1)

    def close(self):
        """Close the connection."""
        self.running = False

    def run(self):
        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "SERIAL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)
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
                    [_, data]= self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    # If there aren't two parts continue.
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
                        tx_zmq_pub.send_multipart([message, self.zmq_connection_uuid])
                    except UnicodeDecodeError:
                        logging.debug("SERIAL DECODE ERROR Rx:\n%s", message.hex())

        self.serial_com.close()
        tx_zmq_pub.close()
        self.rx_zmq_sub.close()
