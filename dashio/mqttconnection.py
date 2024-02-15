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
import ssl
import threading
import time

import paho.mqtt.client as mqtt
import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL

from .iotcontrol.enums import ConnectionState


logger = logging.getLogger(__name__)


class MQTTConnection(threading.Thread):
    """Setups and manages a connection thread to the MQTT Server."""

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connection_state = ConnectionState.CONNECTED
            for device_id in self._device_id_list:
                control_topic = f"{self.username}/{device_id}/control"
                self.mqttc.subscribe(control_topic, 0)
            for device_id in self._device_id_rx_list:
                data_topic = f"{self.username}/{device_id}/data"
                self.mqttc.subscribe(data_topic, 0)
            self._send_dash_announce()
            logger.debug("connected OK")
        else:
            logger.debug("Bad connection Returned code=%s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.debug("disconnecting reason  %s", reason_code)
        self._connection_state = ConnectionState.DISCONNECTED

    def _on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logger.debug("MQTT RX:\n%s", data)
        self.tx_zmq_pub.send_multipart([msg.payload, self.b_connection_id])

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        logger.debug("Subscribed: %s %s", str(mid), str(reason_codes))

    def _on_log(self, client, obj, level, string):
        logger.debug(string)

    def add_device(self, device):
        """Add a Device to the connextion

        Parameters
        ----------
            device (Device):
                The Device to add.
        """
        if device.device_id not in self._device_id_list:
            self._device_id_list.append(device.device_id)
            device.register_connection(self)
            if self._connection_state == ConnectionState.CONNECTED:
                control_topic = f"{self.username}/{device.device_id}/control"
                self.mqttc.subscribe(control_topic, 0)
                self._send_dash_announce()

    def _add_device_rx(self, msg_dict):
        """Connect to another device"""
        device_id = msg_dict["deviceID"]
        logger.debug("MQTT DEVICE CONNECT: %s", device_id)
        if device_id not in self._device_id_rx_list:
            self._device_id_rx_list.append(device_id)
            data_topic = f"{self.username}/{device_id}/data"
            self.mqttc.subscribe(data_topic, 0)

    def _del_device_rx(self, msg_dict):
        device_id = msg_dict["deviceID"]
        if device_id in self._device_id_rx_list:
            data_topic = f"{self.username}/{device_id}/data"
            self.mqttc.unsubscribe(data_topic)
            logger.debug("MQTT DEVICE_DISCONNECT: %s", device_id)
            del self._device_id_rx_list[device_id]

    def _send_dash_announce(self):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid
        }
        logger.debug("MQTT SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])

    def close(self):
        """Close the connection."""
        self.running = False

    def __init__(self, host, port, username="", password="", use_ssl=False, context: zmq.Context = None):
        """
        Setups and manages a connection thread to the MQTT Server.

        Parameters
        ---------
            host : str
                The server name of the mqtt host.
            port :int
                Port number to connect to.
            username : str
                username for the mqtt connection.
            password : str
                password for the mqtt connection.

        Keyword Parameters
        -----------------
            use_ssl : bool
                Whether to use ssl for the connection or not. (default: {False})
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.zmq_connection_uuid = "MQTT:" + shortuuid.uuid()
        self.b_connection_id = self.zmq_connection_uuid.encode('utf-8')
        self._connection_state = ConnectionState.DISCONNECTED
        self.connection_topic_list = []
        self._device_id_list = []
        self._device_id_rx_list = []
        self.host = host
        self.port = port
        # self.last_will = "OFFLINE"
        self.running = True
        self.username = username
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        # Assign event callbacks
        self.mqttc.on_message = self._on_message
        self.mqttc.on_connect = self._on_connect
        self.mqttc.on_disconnect = self._on_disconnect
        self.mqttc.on_subscribe = self._on_subscribe

        if use_ssl:
            self.mqttc.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )
            self.mqttc.tls_insecure_set(False)

        self.mqttc.on_log = self._on_log
        # self.mqttc.will_set(self.data_topic, self.last_will, qos=1, retain=False)
        # Connect
        if username and password:
            self.mqttc.username_pw_set(username, password)
        try:
            self.mqttc.connect(self.host, self.port)
            self._connection_state = ConnectionState.CONNECTING
        except mqtt.socket.gaierror as error:
            logger.debug("No connection to internet: %s", str(error))
        # Start subscribe, with QoS level 0
        self._disconnect_timeout = 1.0
        self.start()

    def _mqtt_command(self, msg_dict: dict):
        logger.debug("MQTT CMD: %s", msg_dict)
        if msg_dict['msgType'] == 'connect':
            self._add_device_rx(msg_dict)
        if msg_dict['msgType'] == 'disconnect':
            self._del_device_rx(msg_dict)

    def run(self):
        self.mqttc.loop_start()

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.tx_zmq_pub = self.context.socket(zmq.PUB)

        #  Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"MQTT")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)

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
                    logger.debug("MQTT value error")
                    continue
                if not data:
                    logger.debug("MQTT no data error")
                    continue
                # logger.debug("DASH: %s ,%s", msg_to, data)
                if msg_to == b'COMMAND':
                    logger.debug("MQTT RX COMMAND")
                    self._mqtt_command(json.loads(data))
                    continue
                msg_l = data.split(b'\t')
                try:
                    device_id = msg_l[1].decode().strip()
                except IndexError:
                    continue
                data_topic = f"{self.username}/{device_id}/data"
                if self._connection_state == ConnectionState.CONNECTED:
                    logger.debug("MQTT TX:\n%s", data.decode().rstrip())
                    self.mqttc.publish(data_topic, data.decode())
            if self._connection_state == ConnectionState.DISCONNECTED:
                self._disconnect_timeout = min(self._disconnect_timeout, 900)
                time.sleep(self._disconnect_timeout)
                try:
                    self.mqttc.connect(self.host, self.port)
                    self._connection_state = ConnectionState.CONNECTING
                except mqtt.socket.gaierror as error:
                    logger.debug("No connection to internet: %s", str(error))
                self._disconnect_timeout = self._disconnect_timeout * 2

        self.mqttc.loop_stop()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
