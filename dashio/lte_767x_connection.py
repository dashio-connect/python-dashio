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
from .iotcontrol.enums import ConnectionState


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
            self.connection_state = ConnectionState.CONNECTED  # Change this to CONNECTING
        except serial.serialutil.SerialException as e:
            logger.debug("LTE Serial Err: %s", str(e))

    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=115200, context: zmq.Context = None):
        """LTE 767x Connection

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
        self.connection_state = ConnectionState.DISCONNECTED
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
            if self.rx_zmq_sub in socks and self.connection_state == ConnectionState.CONNECTED:  # If not connected the incoming messages are queued
                try:
                    [msg_to, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    #  If there aren't two parts continue.
                    continue
                if not data:
                    continue

                msg_l = data.split(b'\t')
                if len(msg_l) > 3:
                    control_type = msg_l[2]
                try:
                    device_id = msg_l[1].decode().strip()
                except IndexError:
                    continue
                if control_type == b'ALM':
                    data_topic = f"{self.username}/{device_id}/alarm"
                    control_type = ""
                elif msg_to == b"DASH":
                    data_topic = f"{self.username}/{device_id}/announce"
                else:
                    data_topic = f"{self.username}/{device_id}/data"

                logger.debug("LTE TX:\n%s\n%s", data_topic, data.decode().rstrip())

                # self._lte_publish(data_topic, data.decode()) <- craig needs to write this function

            try:
                if self.serial_com.in_waiting > 0:
                    # Craig needs to change this to get data from LTE
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
