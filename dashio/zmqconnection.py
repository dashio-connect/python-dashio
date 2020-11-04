import zmq
import threading
import logging
import shortuuid
from zeroconf import ServiceInfo, Zeroconf, IPVersion
import socket


class zmqConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __get_local_ip_address(self):
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

    def __zconf_publish_zmq(self, sub_port, pub_port):
        zconf_desc = {'sub_port': str(sub_port),
                      'pub_port': str(pub_port)}

        zconf_info = ServiceInfo(
            "_DashZMQ._tcp.local.",
            "{}._DashZMQ._tcp.local.".format(self.connection_id),
            addresses=[socket.inet_aton(self.local_ip)],
            port=pub_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.register_service(zconf_info)

    def add_device(self, device):
        device.add_connection(self.connection_id)
        sub_topic = "\t{}".format(device.device_id)
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, sub_topic.encode('utf-8'))

    def close(self):
        self.zeroconf.unregister_all_services()
        self.zeroconf.close()
        self.running = False

    def __init__(self, zmq_out_url="*", pub_port=5555, sub_port=5556, context=None):
        """
        Arguments: figure it out for yourself.
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.running = True

        self.tx_url_external = "tcp://{}:{}".format(zmq_out_url, pub_port)
        self.rx_url_external = "tcp://{}:{}".format(zmq_out_url, sub_port)

        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')

        self.tx_url_internal = "inproc://TX_{}".format(self.connection_id)
        self.rx_url_internal = "inproc://RX_{}".format(self.connection_id)

        host_name = socket.gethostname()
        hs = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = "{}.local".format(hs[0])

        self.local_ip = self.__get_local_ip_address()
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.__zconf_publish_zmq(sub_port, pub_port)
        self.start()

    def run(self):

        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(self.tx_url_internal)

        rx_zmq_sub = self.context.socket(zmq.SUB)
        rx_zmq_sub.bind(self.rx_url_internal)

        #  Subscribe on ALL, and my connection
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALL")
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"ALARM")
        rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)

        ext_tx_zmq_pub = self.context.socket(zmq.PUB)
        ext_tx_zmq_pub.bind(self.tx_url_external)

        self.ext_rx_zmq_sub = self.context.socket(zmq.SUB)
        self.ext_rx_zmq_sub.bind(self.rx_url_external)

        # Subscribe on WHO, and my deviceID
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b'\tWHO')

        poller = zmq.Poller()
        poller.register(self.ext_rx_zmq_sub, zmq.POLLIN)
        poller.register(rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.ext_rx_zmq_sub in socks:
                message = self.ext_rx_zmq_sub.recv()
                logging.debug("ZMQ Rx: %s", message.decode('utf-8').rstrip())
                tx_zmq_pub.send_multipart([self.b_connection_id, b'', message])

            if rx_zmq_sub in socks:
                [address, msg_id, data] = rx_zmq_sub.recv_multipart()
                if address == b'ALL' or address == self.b_connection_id:
                    logging.debug("ZMQ Tx: %s", data.decode('utf-8').rstrip())
                    ext_tx_zmq_pub.send(data)

        tx_zmq_pub.close()
        rx_zmq_sub.close()
