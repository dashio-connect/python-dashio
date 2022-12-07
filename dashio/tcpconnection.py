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
from zeroconf import IPVersion, ServiceInfo, Zeroconf, ServiceBrowser

from . import ip
from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL
from .device import Device

class TCPControl():
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
            dashboard_id = data[2]
        except IndexError:
            return ""
        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def get_cfg64(self, data) -> dict:
        """Returns the CFG dict for this TCP control

        Returns
        -------
        dict
            The CFG string for this control
        """
        return self._cfg

    def __init__(self, control_id, ip_address="", port=5650):
        self._cfg = {}
        self.cntrl_type = "TCP"
        self._cfg["controlID"] = control_id
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


class ZeroConfDashTCPListener:
    def __init__(self, context):
        self.context = context
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.connect("inproc://zconf")

    def remove_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if service_type ==  "_DashIO._tcp.local.":
            msg = {
                'objectType': 'zeroConfDisconnect',
                'connectionID': name.split("_", 1)[0]
            }
            self.zmq_socket.send(json.dumps(msg).encode())

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            for address in info.addresses:
                msg = {
                    'objectType': 'zeroConfAdd',
                    'address': socket.inet_ntoa(address),
                    'deviceID': info.properties[b'deviceID'].decode(),
                    'connectionID': name.split("_", 1)[0],
                    'port': str(info.port)
                }
                self.zmq_socket.send(json.dumps(msg).encode())

    def update_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            for address in info.addresses:
                msg = {
                    'objectType': 'zeroConfUpdate',
                    'address': socket.inet_ntoa(address),
                    'deviceID': info.properties[b'deviceID'].decode(),
                    'connectionID': name.split("_", 1)[0],
                    'port': str(info.port)
                }
                self.zmq_socket.send(json.dumps(msg).encode())


class TCPConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def _zconf_start_zmq(self):
        # give a little time for ZMQ to start up.
        self.browser = ServiceBrowser(self.zeroconf, "_DashIO._tcp.local.", self.listener)
        zconf_desc = {
            'connectionUUID': self.connection_id,
            'deviceID': ','.join(self.device_id_list)
        }
        zconf_info = ServiceInfo(
            "_DashIO._tcp.local.",
            f"{self.connection_id}._DashIO._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.local_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.update_service(zconf_info)

    def _zconf_update_zmq(self):
        zconf_desc = {
            'connectionUUID': self.connection_id,
            'deviceID': ','.join(self.device_id_list)
        }
        zconf_info = ServiceInfo(
            "_DashIO._tcp.local.",
            f"{self.connection_id}._DashIO._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.local_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.update_service(zconf_info)


    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        device._add_connection(self)
        self.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=device.zmq_pub_id))
        if device.device_id not in self.device_id_list:
            self.device_id_list.append(device.device_id)
            self._zconf_update_zmq()
        #self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, device.zmq_pub_id)

    @staticmethod
    def _is_port_in_use(ip_address, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_s:
            return port_s.connect_ex((ip_address, port)) == 0

    def __init__(self, ip_address="*", port=5650, use_zero_conf=True, context: zmq.Context=None):
        """TCP Connection

        Parameters
        ---------
            ip_address : str, optional
                IP Address to use. Defaults to "*" - forces The TCP connection to find the ip address attached to the local network.
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
        if ip_address == "*":
            self.local_ip = ip.get_local_ip_address()
        else:
            self.local_ip = ip_address
        self.local_port = port
        while self._is_port_in_use(self.local_ip, self.local_port) and use_zero_conf:
            # increment port until we find one that is free.
            self.local_port += 1
        self.ext_url = "tcp://" + self.local_ip + ":" + str(self.local_port)
        self.socket_ids = []
        self.device_id_list = []
        self.remote_connection_dict = {}
        self.remote_device_con_dict = {}
        self.remote_device_id_list = []
        self.running = True

        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"
        if self.use_zeroconf:
            self.zeroconf = Zeroconf()
            self.listener = ZeroConfDashTCPListener(self.context)

        self.connection_control = TCPControl(self.connection_id, self.local_ip, self.local_port)
        self.start()
        time.sleep(1)

    def close(self):
        """Close the connection."""

        if self.use_zeroconf:
            self.zeroconf.remove_all_service_listeners()
            self.zeroconf.unregister_all_services()
            time.sleep(1.0)
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
            except OSError as exc:
                logging.debug("Socket assignment error: %s", exc)

        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.connection_id))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DVCE_CNCT")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DVCE_DCNCT")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.connection_id)
        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")

        tcpsocket.bind(self.ext_url)
        tcpsocket.set(zmq.SNDTIMEO, 5)

        rx_zconf_pull = self.context.socket(zmq.PULL)
        rx_zconf_pull.bind("inproc://zconf")

        poller = zmq.Poller()
        poller.register(tcpsocket, zmq.POLLIN)
        poller.register(self.rx_zmq_sub, zmq.POLLIN)
        poller.register(rx_zconf_pull, zmq.POLLIN)
        threading.Thread(target=self._zconf_start_zmq).start()
            
        tcp_id = tcpsocket.recv()
        tcpsocket.recv()  # empty data here
        added = False
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
            if rx_zconf_pull in socks:
                message = rx_zconf_pull.recv()
                logging.debug("ZCONF Rx: %s", message)
                msg = json.loads(message)
                if msg['objectType'] in ['zeroConfAdd', 'zeroConfUpdate']:
                    device_list = msg['deviceID'].split(',')
                    for device_id in device_list:
                        if len(device_id) > 0 and (device_id not in self.device_id_list) and (device_id not in self.remote_device_id_list):
                            self.remote_device_id_list.append(device_id)
                            added = True
                        else:
                            added = False
                    if added:
                        self.remote_connection_dict[msg['connectionID']] = device_list
                        self.remote_device_con_dict[msg['connectionID']] = msg
                        added = False
                elif msg['objectType'] == 'remove':
                    for device_id in self.remote_connection_dict[msg['connectionID']]:
                        if device_id in self.remote_device_id_list:
                            self.remote_device_id_list.remove(device_id)
                    del self.remote_connection_dict[msg['connectionID']]
                    del self.remote_device_con_dict[msg['connectionID']]
                logging.debug("DeviceID List: %s", self.remote_device_id_list)
                logging.debug("ConnectionID Dict: %s", self.remote_device_con_dict)
        for tcp_id in self.socket_ids:
            _zmq_tcp_send(tcp_id, b'')

        tcpsocket.close()
        tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        rx_zconf_pull.close()
