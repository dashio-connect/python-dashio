import threading
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
import uuid
import json

from .constants import *

# TODO: Add documentation

class MQTT(object):

    """A connection only control"""
    def get_state(self):
        return ""
    
    def get_cfg(self, page_size_x, page_size_y):
        cfg_str = "\tCFG\t" + self.msg_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, username="", password="", servername="", use_ssl=False):
        self._cfg = {}
        self.msg_type = "MQTT"
        self.control_id = control_id
        self.username = username
        self.servername = servername

    def set_mqtt(self, username, servername):
        self.username = username
        self.servername = servername

    @property
    def username(self) -> str:
        return self._cfg["userName"]

    @username.setter
    def username(self, val: str):
        self._cfg["userName"] = val

    @property
    def servername(self) -> str:
        return self._cfg["hostURL"]

    @servername.setter
    def servername(self, val: str):
        self._cfg["hostURL"] = val


class mqttConnection(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.disconnect = False
            for device_id in self.device_id_list:
                control_topic = "{}/{}/control".format(self.username, device_id)
                self.dash_c.subscribe(control_topic, 0)
            logging.debug("connected OK")
        else:
            logging.debug("Bad connection Returned code=%s", rc)

    def __on_disconnect(self, client, userdata, rc):
        logging.debug("disconnecting reason  "  + str(rc))
        self.connected = False
        self.disconnect = True

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logging.debug("DASH RX: %s", data)
        self.tx_zmq_pub.send_multipart([self.b_connection_id, b'1', msg.payload])

    def __on_publish(self, client, obj, mid):
        pass

    def __on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def __on_log(self, client, obj, level, string):
        logging.debug(string)
    
    def add_device(self, device):
        if device.device_id not in self.device_id_list:
            self.device_id_list.append(device.device_id)
            device._add_connection(self)
            device.add_control(self.dash_control)

            self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device._zmq_pub_id))
            self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device._zmq_pub_id)

            if self.connected:
                control_topic = "{}/{}/control".format(self.username, device.device_id)
                self.dash_c.subscribe(control_topic, 0)

    def __init__(self, host, port, username="", password="", use_ssl=False, context=None):
        """
        Arguments:
            host {str} -- The server name of the mqtt host.
            port {int} -- Port number to connect to.
            username {str} -- username for the mqtt connection.
            password {str} -- password for the mqtt connection.

        Keyword Arguments:
            use_ssl {bool} -- Whether to use ssl for the connection or not. (default: {False})
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()

        self.connected = False
        self.connection_topic_list = []
        self.device_id_list = []
        self.connection_id = uuid.uuid4()
        self.b_connection_id = self.connection_id.bytes

        self.LWD = "OFFLINE"
        self.running = True
        self.username = username
        self.mqttc = mqtt.Client()

        # Assign event callbacks
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_disconnect = self.__on_disconnect
        self.mqttc.on_publish = self.__on_publish
        self.mqttc.on_subscribe = self.__on_subscribe

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

        self.mqttc.on_log = self.__on_log
        self.mqttc.will_set(self.data_topic, self.LWD, qos=1, retain=False)
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
                [address, id, data] = self.rx_zmq_sub.recv_multipart()
                msg_l = data.split(b'\t')
                device_id = msg_l[1].decode('utf-8').strip()
                if self.connected:
                    logging.debug("%s TX: %s", self.b_connection_id.decode('utf-8'), data.decode('utf-8').rstrip())
                    data_topic = f"{self.username}/{device_id}/data"
                    self.mqttc.publish(data_topic, data)

        self.mqttc.loop_stop()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
