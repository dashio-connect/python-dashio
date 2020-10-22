import threading
import time
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
import signal
import socket
import multiping
import ipaddress
import netifaces
from zeroconf import IPVersion, ServiceInfo, Zeroconf, ServiceBrowser

# TODO: Add documentation


class ZeroConfDashTCPListener:
    def __init__(self, context=None):
        self.context = context or zmq.Context.instance()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.bind("inproc://zconf")

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            self.zmq_socket.send_multipart([b"remove", socket.inet_ntoa(info.addresses[0]).encode('utf-8'), str(info.port).encode('utf-8')])

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            self.zmq_socket.send_multipart([b"add", socket.inet_ntoa(info.addresses[0]).encode('utf-8'), str(info.port).encode('utf-8')])

    def update_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            self.zmq_socket.send_multipart([b"update", socket.inet_ntoa(info.addresses[0]).encode('utf-8'), str(info.port).encode('utf-8')])


class TCPPoller(threading.Thread):

    def check_port(self, ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
            #  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            socket.setdefaulttimeout(1.0)  # seconds (float)
            result = sock.connect_ex((ip, port))
            if result == 0:
                if ip not in self.open_address_list:
                    self.open_address_list.append(ip)
            sock.close()
        except:
            pass

    def __init__(self, port=5000, context=None):
        """

        """
        self.port = port
        self.finish = False
        threading.Thread.__init__(self, daemon=True)
        self.max_threads = 50

        self.context = context or zmq.Context.instance()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.bind("inproc://tcp_poller")
        self.open_address_list = []
        gws = netifaces.gateways()
        net_dict = netifaces.ifaddresses(gws['default'][netifaces.AF_INET][1])[netifaces.AF_INET]
        net_str = '{}/{}'.format(net_dict[0]['addr'], net_dict[0]['netmask'])
        self.network = ipaddress.IPv4Network(net_str, strict=False)
        self.start()

    def run(self):
        while not self.finish:
            for ip in self.network:
                threading.Thread(target=self.check_port, args=[str(ip), self.port]).start()
                #  sleep(0.1)

            # limit the number of threads.
            while threading.active_count() > self.max_threads:
                time.sleep(1)
            print(self.open_address_list)

            time.sleep(60)


class tcp_dashBridge(threading.Thread):
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

    def __init__(
        self, username, password, host='dash.dashio.io', port=8883, context=None
    ):
        """

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
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ANNOUNCE")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)

        self.poller = zmq.Poller()
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.LWD = "OFFLINE"
        self.running = True
        self.username = username
        self.dash_c = mqtt.Client()

        # Assign event callbacks
        self.dash_c.on_message = self.__on_message
        self.dash_c.on_connect = self.__on_connect
        self.dash_c.on_publish = self.__on_publish
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

        self.control_topic = "{}/{}/control".format(username, device_id)
        self.data_topic = "{}/{}/data".format(username, device_id)
        self.alarm_topic = "{}/{}/alarm".format(username, device_id)
        self.announce_topic = "{}/{}/announce".format(username, device_id)
        self.dash_c.on_log = self.__on_log
        self.dash_c.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        self.dash_c.username_pw_set(username, password)
        self.dash_c.connect(host, port)
        # Start subscribe, with QoS level 0
        self.dash_c.subscribe(self.control_topic, 0)
        self.start()

    def run(self):
        self.dash_c.loop_start()

        while self.running:
            socks = dict(self.poller.poll())

            if self.rx_zmq_sub in socks:
                [address, id, data] = self.rx_zmq_sub.recv_multipart()
                logging.debug("%s TX: %s", self.b_connection_id.decode('utf-8'), data.decode('utf-8').rstrip())
                if address == b'ANNOUNCE':
                    self.dash_c.publish(self.announce_topic, data)
                elif address == b'ALARM':
                    self.dash_c.publish(self.alarm_topic, data)
                else:
                    self.dash_c.publish(self.data_topic, data)

        self.dash_c.publish(self.announce_topic, "disconnect")
        self.dash_c.loop_stop()

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()


def init_logging(logfilename, level):
    log_level = logging.WARN
    if level == 1:
        log_level = logging.INFO
    elif level == 2:
        log_level = logging.DEBUG
    if not logfilename:
        formatter = logging.Formatter("%(asctime)s, %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(log_level)
    else:
        logging.basicConfig(
            filename=logfilename,
            level=log_level,
            format="%(asctime)s, %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    logging.info("==== Started ====")


shutdown = False


def signal_cntrl_c(os_signal, os_frame):
    global shutdown
    shutdown = True


def main():
    # Catch CNTRL-C signel
    global shutdown
    signal.signal(signal.SIGINT, signal_cntrl_c)

    init_logging("", 2)

    context = zmq.Context.instance()
    zeroconf = Zeroconf()
    listener = ZeroConfDashTCPListener(context)
    browser = ServiceBrowser(zeroconf, "_DashTCP._tcp.local.", listener)
    pinger = TCPPoller()
    # b = tcp_dashBridge(context=context)

    while not shutdown:
        time.sleep(5)


if __name__ == "__main__":
    main()
