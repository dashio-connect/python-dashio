import threading
import time
import paho.mqtt.client as mqtt
import ssl
import logging
import zmq
import signal
import socket
import configparser
import ipaddress
import netifaces
from zeroconf import IPVersion, ServiceInfo, Zeroconf, ServiceBrowser

# TODO: Add documentation


class ZeroConfDashTCPListener:
    def __init__(self, context=None):
        self.context = context or zmq.Context.instance()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.connect("inproc://zconf")

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            for address in info.addresses:
                self.zmq_socket.send_multipart([b"remove", socket.inet_ntoa(address).encode('utf-8'), str(info.port).encode('utf-8')])

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            for address in info.addresses:
                logging.debug('IP: %s', socket.inet_ntoa(address).encode('utf-8'))
                self.zmq_socket.send_multipart([b"add", socket.inet_ntoa(address).encode('utf-8'), str(info.port).encode('utf-8')])

    def update_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            for address in info.addresses:
                self.zmq_socket.send_multipart([b"update", socket.inet_ntoa(address).encode('utf-8'), str(info.port).encode('utf-8')])


class TCPPoller(threading.Thread):

    def check_port(self, ip, port, context):
        self.context = context or zmq.Context.instance()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.connect("inproc://zconf")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
            #  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            socket.setdefaulttimeout(1.0)  # seconds (float)
            result = sock.connect_ex((ip, port))
            if result == 0:
                if ip not in self.open_address_list:
                    self.open_address_list.append(ip)
                    self.zmq_socket.send_multipart([b"add", ip.encode('utf-8'), str(port).encode('utf-8')])
            else:
                if ip in self.open_address_list:
                    self.open_address_list.remove(ip)
                    self.zmq_socket.send_multipart([b"remove", ip.encode('utf-8'), str(port).encode('utf-8')])
            sock.close()
        except socket.error:
            pass

    def remove_ip(self, ip_address):
        if ipaddress in self.network:
            self.network.remove(ip_address)

    def add_ip(self, ip_address):
        if ipaddress not in self.network:
            self.network.append(ip_address)

    def __init__(self, port=5000, context=None):
        self.port = port
        self.context = context
        self.finish = False
        threading.Thread.__init__(self, daemon=True)
        self.max_threads = 255

        self.open_address_list = []
        gws = netifaces.gateways()
        net_dict = netifaces.ifaddresses(gws['default'][netifaces.AF_INET][1])[netifaces.AF_INET]
        net_str = '{}/{}'.format(net_dict[0]['addr'], net_dict[0]['netmask'])
        self.network = [str(ip) for ip in ipaddress.IPv4Network(net_str, strict=False)]
        self.start()

    def run(self):
        while not self.finish:
            for ip in self.network:
                threading.Thread(target=self.check_port, args=[ip, self.port, self.context]).start()

            # limit the number of threads.
            while threading.active_count() > self.max_threads:
                time.sleep(1)
            time.sleep(60)


class tcp_dashBridge(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        logging.debug("rc: %s", str(rc))

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        topic_array = msg.topic.split("/")
        device_id = topic_array[1]
        logging.debug("BRIDGE Dash: RX: %s", data)
        self.tcp_socket.send(self.tcp_device_dict[device_id.encode('utf-8')], zmq.SNDMORE)
        self.tcp_socket.send(msg.payload)

    def __on_publish(self, client, obj, mid):
        pass

    def __on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def __on_log(self, client, obj, level, string):
        logging.debug(string)

    def add_device(self, ip_address, port):
        url = "tcp://{}:{}".format(ip_address.decode('utf-8'), port.decode('utf-8'))
        print(url)
        self.tcp_socket.connect(url)
        id = self.tcp_socket.getsockopt(zmq.IDENTITY)
        try:
            self.tcp_socket.send(id, zmq.SNDMORE)
            self.tcp_socket.send_string('\tWHO\n')
            logging.debug("BRIDGE TX: \tWHO")
        except zmq.error.ZMQError:
            logging.debug("Sending TX Error.")
            self.tcp_socket.send(b'')
        time.sleep(0.1)
        return id

    def remove_device(self, ip_address, port):
        pass

    def __init__(self, username, password, host='dash.dashio.io', port=8883, context=None, ignore_devices=None):

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.ignore_list = ignore_devices

        self.tcp_id_dict = {}
        self.tcp_device_dict = {}

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

        self.dash_c.username_pw_set(username, password)
        self.dash_c.connect(host, port)
        self.username = username
        self.start()

    def announce_device(self, device_id, message):
        logging.debug("Adding device: %s", device_id)
        control_topic = "{}/{}/control".format(self.username, device_id)
        announce_topic = "{}/{}/announce".format(self.username, device_id)
        self.dash_c.subscribe(control_topic, 0)
        self.dash_c.publish(announce_topic, message)

    def clear_device(self, device_id):
        logging.debug("Removing device: %s", device_id)
        control_topic = "{}/{}/control".format(self.username, device_id)
        id = self.tcp_device_dict[device_id.encode('utf-8')]
        self.tcp_device_dict.pop(device_id.encode('utf-8'))
        self.tcp_id_dict.pop(id)
        self.dash_c.unsubscribe(control_topic)

    def run(self):
        self.dash_c.loop_start()

        self.tcp_socket = self.context.socket(zmq.STREAM)
        self.tcp_socket.set(zmq.SNDTIMEO, 1)

        rx_zconf_pull = self.context.socket(zmq.PULL)
        rx_zconf_pull.bind("inproc://zconf")

        poller = zmq.Poller()
        poller.register(rx_zconf_pull, zmq.POLLIN)
        poller.register(self.tcp_socket, zmq.POLLIN)

        while self.running:
            socks = dict(self.poller.poll(50))

            if rx_zconf_pull in socks:
                action, ip_address, port = rx_zconf_pull.recv_multipart()
                if action == b'add':
                    logging.debug("Adding device: %s:%s", ip_address.decode('utf-8'), port.decode('utf-8'))
                    self.add_device(ip_address, port)
                elif action == b'remove':
                    logging.debug("Remove device: %s:%s", ip_address.decode('utf-8'), port.decode('utf-8'))
                    self.remove_device(ip_address, port)
            if self.tcp_socket in socks:
                id = self.tcp_socket.recv()
                message = self.tcp_socket.recv()
                if message:
                    if id not in self.tcp_id_dict:
                        msg_l = message.split(b'\t')
                        if (len(msg_l) > 3) and (msg_l[2] == b'WHO') and (msg_l[1] not in self.tcp_device_dict) and (msg_l[1].decode('utf-8') not in self.ignore_list):
                            logging.debug("Added device: %s", msg_l[1].decode('utf-8'))
                            self.tcp_id_dict[id] = msg_l[1]
                            self.tcp_device_dict[msg_l[1]] = id
                            self.announce_device(msg_l[1].decode('utf-8'), message)
                            continue
                        self.tcp_socket.send(id, zmq.SNDMORE)
                        self.tcp_socket.send(b'')
                    else:
                        logging.debug("BRIDGE  TCP: RX: %s", message.decode('utf-8').strip())
                        msg_l = message.split(b'\t')
                        if msg_l[2] == b'ALM':
                            data_topic = "{}/{}/alarm".format(self.username, self.tcp_id_dict[id].decode('utf-8'))
                        else:
                            data_topic = "{}/{}/data".format(self.username, self.tcp_id_dict[id].decode('utf-8'))
                        self.dash_c.publish(data_topic, message)
                elif id in self.tcp_id_dict:
                    self.clear_device(self.tcp_id_dict[id].decode('utf-8'))

        self.dash_c.loop_stop()
        rx_zconf_pull.close()
        self.tcp_socket.close()


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


def load_configfile(filename):
    config_file_parser = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_file_parser.defaults()
    config_file_parser.read(filename)
    return config_file_parser


def main():
    # Catch CNTRL-C signel
    global shutdown
    signal.signal(signal.SIGINT, signal_cntrl_c)

    init_logging("", 2)

    configs = load_configfile("bridge.ini")
    ignore_list = configs.getlist('Device', 'Ignore')
    context = zmq.Context.instance()
    zeroconf = Zeroconf()
    listener = ZeroConfDashTCPListener(context)
    browser = ServiceBrowser(zeroconf, "_DashIO._tcp.local.", listener)
    pinger = TCPPoller(port=5000, context=context)
    b = tcp_dashBridge(
        configs.get('Dash', 'Username'),
        configs.get('Dash', 'Password'),
        host=configs.get('Dash', 'Server'),
        port=configs.getint('Dash', 'Port'),
        ignore_devices=ignore_list,
        context=context
    )

    while not shutdown:
        time.sleep(5)

    zeroconf.unregister_all_services()
    zeroconf.close()


if __name__ == "__main__":
    main()
