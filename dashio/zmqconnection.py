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


class ZMQControl():
    """A CFG control class to store ZMQ connection information
    """

    def get_state(self) -> str:
        """Returns controls state. Not used for this control

        Returns
        -------
        str
            Not used in this control
        """
        return ""

    def get_cfg(self, data) -> str:
        """Returns the CFG string for this ZMQ control

        Returns
        -------
        str
            The CFG string for this control
        """
        try:
            dashboard_id = data[2]
        except IndexError:
            return ""
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def get_cfg64(self, data) -> dict:
        """Returns the CFG dict for this ZMQ control

        Returns
        -------
        dict
            The CFG string for this control
        """
        return self._cfg

    def __init__(self, control_id, zmq_url="*", pub_port=5555, sub_port=5556):
        self._cfg = {}
        self.cntrl_type = "TCP"
        self._cfg["controlID"] = control_id
        self.control_id = control_id
        self.zmq_url = zmq_url
        self.pub_port = pub_port
        self.sub_port = sub_port

    @property
    def zmq_url(self) -> str:
        """IP address of current connection

        Returns
        -------
        str
            IP address
        """
        return self._cfg["url"]

    @zmq_url.setter
    def zmq_url(self, val: str):
        self._cfg["url"] = val

    @property
    def pub_port(self) -> int:
        """The pub_port of the current connection

        Returns
        -------
        int
            The pub_port number used by the current connection
        """
        return self._cfg["pubPort"]

    @pub_port.setter
    def pub_port(self, val: int):
        self._cfg["pubPort"] = val

    @property
    def sub_port(self) -> int:
        """The sub_port of the current connection

        Returns
        -------
        int
            The sub_port number used by the current connection
        """
        return self._cfg["subPort"]

    @sub_port.setter
    def sub_port(self, val: int):
        self._cfg["subPort"] = val



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
            f"{self.connection_uuid}._DashZMQ._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip)],
            port=pub_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.update_service(zconf_info)

    def add_device(self, device):
        """Add a device to the connection

        Parameters
        ----------
        device : Device
            The device to add to the connection
        """
        device._add_connection(self)
        self.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=device.zmq_connection_uuid))
        if device.device_id not in self.device_id_list:
            self.device_id_list.append(device.device_id)
            self._zconf_publish_tcp(self.local_ip, self.local_port)

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

        self.device_id_list = []
        self.connection_uuid = shortuuid.uuid()
        self.b_connection_id = self.connection_uuid.encode('utf-8')

        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"

        self.local_ip = ip.get_local_ip_address()
        self.connection_control = ZMQControl(zmq_out_url, pub_port, sub_port)
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self._zconf_publish_zmq(sub_port, pub_port)
        self.start()

    def run(self):

        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_uuid))

        #  Subscribe on ALL, and my connection
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DVCE_CNCT")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DVCE_DCNCT")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_uuid)
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
                tx_zmq_pub.send_multipart([self.b_connection_id, b'', message])

            if self.rx_zmq_sub in socks:
                [address, _, data] = self.rx_zmq_sub.recv_multipart()
                if address in (b'ALL', self.b_connection_id):
                    logging.debug("ZMQ Tx: %s", data.decode('utf-8').rstrip())
                    ext_tx_zmq_pub.send(data)

        tx_zmq_pub.close()
        self.rx_zmq_sub.close()
