import threading
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
import shortuuid
from .constants import *
import time
import json

class Dash(object):
    
    def get_state(self) -> str:
        return ""

    def get_cfg(self, page_size_x, page_size_y):
        cfg_str = "\tCFG\t" + self.msg_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, username="", servername=""):
        self.msg_type = "DASHIO"
        self._cfg = {}
        self.control_id = control_id
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


class dashConnection(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.disconnect = False
            self._send_dash_announce()
            for device_id in self.device_id_list:
                control_topic = "{}/{}/control".format(self.username, device_id)
                self.dash_c.subscribe(control_topic, 0)
            logging.debug("connected OK")
        else:
            logging.debug("Bad connection Returned code=%s", rc)

    def __on_disconnect(self, client, userdata, rc):
        logging.debug("disconnecting reason  " + str(rc))
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
                self._send_dash_announce()

    def _send_dash_announce(self):
        self.tx_zmq_pub.send_multipart([b'COMMAND', b'1', b"send_announce"])

    def set_connection(self, username, password):
        self.dash_c.disconnect()
        self.username = username
        self.dash_c.username_pw_set(username, password)
        self.dash_c.connect(self.host, self.port)

    def __init__(self, username="", password="", host='dash.dashio.io', port=8883, set_by_iotdashboard=False, context=None):
        """
        Arguments:
            host {str} -- The server name of the dash host.
            port {int} -- Port number to connect to.
            username {str} -- username for the dash connection.
            password {str} -- password for the dash connection.
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.connected = False
        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')
        self.device_id_list = []
        self.LWD = "OFFLINE"
        self.running = True
        self.username = username
        self.dash_c = mqtt.Client()
        self.host = host
        self.port = port
        self.set_by_iotdashboard = set_by_iotdashboard
        # Assign event callbacks
        self.dash_c.on_message = self.__on_message
        self.dash_c.on_connect = self.__on_connect
        self.dash_c.on_disconnect = self.__on_disconnect
        # self.dash_c.on_publish = self.__on_publish
        self.dash_c.on_subscribe = self.__on_subscribe
        self.dash_control = Dash(self.connection_id, username, host)
        self.dash_c.tls_set(
            ca_certs=None,
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None,
        )
        self.dash_c.tls_insecure_set(False)

        self.dash_c.on_log = self.__on_log
        # self.dash_c.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        if username and password:
            self.dash_c.username_pw_set(username, password)
            self.dash_c.connect(host, port)
        # Start subscribe, with QoS level 0
        self.start()
        time.sleep(1)

    def close(self):
        self.running = False

    def run(self):
        self.dash_c.loop_start()

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)

        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ANNOUNCE")
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
                try:
                    device_id = msg_l[1].decode('utf-8').strip()
                except IndexError:
                    continue
                if address == b'ALARM':
                    data_topic = "{}/{}/alarm".format(self.username, device_id)
                elif address == b"ANNOUNCE":
                    data_topic = "{}/{}/announce".format(self.username, device_id)
                else:
                    data_topic = "{}/{}/data".format(self.username, device_id)
                if self.connected:
                    logging.debug("DASH TX: %s", data.decode('utf-8').rstrip())
                    self.dash_c.publish(data_topic, data.decode('utf-8'))

        if self.connected:
            self.dash_c.publish(self.announce_topic, "disconnect")
        self.dash_c.loop_stop()

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
