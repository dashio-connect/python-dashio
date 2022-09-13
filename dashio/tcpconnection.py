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
import json
import logging
import socket
import threading
import time

import shortuuid
import zmq
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from . import ip
from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL


class TCP():
    """A CFG control class to store TCP connection information
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
        """Returns the CFG string for this TCP control

        Returns
        -------
        str
            The CFG string for this control
        """
        try:
            num_columns = data[3]
            dashboard_id = data[2]
        except IndexError:
            return
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, ip_address="", port=5650):
        self._cfg = {}
        self.cntrl_type = "TCP"
        self.control_id = control_id
        self.ip_address = ip_address
        self.port = port

    @property
    def ip_address(self) -> str:
        """IP address of current connection

        Returns
        -------
        str
            IP address
        """
        return self._cfg["ipAddress"]

    @ip_address.setter
    def ip_address(self, val: str):
        self._cfg["ipAddress"] = val

    @property
    def port(self) -> int:
        """The port of the current connection

        Returns
        -------
        int
            The port number used by the current connection
        """
        return self._cfg["port"]

    @port.setter
    def port(self, val: int):
        self._cfg["port"] = val


class TCPConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

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
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        device.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.connection_id))
        device.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self.b_connection_id)
        device.add_control(self.tcp_control)

        self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_pub_id))
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)

    @staticmethod
    def _is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_s:
            return port_s.connect_ex(('localhost', port)) == 0

    def __init__(self, ip_address="*", port=5650, use_zero_conf=True, context=None):
        """TCP Connection

        Parameters
        ---------
            ip_address : str, optional
                IP Address to use. Defaults to "*".
            port : int, optional
                Port to use. Defaults to 5650.
            use_zero_conf : bool, optional
                Use mDNS to advertise the connection. Defaults to True.
            context : optional
                ZMQ context. Defaults to None.
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.connection_id = shortuuid.uuid()
        self.b_connection_id = self.connection_id.encode('utf-8')
        self.use_zeroconf = use_zero_conf
        while self._is_port_in_use(port) and use_zero_conf:
            # increment port until we find one that is free.
            port += 1
        self.ext_url = "tcp://" + ip_address + ":" + str(port)

        self.socket_ids = []
        self.running = True

        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"
        self.local_ip = ip.get_local_ip_address()
        if self.use_zeroconf:
            self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            self._zconf_publish_tcp(port)
        
        self.tcp_control = TCP(self.connection_id, self.local_ip, port)
        self.start()
        time.sleep(1)

    def close(self):
        """Close the connection."""

        if self.use_zeroconf:
            self.zeroconf.unregister_all_services()
            self.zeroconf.close()
        self.running = False

    def run(self):
        tcpsocket = self.context.socket(zmq.STREAM)

        def _zmq_tcp_send(tcp_id, data):
            try:
                tcpsocket.send(tcp_id, zmq.SNDMORE)
                tcpsocket.send(data, zmq.NOBLOCK)
            except zmq.error.ZMQError as zmq_e:
                logging.debug("Sending TX Error: %s", zmq_e)
                # self.socket_ids.remove(tcp_id)

        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALARM")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_id)
        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")

        tcpsocket.bind(self.ext_url)
        tcpsocket.set(zmq.SNDTIMEO, 5)

        poller = zmq.Poller()
        poller.register(tcpsocket, zmq.POLLIN)
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        tcp_id = tcpsocket.recv()
        tcpsocket.recv()  # empty data here

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break

            if tcpsocket in socks:
                tcp_id = tcpsocket.recv()
                message = tcpsocket.recv()
                if tcp_id not in self.socket_ids:
                    logging.debug("Added Socket ID: %s", tcp_id.hex())
                    self.socket_ids.append(tcp_id)
                logging.debug("TCP ID: %s, Rx:\n%s", tcp_id.hex(), message.decode('utf-8').rstrip())
                if message:
                    tx_zmq_pub.send_multipart([self.b_connection_id, tcp_id, message])
                else:
                    if tcp_id in self.socket_ids:
                        logging.debug("Removed Socket ID: %s", tcp_id.hex())
                        self.socket_ids.remove(tcp_id)
            if self.rx_zmq_sub in socks:
                try:
                    [address, msg_id, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    # If there aren't three parts continue.
                    continue
                if not data:
                    continue
                if address == b'ALL':
                    for tcp_id in self.socket_ids:
                        logging.debug("TCP ID: %s, Tx:\n%s", tcp_id.hex(), data.decode('utf-8').rstrip())
                        _zmq_tcp_send(tcp_id, data)
                elif address == self.b_connection_id:
                    logging.debug("TCP ID: %s, Tx:\n%s", msg_id.hex(), data.decode('utf-8').rstrip())
                    _zmq_tcp_send(msg_id, data)

        for tcp_id in self.socket_ids:
            _zmq_tcp_send(tcp_id, b'')

        tcpsocket.close()
        tx_zmq_pub.close()
        self.rx_zmq_sub.close()
