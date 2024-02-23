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
import time

import shortuuid
import zmq
import serial

from .constants import CONNECTION_PUB_URL
from .device import Device


logger = logging.getLogger(__name__)


class Lte767xConnection(threading.Thread):
    """Under Active Development - DOES NOT WORK!"""

    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        if device.device_id not in self._device_id_list:
            device.register_connection(self)
            self._device_id_list.append(device.device_id)

    def _init_serial(self):
        try:
            self.serial_com = serial.Serial(self.serial_port, self.baud_rate, timeout=1.0)
            self.serial_com.flush()
        except serial.serialutil.SerialException as e:
            logger.debug("LTE Serial Err: %s", str(e))

    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=115200, context: zmq.Context = None):
        """Serial Connection

        Parameters
        ---------
            serial_port : str, optional
                Serial port to use. Defaults to "/dev/ttyUSB0".
            baud_rate : int, optional
                Baud rate to use. Defaults to 115200.
            context : optional
                ZMQ context. Defaults to None.
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.zmq_connection_uuid = "LTE:" + shortuuid.uuid()
        self.b_zmq_connection_uuid = self.zmq_connection_uuid.encode()

        self.running = True
        self._device_id_list = []
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self._init_serial()
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
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "LTE")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)
        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(1))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                try:
                    [_, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    #  If there aren't two parts continue.
                    continue
                if not data:
                    continue
                logger.debug("LTE Tx:\n%s", data.decode().rstrip())
                # be nice and split the strings up
                lines = data.split(b'\n')
                for line in lines:
                    if line:
                        try:
                            self.serial_com.write(line + b'\n')
                        except serial.serialutil.SerialException as e:
                            logger.debug("LTE Serial Error: %s", str(e))
                            time.sleep(1.0)
                            self._init_serial()
            try:
                if self.serial_com.in_waiting > 0:
                    message = self.serial_com.readline()
                    if message:
                        try:
                            logger.debug("LTE Rx:\n%s", message.rstrip().decode())
                            parts = message.strip().decode().split('\t')
                            if len(parts) == 2 and parts[1] == 'CTRL':
                                if self._crtl_device_id_callback:
                                    self._crtl_device_id_callback(parts)
                            elif len(parts) > 2 and parts[1] == 'CTRL':
                                self.crtl_map[parts[2]](parts)
                            tx_zmq_pub.send_multipart([message, self.b_zmq_connection_uuid])
                        except UnicodeDecodeError:
                            logger.debug("LTE SERIAL DECODE ERROR Rx:\n%s", message.hex())
            except OSError as e:
                logger.debug("LTE Serial Error: %s", str(e))
                time.sleep(1.0)
                self._init_serial()

        self.serial_com.close()
        tx_zmq_pub.close()
        self.rx_zmq_sub.close()