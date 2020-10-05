import threading
import time
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page

# TODO: Add documentation


class mqttConnectionThread(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        logging.debug("rc: %s", str(rc))

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logging.debug("MQTT RX: %s", data)
        self.tx_zmq_pub.send_multipart([self.b_connection_id, b'0', msg.payload])

    def __on_publish(self, client, obj, mid):
        pass

    def __on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def __on_log(self, client, obj, level, string):
        logging.debug(string)

    def __init__(self, connection_id, device_id, host, port, username="", password="", use_ssl=False, context=None):
        """
        Arguments:
            device_type {str} --  The connection name as advertised to iotdashboard.
            host {str} -- The server name of the mqtt host.
            port {int} -- Port number to connect to.
            username {str} -- username for the mqtt connection.
            password {str} -- password for the mqtt connection.

        Keyword Arguments:
            use_ssl {bool} -- Whether to use ssl for the connection or not. (default: {False})
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
        """

        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.b_connection_id = connection_id.encode('utf-8')

        tx_url_internal = "inproc://TX_{}".format(device_id)
        rx_url_internal = "inproc://RX_{}".format(device_id)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.connect(tx_url_internal)

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.connect(rx_url_internal)

        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)

        self.poller = zmq.Poller()
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.LWD = "OFFLINE"
        self.running = True
        self.username = username
        self.mqttc = mqtt.Client()

        # Assign event callbacks
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_connect = self.__on_connect
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

        self.control_topic = "{}/{}/{}/control".format(username, connection_id, device_id)
        self.data_topic = "{}/{}/{}/data".format(username, connection_id, device_id)
        self.mqttc.on_log = self.__on_log
        self.mqttc.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        if username and password:
            self.mqttc.username_pw_set(username, password)
        self.mqttc.connect(host, port)
        # Start subscribe, with QoS level 0
        self.mqttc.subscribe(self.control_topic, 0)
        self.start()

    def run(self):
        self.mqttc.loop_start()

        while self.running:
            socks = dict(self.poller.poll())
            if self.rx_zmq_sub in socks:
                [address, id, data] = self.rx_zmq_sub.recv_multipart()
                logging.debug("%s TX: %s", self.b_connection_id, data.rstrip())
                self.mqttc.publish(self.data_topic, data)

        self.mqttc.loop_stop()
