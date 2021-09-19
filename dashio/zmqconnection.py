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
import logging
import socket
import threading

import shortuuid
import zmq
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from . import ip
from .constants import CONNECTION_PUB_URL

class ZMQConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via ZMQ."""

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
        """Add a device to the connection

        Parameters
        ----------
        device : Device
            The device to add to the connection
        """
        device.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.connection_id))
        device.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)
        sub_topic = "\t{}".format(device.device_id)
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, sub_topic.encode('utf-8'))

    def close(self):
        """Close the connection."""

        self.zeroconf.unregister_all_services()
        self.zeroconf.close()
        self.running = False

    def __init__(self, zmq_out_url="*", pub_port=5555, sub_port=5556, context=None):
        """ZMQConnection

        Parameters
        ---------
            zmq_out_url (str, optional):
                URL to use. Defaults to "*".
            pub_port (int, optional):
                Port to publish with. Defaults to 5555.
            sub_port (int, optional):
                Port to subscribe with. Defaults to 5556.
            context (ZMQ Context, optional): Defaults to None.
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.running = True

        self.tx_url_external = f"tcp://{zmq_out_url}:{pub_port}"
        self.rx_url_external = f"tcp://{zmq_out_url}:{sub_port}"

        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')

        self.tx_url_internal = f"inproc://TX_{self.connection_id}"
        self.rx_url_internal = f"inproc://RX_{self.connection_id}"

        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = "{}.local".format(host_list[0])

        self.local_ip = ip.get_local_ip_address()
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
                [address, _, data] = rx_zmq_sub.recv_multipart()
                if address in (b'ALL', self.b_connection_id):
                    logging.debug("ZMQ Tx: %s", data.decode('utf-8').rstrip())
                    ext_tx_zmq_pub.send(data)

        tx_zmq_pub.close()
        rx_zmq_sub.close()
