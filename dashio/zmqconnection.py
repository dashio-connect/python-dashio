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
import json
import shortuuid
import zmq
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from . import ip
from .constants import CONNECTION_PUB_URL


class ZMQConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via ZMQ."""

    def _zconf_publish_zmq(self, sub_port, pub_port):
        zconf_desc = {
            'subPort': str(sub_port),
            'pubPort': str(pub_port),
            'deviceID': ','.join(self.device_id_list)
        }

        zconf_info = ServiceInfo(
            "_DashZMQ._tcp.local.",
            f"{self.zmq_connection_uuid}._DashZMQ._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip)],
            port=pub_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.update_service(zconf_info)


    def add_device(self, device):
        """Add a Device to the connextion

        Parameters
        ----------
            device (Device):
                The Device to add.
        """
        if device.device_id not in self._device_id_list:
            self._device_id_list.append(device.device_id)
            device.register_connection(self)
            self._send_dash_announce()


    def _send_dash_announce(self):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid
        }
        logging.debug("ZMQ SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])


    def close(self):
        """Close the connection."""

        self.zeroconf.unregister_all_services()
        self.zeroconf.close()
        self.running = False

    def __init__(self, zmq_out_url="*", pub_port=5555, sub_port=5556, context: zmq.Context=None):
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

        self._device_id_list = []
        self.zmq_connection_uuid = "ZMQ:" + shortuuid.uuid()
        self.b_zmq_connection_id = self.zmq_connection_uuid.encode('utf-8')

        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"

        self.local_ip = ip.get_local_ip_address()
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self._zconf_publish_zmq(sub_port, pub_port)
        self.start()


    def _add_device_rx(self, msg_dict):
        """Connect to another device"""
        device_id = msg_dict["deviceID"]
        logging.debug("ZMQ DEVICE CONNECT: %s", device_id)
        # TODO finish this

    def _del_device_rx(self, msg_dict):
        device_id = msg_dict["deviceID"]
        logging.debug("TCP DEVICE_DISCONNECT: %s", device_id)
         # TODO finish this

    def _zmq_command(self, msg_dict: dict):
        logging.debug("TCP CMD: %s", msg_dict)
        if msg_dict['msgType'] == 'connect':
            self._add_device_rx(msg_dict)
        if msg_dict['msgType'] == 'disconnect':
            self._del_device_rx(msg_dict)

    def run(self):

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        #  Subscribe on ALL, and my connection
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "COMMAND")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "MQTT")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)
        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")

        ext_tx_zmq_pub = self.context.socket(zmq.PUB)
        ext_tx_zmq_pub.bind(self.tx_url_external)

        self.ext_rx_zmq_sub = self.context.socket(zmq.SUB)
        self.ext_rx_zmq_sub.bind(self.rx_url_external)

        # Subscribe on WHO, and my deviceID
        self.ext_rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b'\tWHO')

        poller = zmq.Poller()
        poller.register(self.ext_rx_zmq_sub, zmq.POLLIN)
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.ext_rx_zmq_sub in socks:
                message = self.ext_rx_zmq_sub.recv()
                logging.debug("ZMQ Rx: %s", message.decode('utf-8').rstrip())
                self.tx_zmq_pub.send_multipart([message, self.b_zmq_connection_id])

            if self.rx_zmq_sub in socks:
                [msg_to, data] = self.rx_zmq_sub.recv_multipart()

                if msg_to == b'ALL':
                    logging.debug("ZMQ Tx: %s", data.decode('utf-8').rstrip())
                    ext_tx_zmq_pub.send(data)
                elif msg_to == b'COMMAND':
                    self._zmq_command(json.loads(data))
                    return

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
