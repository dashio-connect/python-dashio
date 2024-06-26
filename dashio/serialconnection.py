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

from __future__ import annotations
import logging
import socket
import threading
import time

import shortuuid
import zmq
import serial
from serial.serialutil import SerialException
from .constants import CONNECTION_PUB_URL
from .device import Device


logger = logging.getLogger(__name__)


class SerialConnection(threading.Thread):
    """Under Development! - Setups and manages a connection thread to iotdashboard via a serial port."""

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

    def _dashio_crtl_reboot(self, msg):
        if self._crtl_reboot_callback:
            self._crtl_reboot_callback(msg)

    def set_crtl_reboot_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_reboot_callback = callback

    def unset_crtl_reboot_callback(self):
        """
        Unset the reboot callback function.
        """
        self._crtl_reboot_callback = None

    def _dashio_crtl_connection_callback(self, msg):
        if self._crtl_cnctn_callback:
            self._crtl_cnctn_callback(msg)

    def _dashio_crtl_ble_callback(self, msg):
        if self._crtl_ble_callback:
            self._crtl_ble_callback(msg)

    def _dashio_crtl_device_id_callback(self, msg):
        if self._crtl_device_id_callback:
            self._crtl_device_id_callback(msg)

    def _dashio_crtl_status_callback(self, msg):
        if self._crtl_status_callback:
            self._crtl_status_callback(msg)

    def set_crtl_ble_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL BLE message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_ble_callback = callback

    def unset_crtl_ble_callback(self):
        """
        Unset BLE callback function.
        """
        self._crtl_ble_callback = None

    def set_crtl_status_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL STS message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_status_callback = callback

    def unset_crtl_status_callback(self):
        """
        Unset status callback function.
        """
        self._crtl_status_callback = None

    def set_crtl_connection_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL CTCTN message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_cnctn_callback = callback

    def set_crtl_device_id_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL CTCTN message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_device_id_callback = callback

    def unset_crtl_connection_callback(self):
        """
        Unset connection callback function.
        """
        self._crtl_cnctn_callback = None

    def _init_serial(self):
        try:
            self.serial_com = serial.Serial(self.serial_port, self.baud_rate, timeout=1.0)
            self.serial_com.flush()
        except SerialException as e:
            logger.debug("Serial Err: %s", str(e))

    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=115200, context: zmq.Context | None = None):
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

        self.crtl_map = {
            'REBOOT': self._dashio_crtl_reboot,
            'CNCTN': self._dashio_crtl_connection_callback,
            'BLE': self._dashio_crtl_ble_callback,
            'STS': self._dashio_crtl_status_callback
        }

        self.context = context or zmq.Context.instance()
        self.zmq_connection_uuid = "SERIAL:" + shortuuid.uuid()
        self.b_zmq_connection_uuid = self.zmq_connection_uuid.encode()
        self._crtl_reboot_callback = None
        self._crtl_cnctn_callback = None
        self._crtl_device_id_callback = None
        self._crtl_ble_callback = None
        self._crtl_status_callback = None

        self.running = True
        self._device_id_list = []
        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"
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
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "SERIAL")
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
                    [msg_to, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    #  If there aren't two parts continue.
                    continue
                if not data:
                    continue
                dest = msg_to.split(b':')[-1]
                if dest == b"ALL":
                    dest = b"\tALL"
                logger.debug("SERIAL Tx:\n%s", data.decode().rstrip())
                # be nice and split the strings up
                lines = data.split(b'\n')
                for line in lines:
                    if line:
                        try:
                            self.serial_com.write(dest + line + b'\n')
                        except SerialException as e:
                            logger.debug("Serial Error: %s", str(e))
                            time.sleep(1.0)
                            self._init_serial()
            try:
                if self.serial_com.in_waiting > 0:
                    message = self.serial_com.readline()
                    if message:
                        try:
                            logger.debug("SERIAL Rx:\n%s", message.rstrip().decode())
                            parts = message.strip().decode().split('\t')
                            if len(parts) == 2 and parts[1] == 'CTRL':
                                if self._crtl_device_id_callback is not None:
                                    self._crtl_device_id_callback(parts)
                            elif len(parts) > 2 and parts[1] == 'CTRL':
                                try:
                                    self.crtl_map[parts[2]](parts)
                                except KeyError:
                                    logger.debug("Unkown CTRL: %s", message.rstrip().decode())
                                    continue
                            msg_from = self.b_zmq_connection_uuid + b":" + parts[0].encode()
                            tx_message = '\t' + '\t'.join(parts[1:]) + '\n'
                            tx_zmq_pub.send_multipart([tx_message.encode(), msg_from])
                        except UnicodeDecodeError:
                            logger.debug("SERIAL DECODE ERROR Rx:\n%s", message.hex())
            except OSError as e:
                logger.debug("Serial Error: %s", str(e))
                time.sleep(1.0)
                self._init_serial()

        self.serial_com.close()
        tx_zmq_pub.close()
        self.rx_zmq_sub.close()
