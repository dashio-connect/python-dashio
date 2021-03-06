import threading
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
import shortuuid


class dashConnection(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.disconnect = False
            if self.device_list:
                for device in self.device_list:
                    control_topic = "{}/{}/control".format(self.username, device.device_id)
                    self.dash_c.subscribe(control_topic, 0)
                    self.__send_dash_announce(device)
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
        device.add_connection(self.connection_id)
        self.device_list.append(device)
        if self.connected:
            control_topic = "{}/{}/control".format(self.username, device.device_id)
            self.dash_c.subscribe(control_topic, 0)
            self.__send_dash_announce(device)

    def __send_dash_announce(self, device):
        data_topic = "{}/{}/announce".format(self.username, device.device_id)
        data = device.device_id_str + "\tWHO\t{}\t{}\n".format(device.device_type, device.device_name_cntrl.control_id)
        self.dash_c.publish(data_topic, data)

    def __set_connection(self, username, password):
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
        self.device_list = []
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

    def close(self):
        self.running = False

    def run(self):
        self.dash_c.loop_start()

        tx_url_internal = "inproc://TX_{}".format(self.connection_id)
        rx_url_internal = "inproc://RX_{}".format(self.connection_id)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(tx_url_internal)

        rx_zmq_sub = self.context.socket(zmq.SUB)
        rx_zmq_sub.bind(rx_url_internal)

        # Subscribe on ALL, and my connection
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ANNOUNCE")
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
                try:
                    device_id = msg_l[1].decode('utf-8').strip()
                except IndexError:
                    continue
                if address == b'ALARM':
                    data_topic = "{}/{}/alarm".format(self.username, device_id)
                else:
                    data_topic = "{}/{}/data".format(self.username, device_id)
                if self.connected:
                    logging.debug("DASH TX: %s", data.decode('utf-8').rstrip())
                    self.dash_c.publish(data_topic, data.decode('utf-8'))

        if self.connected:
            self.dash_c.publish(self.announce_topic, "disconnect")
        self.dash_c.loop_stop()

        self.tx_zmq_pub.close()
        rx_zmq_sub.close()
