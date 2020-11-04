import threading
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
import uuid
# TODO: Add documentation


class mqttConnection(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        logging.debug("rc: %s", str(rc))

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
        device.add_connection(self.connection_id)
        control_topic = "{}/{}/control".format(self.username, device.device_id)
        self.dash_c.subscribe(control_topic, 0)

    def __init__(self, device_id, host, port, username="", password="", use_ssl=False, context=None):
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

        self.connection_id = uuid.uuid4()
        self.b_connection_id = self.connection_id.bytes

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

        tx_url_internal = "inproc://TX_{}".format(self.connection_id.hex)
        rx_url_internal = "inproc://RX_{}".format(self.connection_id.hex)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(tx_url_internal)

        rx_zmq_sub = self.context.socket(zmq.SUB)
        rx_zmq_sub.bind(rx_url_internal)

        # Subscribe on ALL, and my connection
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)

        poller = zmq.Poller()
        poller.register(rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if rx_zmq_sub in socks:
                [address, id, data] = rx_zmq_sub.recv_multipart()
                msg_l = data.split(b'\t')
                logging.debug("%s TX: %s", self.b_connection_id.decode('utf-8'), data.decode('utf-8').rstrip())
                data_topic = "{}/{}/data".format(self.username, msg_l[1].decode('utf-8'))
                self.mqttc.publish(data_topic, data)

        self.mqttc.loop_stop()
        self.tx_zmq_pub.close()
        rx_zmq_sub.close()
