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
import configparser
import ipaddress
import logging
import signal
import socket
import ssl
import threading
import time
from collections import defaultdict

import netifaces
import paho.mqtt.client as mqtt
import zmq
from zeroconf import ServiceBrowser, Zeroconf

# TODO: Add documentation


class ZeroConfDashTCPListener:
    def __init__(self, context=None):
        self.context = context or zmq.Context.instance()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.connect("inproc://zconf")

    def remove_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            for address in info.addresses:
                self.zmq_socket.send_multipart([b"remove", socket.inet_ntoa(address).encode(), str(info.port).encode()])

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            for address in info.addresses:
                logging.debug('IP: %s', socket.inet_ntoa(address).encode())
                self.zmq_socket.send_multipart([b"add", socket.inet_ntoa(address).encode(), str(info.port).encode()])

    def update_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            for address in info.addresses:
                self.zmq_socket.send_multipart([b"update", socket.inet_ntoa(address).encode(), str(info.port).encode()])


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
                    self.zmq_socket.send_multipart([b"add", ip.encode(), str(port).encode()])
            else:
                if ip in self.open_address_list:
                    self.open_address_list.remove(ip)
                    self.zmq_socket.send_multipart([b"remove", ip.encode(), str(port).encode()])
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
        net_str = f"{net_dict[0]['addr']}/{net_dict[0]['netmask']}"
        self.network = [str(ip) for ip in ipaddress.IPv4Network(net_str, strict=False)]
        self.start()

    def close(self):
        self.finish = True

    def run(self):
        while not self.finish:
            for ip in self.network:
                threading.Thread(target=self.check_port, args=[ip, self.port, self.context]).start()

            # limit the number of threads.
            while threading.active_count() > self.max_threads:
                time.sleep(1)
            time.sleep(60)


class TCPDashBridge(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        logging.debug("rc: %s", str(rc))

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        topic_array = msg.topic.split("/")
        device_id = topic_array[1]
        logging.debug("BRIDGE Dash: RX: %s", data)
        self.tcp_socket.send(self.tcp_device_dict[device_id.encode()], zmq.SNDMORE)
        self.tcp_socket.send(msg.payload)

    def __on_publish(self, client, obj, mid):
        pass

    def __on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def __on_log(self, client, obj, level, string):
        logging.debug(string)

    def add_device(self, ip_address, port):
        url = f"tcp://{ip_address.decode()}:{port.decode()}"
        self.tcp_socket.connect(url)
        socket_id = self.tcp_socket.getsockopt(zmq.IDENTITY)
        ip_b = ip_address + b':' + port
        if ip_b not in self.tcp_ip_2_id_dict:
            try:
                self.tcp_socket.send(socket_id, zmq.SNDMORE)
                self.tcp_socket.send_string('\tWHO\n')
                self.tcp_id_2_ip_dict[socket_id] = ip_address + b':' + port
                self.tcp_ip_2_id_dict[ip_address + b':' + port] = socket_id
                logging.debug("BRIDGE TX: \tWHO")

            except zmq.error.ZMQError:
                logging.debug("Sending TX Error.")
                self.tcp_socket.send(b'')
        time.sleep(0.1)
        return socket_id

    def remove_device(self, ip_address, port):
        pass

    def __init__(self, username, password, host='dash.dashio.io', port=8883, context=None, ignore_devices=None):

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.ignore_list = ignore_devices

        # A dictionary of list of tcp ids.
        self.tcp_id_dict = defaultdict(list)
        self.tcp_device_dict = {}
        self.tcp_id_2_ip_dict = {}
        self.tcp_ip_2_id_dict = {}
        self.connected_ip = {}

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
        control_topic = f"{self.username}/{device_id}/control"
        announce_topic = f"{self.username}/{device_id}/announce"
        self.dash_c.subscribe(control_topic, 0)
        self.dash_c.publish(announce_topic, message)

    def clear_device(self, device_id):
        logging.debug("Removing device: %s", device_id)
        control_topic = f"{self.username}/{device_id}/control"
        socket_id = self.tcp_device_dict[device_id.encode()]
        self.tcp_device_dict.pop(device_id.encode())
        try:
            self.tcp_id_dict[socket_id].remove(device_id)
        except ValueError:
            pass
        self.dash_c.unsubscribe(control_topic)

    def close(self):
        self.running = False

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
            socks = dict(poller.poll(50))
            if rx_zconf_pull in socks:
                action, ip_address, port = rx_zconf_pull.recv_multipart()
                if action == b'add':
                    logging.debug("Adding device: %s:%s", ip_address.decode(), port.decode())
                    self.add_device(ip_address, port)
                elif action == b'remove':
                    logging.debug("Remove device: %s:%s", ip_address.decode(), port.decode())
                    self.remove_device(ip_address, port)
            if self.tcp_socket in socks:
                socket_id = self.tcp_socket.recv()
                message = self.tcp_socket.recv()
                if message:
                    msg_l = message.split(b'\t')
                    if len(msg_l) == 1:
                        self.tcp_socket.send(socket_id, zmq.SNDMORE)
                        self.tcp_socket.send(b'')
                    elif msg_l[1] not in self.tcp_device_dict:
                        if (len(msg_l) > 3) and (msg_l[2] == b'WHO') and (msg_l[1].decode() not in self.ignore_list):
                            logging.debug("Added device: %s", msg_l[1].decode())
                            self.tcp_id_dict[socket_id].append(msg_l[1])
                            self.tcp_device_dict[msg_l[1]] = socket_id
                            self.announce_device(msg_l[1].decode(), message)
                    else:
                        logging.debug("BRIDGE  TCP: RX: %s", message.decode().strip())
                        if msg_l[2] == b'ALM':
                            data_topic = f"{self.username}/{msg_l[1].decode()}/alarm"
                        else:
                            data_topic = f"{self.username}/{msg_l[1].decode()}/data"
                        self.dash_c.publish(data_topic, message)
                elif socket_id in self.tcp_id_dict:
                    for device_id in self.tcp_id_dict[socket_id]:
                        self.clear_device(device_id.decode())
                    self.tcp_socket.send(socket_id, zmq.SNDMORE)
                    self.tcp_socket.send(b'')
                    ip_b = self.tcp_id_2_ip_dict[socket_id]
                    self.tcp_id_2_ip_dict.pop(socket_id)
                    self.tcp_ip_2_id_dict.pop(ip_b)


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


SHUTDOWN = False


def signal_cntrl_c(os_signal, os_frame):
    global SHUTDOWN
    SHUTDOWN = True


def load_configfile(filename):
    config_file_parser = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_file_parser.defaults()
    config_file_parser.read(filename)
    return config_file_parser


def main():
    # Catch CNTRL-C signel
    signal.signal(signal.SIGINT, signal_cntrl_c)

    init_logging("", 2)

    configs = load_configfile("bridge.ini")
    ignore_list = configs.getlist('Device', 'Ignore')
    context = zmq.Context.instance()
    zeroconf = Zeroconf()
    listener = ZeroConfDashTCPListener(context)
    browser = ServiceBrowser(zeroconf, "_DashIO._tcp.local.", listener)
    pinger = TCPPoller(port=5000, context=context)
    bridge = TCPDashBridge(
        configs.get('Dash', 'Username'),
        configs.get('Dash', 'Password'),
        host=configs.get('Dash', 'Server'),
        port=configs.getint('Dash', 'Port'),
        ignore_devices=ignore_list,
        context=context
    )

    while not SHUTDOWN:
        time.sleep(5)

    pinger.close()
    bridge.close()
    browser.cancel()
    zeroconf.unregister_all_services()
    zeroconf.close()


if __name__ == "__main__":
    main()
