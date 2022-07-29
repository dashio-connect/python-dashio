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
import shortuuid

import paho.mqtt.client as mqtt
import zmq

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL


class MQTT():
    """A CFG only control"""
    def get_state(self):
        """Not used by this class as its a CFG only control
        """
        return ""

    def get_cfg(self, data):
        """Returns the CFG string for this TCP control

        Returns
        -------
        str
            The CFG string for this control
        """
        try:
            num_columns = data[3]
            dashboard_id = data[2]
        except IndexError:
            return
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id: str, username="", password="", servername="", use_ssl=False):
        self._cfg = {}
        self.cntrl_type = "MQTT"
        self.control_id = control_id
        self.username = username
        self.servername = servername
        self.password = password
        self.use_ssl = use_ssl

    def set_mqtt(self, username: str, servername: str):
        """Set the connection parameters for mqtt

        Parameters
        ----------
        username : str
            username
        servername : [type]
            servername
        """
        self.username = username
        self.servername = servername

    @property
    def username(self) -> str:
        """username

        Returns
        -------
        str
            username
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
            servername
        """
        return self._cfg["hostURL"]

    @servername.setter
    def servername(self, val: str):
        self._cfg["hostURL"] = val


class MQTTConnection(threading.Thread):
    """Setups and manages a connection thread to the MQTT Server."""

    def _on_connect(self, client, userdata, flags, msg):
        if msg == 0:
            self.connected = True
            self.disconnect = False
            for device_id in self.device_id_list:
                control_topic = "{}/{}/control".format(self.username, device_id)
                self.mqttc.subscribe(control_topic, 0)
            logging.debug("connected OK")
        else:
            logging.debug("Bad connection Returned code=%s", msg)

    def _on_disconnect(self, client, userdata, msg):
        logging.debug("disconnecting reason  %s", msg)
        self.connected = False
        self.disconnect = True

    def _on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logging.debug("DASH RX: %s", data)
        self.tx_zmq_pub.send_multipart([self.b_connection_id, b'1', msg.payload])

    def _on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def _on_log(self, client, obj, level, string):
        logging.debug(string)

    def add_device(self, device):
        """Add device to the connection

        Parameters
        ---------
            device : Device
                The device to add.
        """
        if device.device_id not in self.device_id_list:
            self.device_id_list.append(device.device_id)
            device.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.connection_id))
            device.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)
            device.add_control(self.mqtt_control)

            self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_pub_id))
            self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)

            if self.connected:
                control_topic = "{}/{}/control".format(self.username, device.device_id)
                self.mqttc.subscribe(control_topic, 0)

    def __init__(self, host, port, username="", password="", use_ssl=False, context=None):
        """
        Setups and manages a connection thread to the MQTT Server.

        Parameters
        ---------
            host : str
                The server name of the mqtt host.
            port {int}:
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
        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')

        self.mqtt_control = MQTT(self.connection_id, username, password, host, use_ssl)
        self.connected = False
        self.disconnect = True
        self.connection_topic_list = []
        self.device_id_list = []

        # self.last_will = "OFFLINE"
        self.running = True
        self.username = username
        self.mqttc = mqtt.Client()

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
        self.mqttc.connect(host, port)
        # Start subscribe, with QoS level 0
        self.start()

    def run(self):
        self.mqttc.loop_start()

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.tx_zmq_pub = self.context.socket(zmq.PUB)


        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_id)

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                [_, _, data] = self.rx_zmq_sub.recv_multipart()
                msg_l = data.split(b'\t')
                device_id = msg_l[1].decode('utf-8').strip()
                if self.connected:
                    logging.debug("%s TX: %s", self.b_connection_id.decode('utf-8'), data.decode('utf-8').rstrip())
                    data_topic = f"{self.username}/{device_id}/data"
                    self.mqttc.publish(data_topic, data)

        self.mqttc.loop_stop()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
