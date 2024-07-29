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
import threading
import json
import shortuuid  # type: ignore
import zmq  # type: ignore
from .sim767x import Sim767x, ErrorState
from .constants import CONNECTION_PUB_URL
from .device import Device
from .iotcontrol.enums import ConnectionState


logger = logging.getLogger(__name__)


class Lte767xConnection(threading.Thread):
    """Under Active Development - DOES NOT WORK!"""

    def _on_mqtt_connect(self, connected: bool, error_state: ErrorState):
        if connected:
            logger.debug("connected OK")
            self.connection_state = ConnectionState.CONNECTED
            for device_id in self._device_id_list:
                control_topic = f"{self.username}/{device_id}/control"
                self.lte_con.subscribe(control_topic)
        else:
            logger.debug("disconnecting reason  %s", error_state)
            self._connection_state = ConnectionState.DISCONNECTED

    def _on_mqtt_subscribe(self, topic: str, error: int):
        logger.debug("Subscribed: %s %s", topic, str(error))
        if error == 0:
            device_id = topic.split('/')[1]
            self._send_dash_announce(device_id)

    def _on_mqtt_receive_message(self, message: str):
        try:
            logger.debug("LTE Rx ←\n%s", message.rstrip())
            self.tx_zmq_pub.send_multipart([message.encode(), self.b_zmq_connection_uuid])
        except UnicodeDecodeError:
            logger.debug("LTE SERIAL DECODE ERROR Rx:\n%s", message)

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
            if self.connection_state == ConnectionState.CONNECTED:
                control_topic = f"{self.username}/{device.device_id}/control"
                self.lte_con.subscribe(control_topic)

    def remove_device(self, device: Device):
        """Remove a device from the connection

        Parameters
        ----------
        device : dashio.Device
            Remove a device from the connection.
        """
        if device.device_id in self._device_id_list:
            device.de_register_connection(self)
            self._device_id_list.remove(device.device_id)
            # TODO: Unsubscribe here
            # self._lte.unsubscribe(control_topic)

    def _send_dash_announce(self, device_id: str):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid,
            'deviceID': device_id
        }
        logger.debug("DASH SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])

    def __init__(
        self,
        apn: str = "",
        username: str = "",
        password: str = "",
        host: str = 'dash.dashio.io',
        port: int = 8883,
        serial_port: str = '/dev/ttyUSB0',
        baud_rate: int = 115200,
        context=None
    ):
        """LTE 767x Connection

        Parameters
        ---------
            serial_com : str, optional
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

        self.apn = apn
        self.username = username
        self.password = password
        self.host = host
        self.port = port

        self.running = True
        self._device_id_list = []
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.lte_con = Sim767x(self.serial_port, "", self.apn, self.baud_rate)
        self.lte_con.mqtt_setup(self.host, self.port, self.username, self.password)
        self.lte_con.set_callbacks(self._on_mqtt_connect, self._on_mqtt_subscribe, self._on_mqtt_receive_message)
        self.connection_state = ConnectionState.CONNECTING
        self.start()

    def close(self):
        """Close the connection."""
        self.lte_con.close()
        self.running = False

    def run(self):
        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "LTE")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)

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
                    logger.debug("LTE con ZMQ rx: %s, %s", msg_to, data)
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
                elif msg_to == b"ANNOUNCE":
                    data_topic = f"{self.username}/{device_id}/announce"
                else:
                    data_topic = f"{self.username}/{device_id}/data"

                logger.debug("LTE Tx →\n%s\n%s", data_topic, data.decode().rstrip())
                self.lte_con.publish_message(data_topic, data.decode())

    # ???    self.serial_com.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
