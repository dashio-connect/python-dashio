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

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL


class Dash():
    """Class to stare dash connection info
    """
    def get_state(self) -> str:
        """Not used by this class as its a CFG only control
        """
        return ""

    def get_cfg(self, data) -> str:
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
            num_columns = data[3]
            dashboard_id = data[2]
        except IndexError:
            return
        cfg_str =f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, username="", servername=""):
        self.cntrl_type = "DASHIO"
        self._cfg = {}
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
    def _on_connect(self, client, userdata, flags, msg):
        if msg == 0:
            self._connected = True
            self._disconnect = False
            for device_id in self._device_id_list:
                control_topic = f"{self.username}/{device_id}/control"
                self._dash_c.subscribe(control_topic, 0)
            self._send_dash_announce()
            logging.debug("connected OK")
        else:
            logging.debug("Bad connection Returned code=%s", msg)

    def _on_disconnect(self, client, userdata, msg):
        logging.debug("disconnecting reason  %s", msg)
        self._connected = False
        self._disconnect = True

    def _on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logging.debug("DASH RX:\n%s", data)
        self.tx_zmq_pub.send_multipart([self._b_connection_id, b'1', msg.payload])

    def _on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def _on_log(self, client, obj, level, string):
        logging.debug(string)

    def add_device(self, device):
        """Add a Device to the connextion

        Parameters
        ----------
            device (Device):
                The Device to add.
        """
        if device.device_id not in self._device_id_list:
            self._device_id_list.append(device.device_id)
            device.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self._connection_id))
            device.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self._b_connection_id)
            device.add_control(self.dash_control)

            self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_pub_id))
            self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)

            if self._connected:
                control_topic = f"{self.username}/{device.device_id}/control"
                self._dash_c.subscribe(control_topic, 0)
                self._send_dash_announce()

    def _send_dash_announce(self):
        self.tx_zmq_pub.send_multipart([b'COMMAND', b'1', b"send_announce"])

    def set_connection(self, username: str, password: str):
        """Changes the connection to the DashIO server

        Parameters
        ----------
        username : str
            username for the server
        password : str
            password for the server
        """
        self._dash_c.disconnect()
        self.username = username
        self._dash_c.username_pw_set(username, password)
        self._dash_c.connect(self.host, self.port)

    def __init__(
        self,
        username="",
        password="",
        host='dash.dashio.io',
        port=8883,
        use_ssl=True,
        context=None
    ):
        """
        Setups and manages a connection thread to the Dash Server.

        Parameters
        ---------
            host : str
                The server name of the dash host.
            port : int
                Port number to connect to.
            username : str
                username for the dash connection.
            password : str
                password for the dash connection.
            use_ssl : Boolean
                Defaults to True.
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self._connected = False
        self._disconnect = True
        self._connection_id = shortuuid.uuid()
        self._b_connection_id = self._connection_id.encode('utf-8')
        self._device_id_list = []
        # self.LWD = "OFFLINE"
        self.running = True
        self.username = username
        self.host = host
        self.port = port
        self._dash_c = mqtt.Client()
        # Assign event callbacks
        self._dash_c.on_message = self._on_message
        self._dash_c.on_connect = self._on_connect
        self._dash_c.on_disconnect = self._on_disconnect
        # self.dash_c.on_publish = self.__on_publish
        self._dash_c.on_subscribe = self._on_subscribe
        self.dash_control = Dash(self._connection_id, username, host)
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

        # self.dash_c.on_log = self.__on_log
        # self.dash_c.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        if username and password:
            self._dash_c.username_pw_set(username, password)
            self._dash_c.connect(host, port)
        # Start subscribe, with QoS level 0
        self.start()
        time.sleep(1)

    def close(self):
        """Close the connection."""
        self.running = False

    def run(self):
        self._dash_c.loop_start()

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self._connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)

        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ANNOUNCE")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self._connection_id)
        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break

            if self.rx_zmq_sub in socks:
                [address, _, data] = self.rx_zmq_sub.recv_multipart()
                if not data:
                    continue
                msg_l = data.split(b'\t')
                try:
                    device_id = msg_l[1].decode('utf-8').strip()
                except IndexError:
                    continue
                if address == b'ALARM':
                    data_topic = f"{self.username}/{device_id}/alarm"
                elif address == b"ANNOUNCE":
                    data_topic = f"{self.username}/{device_id}/announce"
                else:
                    data_topic = f"{self.username}/{device_id}/data"
                if self._connected:
                    logging.debug("DASH TX:\n%s", data.decode('utf-8').rstrip())
                    self._dash_c.publish(data_topic, data.decode('utf-8'))

        # if self.connected:
        #     self.dash_c.publish(self.announce_topic, "disconnect")
        self._dash_c.loop_stop()

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
