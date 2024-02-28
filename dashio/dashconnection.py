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
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
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
        self.cntrl_type = "DASHIO"
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
        add a Deive to the connection
    set_connection(username, password):
        change the connection username and password
    close() :
        close the connection
    """
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connection_state = ConnectionState.CONNECTED
            for device_id in self._device_id_list:
                control_topic = f"{self.username}/{device_id}/control"
                self._dash_c.subscribe(control_topic, 0)
            for device_id in self._device_id_rx_list:
                data_topic = f"{self.username}/{device_id}/data"
                self._dash_c.subscribe(data_topic, 0)
            self._send_dash_announce()
            self._disconnect_timeout = 1.0
            logger.debug("connected OK")
        else:
            logger.debug("Bad connection Returned code=%s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.debug("disconnecting reason  %s", reason_code)
        self._dash_c.username_pw_set(self.username, self.password)
        self.connection_state = ConnectionState.DISCONNECTED
        self._disconnect_timeout = 1.0

    def _on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logger.debug("DASH RX:\n%s", data)
        self.tx_zmq_pub.send_multipart([msg.payload, self._b_zmq_connection_uuid])

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
            if self.connection_state == ConnectionState.CONNECTED:
                control_topic = f"{self.username}/{device.device_id}/control"
                self._dash_c.subscribe(control_topic, 0)
                self._send_dash_announce()

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

    def _send_dash_announce(self):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid
        }
        logger.debug("DASH SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])

    def connect(self):
        logger.debug("Connecting..")
        try:
            self._dash_c.connect(self.host, self.port)
            self.connection_state = ConnectionState.CONNECTING
        except (mqtt.socket.gaierror, ConnectionRefusedError) as error:
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
        context: zmq.Context = None
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
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.connection_state = ConnectionState.DISCONNECTED
        self.zmq_connection_uuid = "DASH:" + shortuuid.uuid()
        self._b_zmq_connection_uuid = self.zmq_connection_uuid.encode('utf-8')
        self._device_id_list = []
        self._device_id_rx_list = []
        # self.LWD = "OFFLINE"
        self.running = True
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self._dash_c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        # Assign event callbacks

        self._dash_c.on_message = self._on_message
        self._dash_c.on_connect = self._on_connect
        self._dash_c.on_disconnect = self._on_disconnect
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
        # self.dash_c.on_log = self.__on_log
        # self._dash_c.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        if username and password:
            self.connect()
        # Start subscribe, with QoS level 0
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self._disconnect_timeout = 1.0
        self.start()

    def close(self):
        """Close the connection."""
        self.running = False

    def _dash_command(self, msg_dict: dict):
        logger.debug("TCP CMD: %s", msg_dict)
        if msg_dict['msgType'] == 'connect':
            self._add_device_rx(msg_dict)
        if msg_dict['msgType'] == 'disconnect':
            self._del_device_rx(msg_dict)

    def run(self):
        self._dash_c.loop_start()

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        #  Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DASH")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)
        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)
        data_topic = ""
        control_type = ""
        while self.running:
            try:
                socks = dict(poller.poll(1))
            except zmq.error.ContextTerminated:
                break

            if self.rx_zmq_sub in socks:
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
                if self.connection_state == ConnectionState.CONNECTED and data_topic:
                    logger.debug("DASH TX:\n%s", data.decode().rstrip())
                    self._dash_c.publish(data_topic, data.decode())
            if self.connection_state == ConnectionState.DISCONNECTED:
                self._disconnect_timeout = min(self._disconnect_timeout, 900)
                time.sleep(self._disconnect_timeout)
                self.connect()
                self._disconnect_timeout = self._disconnect_timeout * 2

        self._dash_c.loop_stop()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
