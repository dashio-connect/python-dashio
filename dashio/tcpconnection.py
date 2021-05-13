import zmq
import threading
import logging
import shortuuid
import time
import json

from zeroconf import ServiceInfo, Zeroconf, IPVersion
import socket
from .constants import *

class TCP(object):
    def get_state(self) -> str:
        return ""

    def get_cfg(self, page_size_x, page_size_y):
        cfg_str = "\tCFG\t" + self.msg_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, ip_address="", port=5650):
        self._cfg = {}
        self.msg_type = "TCP"
        self.control_id = control_id
        self.ip_address = ip_address
        self.port = port

    @property
    def ip_address(self) -> str:
        return self._cfg["ipAddress"]

    @ip_address.setter
    def ip_address(self, val: str):
        self._cfg["ipAddress"] = val

    @property
    def port(self) -> int:
        return self._cfg["port"]

    @port.setter
    def port(self, val: int):
        self._cfg["port"] = val

class tcpConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def _get_local_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def _zconf_publish_tcp(self, port):
        zconf_desc = {'ConnectionUUID': self.connection_id}
        zconf_info = ServiceInfo(
            "_DashIO._tcp.local.",
            "{}._DashIO._tcp.local.".format(self.connection_id),
            addresses=[socket.inet_aton(self.local_ip)],
            port=port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.register_service(zconf_info)

    def add_device(self, device):
        device._add_connection(self)
        device.add_control(self.tcp_control)

        self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device._zmq_pub_id))
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device._zmq_pub_id)

    def __init__(self, ip="*", port=5650, use_zero_conf=True, context=None):
        """
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')
        self.use_zeroconf = use_zero_conf
        self.ext_url = "tcp://" + ip + ":" + str(port)

        self.socket_ids = []
        self.running = True

        host_name = socket.gethostname()
        hs = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{hs[0]}.local"
        self.local_ip = self._get_local_ip_address()
        if self.use_zeroconf:
            self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            self.tcp_control = TCP(self.connection_id, "", 0)
            self._zconf_publish_tcp(port)
        else:
            self.tcp_control = TCP(self.connection_id, self.local_ip, port)
        self.start()
        time.sleep(1)

    def close(self):
        if self.use_zeroconf:
            self.zeroconf.unregister_all_services()
            self.zeroconf.close()
        self.running = False

    def run(self):
        def __zmq_tcp_send(id, data):
            try:
                tcpsocket.send(id, zmq.SNDMORE)
                tcpsocket.send(data, zmq.NOBLOCK)
            except zmq.error.ZMQError as e:
                logging.debug("Sending TX Error: " + str(e))
                # self.socket_ids.remove(id)

        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALARM")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_id)
        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")

        tcpsocket = self.context.socket(zmq.STREAM)

        tcpsocket.bind(self.ext_url)
        tcpsocket.set(zmq.SNDTIMEO, 5)

        poller = zmq.Poller()
        poller.register(tcpsocket, zmq.POLLIN)
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        id = tcpsocket.recv()
        tcpsocket.recv()  # empty data here

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break

            if tcpsocket in socks:
                id = tcpsocket.recv()
                message = tcpsocket.recv()
                if id not in self.socket_ids:
                    logging.debug("Added Socket ID: " + id.hex())
                    self.socket_ids.append(id)
                logging.debug("TCP ID: %s, Rx:\n%s", id.hex(), message.decode('utf-8').rstrip())
                if message:
                    tx_zmq_pub.send_multipart([self.b_connection_id, id, message])
                else:
                    if id in self.socket_ids:
                        logging.debug("Removed Socket ID: " + id.hex())
                        self.socket_ids.remove(id)
            if self.rx_zmq_sub in socks:
                [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
                if not data:
                    continue
                if address == b'ALL':
                    for id in self.socket_ids:
                        logging.debug("TCP ID: %s, Tx:\n%s", id.hex(), data.decode('utf-8').rstrip())
                        __zmq_tcp_send(id, data)
                elif address == self.b_connection_id:
                    logging.debug("TCP ID: %s, Tx:\n%s", msg_id.hex(), data.decode('utf-8').rstrip())
                    __zmq_tcp_send(msg_id, data)

        for id in self.socket_ids:
            __zmq_tcp_send(id, b'')

        self.tcpsocket.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
