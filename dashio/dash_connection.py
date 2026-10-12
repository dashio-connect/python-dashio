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

import json
import logging
import ssl
import threading
import time
from socket import gaierror

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL
from .iotcontrol.enums import ConnectionState

logger = logging.getLogger(__name__)

MAX_BATCH_LENGTH = 4096  # A batch is published before it would grow past this, as in the DashIO firmware.


class DashControl():
    """Class to stare dash connection info
    """

    def get_state(self) -> str:
        """Not used by this class as its a CFG only control
        """
        return ""

    def get_cfg(self, data: list) -> str:
        """Returns the CFG info for the Dash connection. Called by iotdashboard app

        Parameters
        ----------
        data:
            List sent by dashboard app.

        Returns
        -------
        str
            The CFG string
        """
        try:
            # num_columns = data[3]
            dashboard_id = data[2]
        except IndexError:
            return ""
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.ctrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def get_cfg64(self, data: list) -> dict:
        """Returns the CFG dict for this TCP control

        Returns
        -------
        dict
            The CFG string for this control
        """
        return self._cfg

    def __init__(self, control_id, username="", servername=""):
        self.ctrl_type = "DASHIO"
        self._cfg = {}
        self._cfg["controlID"] = control_id
        self.control_id = control_id
        self.username = username
        self.servername = servername

    @property
    def username(self) -> str:
        """username

        Returns
        -------
        str
            The username for the current connection
        """
        return self._cfg["userName"]

    @username.setter
    def username(self, val: str):
        self._cfg["userName"] = val

    @property
    def servername(self) -> str:
        """servername

        Returns
        -------
        str
            The servername for the current connection
        """
        return self._cfg["hostURL"]

    @servername.setter
    def servername(self, val: str):
        self._cfg["hostURL"] = val


class DashConnection(threading.Thread):
    """Setups and manages a connection thread to the Dash Server.

    Attributes
    ----------
    dash_control : Dash
        A Dash control

    Methods
    -------
    add_device(Device) :
        add a Device to the connection
    set_connection(username, password):
        change the connection username and password
    close() :
        close the connection
    """

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if not reason_code.is_failure:
            self.connection_state = ConnectionState.CONNECTED
            for device_id in self._device_id_list:
                control_topic = f"{self.username}/{device_id}/control"
                result, mid = self._dash_c.subscribe(control_topic, 0)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    self._subscribing_topics[mid] = control_topic
            for device_id in self._device_id_rx_list:
                data_topic = f"{self.username}/{device_id}/data"
                result, mid = self._dash_c.subscribe(data_topic, 0)
            for device_id in self._device_id_list:
                self._send_online_state(device_id, "ONLINE")
            self._disconnect_timeout = 1.0
            logger.debug("connected OK")
        else:
            logger.debug("Bad connection Returned code=%s", reason_code)

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logger.debug("disconnecting reason  %s", reason_code)
        self._dash_c.username_pw_set(self.username, self.password)
        self.connection_state = ConnectionState.DISCONNECTED
        self._disconnect_timeout = 1.0

    def _on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logger.debug("DASH Rx ←\n%s", data)
        self.tx_zmq_pub.send_multipart([msg.payload, self._b_zmq_connection_uuid])

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        logger.debug("Subscribed: %s %s", str(mid), str(reason_codes))
        if not reason_codes[0].is_failure:
            topic = self._subscribing_topics.get(mid, None)
            logger.debug("On sub: %s", topic)
            if topic is not None:
                device_id = topic.split('/')[1]
                self._send_dash_announce(device_id)

    def _on_log(self, client, obj, level, string):
        logger.debug(string)

    def add_device(self, device):
        """Add a Device to the connection

        Parameters
        ----------
            device (Device):
                The Device to add.
        """
        if device.device_id not in self._device_id_list:
            self._device_id_list.append(device.device_id)
            device.register_connection(self)
            if self.connection_state == ConnectionState.CONNECTED:
                control_topic = f"{self.username}/{device.device_id}/control"
                result, mid = self._dash_c.subscribe(control_topic, 0)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    self._subscribing_topics[mid] = control_topic
                self._send_online_state(device.device_id, "ONLINE")

    def _add_device_rx(self, msg_dict):
        """Connect to another device"""
        device_id = msg_dict["deviceID"]
        logger.debug("DASH DEVICE CONNECT: %s", device_id)
        if device_id not in self._device_id_rx_list:
            self._device_id_rx_list.append(device_id)
            data_topic = f"{self.username}/{device_id}/data"
            self._dash_c.subscribe(data_topic, 0)

    def _del_device_rx(self, msg_dict):
        device_id = msg_dict["deviceID"]
        if device_id in self._device_id_rx_list:
            data_topic = f"{self.username}/{device_id}/data"
            self._dash_c.unsubscribe(data_topic)
            logger.debug("DASH DEVICE_DISCONNECT: %s", device_id)
            del self._device_id_rx_list[device_id]

    def _send_dash_announce(self, device_id: str):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid,
            'deviceID': device_id
        }
        logger.debug("DASH SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])

    def _queue_publish(self, topic: str, payload: str, qos: int):
        """Publish payload, batched with other messages for the same topic for batch_delay seconds."""
        if self.batch_delay <= 0:
            logger.debug("DASH Tx →\n%s", payload.rstrip())
            self._dash_c.publish(topic, payload, qos=qos)
            return
        with self._batch_lock:
            pending, pending_qos = self._batch.pop(topic, ("", 0))
            if pending and len(pending) + len(payload) > MAX_BATCH_LENGTH:
                logger.debug("DASH Tx →\n%s", pending.rstrip())
                self._dash_c.publish(topic, pending, qos=pending_qos)
                pending, pending_qos = "", 0
            if not self._batch:
                self._batch_start = time.monotonic()
            self._batch[topic] = (pending + payload, max(pending_qos, qos))

    def _flush_batch(self, force: bool = False):
        """Publish the batched messages, once they have waited batch_delay seconds, or straight away if force."""
        with self._batch_lock:
            if not self._batch or (not force and time.monotonic() - self._batch_start < self.batch_delay):
                return
            batch, self._batch = self._batch, {}
        for topic, (payload, qos) in batch.items():
            logger.debug("DASH Tx →\n%s", payload.rstrip())
            self._dash_c.publish(topic, payload, qos=qos)

    def _send_online_state(self, device_id: str, state: str):
        """Publish ONLINE or OFFLINE for device_id to its data topic."""
        return self._dash_c.publish(f"{self.username}/{device_id}/data", f"\t{device_id}\t{state}\n", qos=1)

    def _set_will(self):
        """Set the MQTT Last Will and Testament: the Dash server publishes OFFLINE if the connection is lost.

        An MQTT connection has a single will on a single topic, so it is for the first device on the connection.
        The will is fixed when connecting, so devices added later aren't included. close() sends OFFLINE for
        every device.
        """
        if not self._device_id_list:
            self._dash_c.will_clear()
            return
        device_id = self._device_id_list[0]
        properties = None
        if self.offline_delay > 0:
            properties = Properties(PacketTypes.WILLMESSAGE)
            properties.WillDelayInterval = self.offline_delay
        self._dash_c.will_set(f"{self.username}/{device_id}/data", f"\t{device_id}\tOFFLINE\n", qos=1, retain=False, properties=properties)

    def connect(self):
        """Connect to the server."""
        logger.debug("Connecting..")
        self._set_will()
        properties = None
        if self.offline_delay > 0:
            # The server only waits the will delay if it keeps the session that long.
            properties = Properties(PacketTypes.CONNECT)
            properties.SessionExpiryInterval = self.offline_delay
        try:
            self._dash_c.connect(self.host, self.port, properties=properties)
            self.connection_state = ConnectionState.CONNECTING
            # Start the network loop only once a host is set, otherwise paho's thread dies with "Invalid host".
            self._dash_c.loop_start()
        except (gaierror, ConnectionRefusedError) as error:
            logger.debug("No connection to server: %s", str(error))

    def set_connection(self, username: str, password: str):
        """Changes the connection to the DashIO server

        Parameters
        ----------
        username : str
            username for the server
        password : str
            password for the server
        """
        self.username = username
        self.password = password
        self._dash_c.disconnect()

    def __init__(
        self,
        username="",
        password="",
        host='dash.dashio.io',
        port=8883,
        use_ssl=True,
        context: zmq.Context | None = None,
        offline_delay: int = 10,
        batch_delay: float = 0.05
    ):
        """
        Setups and manages a connection thread to the Dash Server.

        Parameters
        ---------
            host : str
                The server name of the dash host.
            port : int
                Port number to connect to. Defaults to 8883.
            username : str
                username for the dash connection.
            password : str
                password for the dash connection.
            use_ssl : Boolean
                Defaults to True.
            context : zmq.Context, optional
                ZMQ context. Defaults to the shared zmq.Context.instance().
            offline_delay : int, optional
                If the connection is lost, the Dash server publishes OFFLINE for the first device after this many
                seconds, unless the connection is restored first. 0 publishes it straight away. Defaults to 10.
            batch_delay : float, optional
                Messages for the same topic sent within this many seconds are published together, so a device
                updating several controls makes one publish. Alarms are published straight away. 0 publishes each
                message straight away. Defaults to 0.05.
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.connection_state = ConnectionState.DISCONNECTED
        self.zmq_connection_uuid = "DASH:" + shortuuid.uuid()
        self._b_zmq_connection_uuid = self.zmq_connection_uuid.encode('utf-8')
        self._device_id_list = []
        self._device_id_rx_list = []
        self._subscribing_topics = {}
        self.offline_delay = offline_delay
        self.batch_delay = batch_delay
        self._batch = {}  # Topic -> (messages, qos) waiting to be published.
        self._batch_start = 0.0
        self._batch_lock = threading.Lock()
        self.running = True
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self._dash_c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)  # type: ignore
        # Assign event callbacks

        self._dash_c.on_message = self._on_message
        self._dash_c.on_connect = self._on_connect
        self._dash_c.on_disconnect = self._on_disconnect  # type: ignore
        self._dash_c.on_subscribe = self._on_subscribe
        # self.connection_control = DashControl(self.zmq_connection_uuid, username, host)
        if use_ssl:
            self._dash_c.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )
            self._dash_c.tls_insecure_set(False)

        self._dash_c.username_pw_set(self.username, self.password)
        # The connection thread connects, a moment after it starts, so the devices added straight after creating
        # the connection are included in the will.
        # Start subscribe, with QoS level 0
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self._disconnect_timeout = 1.0
        self.start()

    def close(self):
        """Send OFFLINE for every device, then close the connection."""
        if self.connection_state == ConnectionState.CONNECTED:
            self._flush_batch(force=True)
            messages = [self._send_online_state(device_id, "OFFLINE") for device_id in self._device_id_list]
            for message in messages:
                try:
                    message.wait_for_publish(timeout=2.0)
                except (RuntimeError, ValueError) as error:
                    logger.debug("OFFLINE not sent: %s", error)
            # A normal disconnect, so the server doesn't also publish the will.
            self._dash_c.disconnect()
        self.running = False

    def _dash_command(self, msg_dict: dict):
        logger.debug("TCP CMD: %s", msg_dict)
        if msg_dict['msgType'] == 'connect':
            self._add_device_rx(msg_dict)
        if msg_dict['msgType'] == 'disconnect':
            self._del_device_rx(msg_dict)

    def run(self):
        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        #  Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DASH")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)
        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)
        while self.running:
            try:
                socks = dict(poller.poll(10))
            except zmq.error.ContextTerminated:
                break

            if self.rx_zmq_sub in socks and self.connection_state == ConnectionState.CONNECTED:
                try:
                    [msg_to, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    logger.debug("DASH value error")
                    continue
                if not data:
                    logger.debug("DASH no data error")
                    continue
                # logger.debug("DASH: %s ,%s", msg_to, data)
                if msg_to == b'COMMAND':
                    logger.debug("DASH RX COMMAND")
                    self._dash_command(json.loads(data))
                    continue
                msg_l = data.split(b'\t')
                try:
                    device_id = msg_l[1].decode().strip()
                except IndexError:
                    continue
                control_type = msg_l[2] if len(msg_l) > 2 else b""
                if control_type == b'ALM':
                    # Each alarm is a push notification, so it's published straight away.
                    logger.debug("DASH Tx →\n%s", data.decode().rstrip())
                    self._dash_c.publish(f"{self.username}/{device_id}/alarm", data.decode(), qos=0)
                elif msg_to == b"ANNOUNCE":
                    self._queue_publish(f"{self.username}/{device_id}/announce", data.decode(), 1)
                else:
                    self._queue_publish(f"{self.username}/{device_id}/data", data.decode(), 0)
            self._flush_batch()
            if self.connection_state == ConnectionState.DISCONNECTED:
                self._disconnect_timeout = min(self._disconnect_timeout, 900)
                time.sleep(self._disconnect_timeout)
                self.connect()
                self._disconnect_timeout = self._disconnect_timeout * 2

        self._flush_batch(force=True)
        self._dash_c.loop_stop()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
