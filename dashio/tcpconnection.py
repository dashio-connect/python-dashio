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

from . import ip
from .constants import CONNECTION_PUB_URL
from .device import Device
from .zeroconf_service import ZeroconfService

class TCPConnection(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def _send_announce(self):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid
        }
        # logging.debug("TCP SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])


    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        if device.device_id not in self.local_device_id_list:
            device.register_connection(self)
            self.local_device_id_list.append(device.device_id)
            self.z_conf.add_device(device.device_id)

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
        self.zmq_connection_uuid = "TCP:" + shortuuid.uuid()
        self.b_zmq_connection_uuid = self.zmq_connection_uuid.encode('utf-8')
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
        self.local_device_id_list = []
        self.remote_connection_dict = {}
        self.remote_device_con_dict = {}
        self.remote_device_id_msg_dict = {}
        self._device_id_action_station_list = []

        self.tcp_id_2_ip_dict = {}
        self.tcp_ip_2_id_dict = {}

        self.running = True

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        if self.use_zeroconf:
            self.z_conf = ZeroconfService(self.zmq_connection_uuid, self.local_ip, self.local_port, self.context)

        self.start()

    def close(self):
        """Close the connection."""

        if self.use_zeroconf:
            self.z_conf.close()
        self.running = False

    def _connect_remote_device(self, msg: dict):
        """Connect to remote device"""
        ip_address = msg['address']
        port = msg['port']
        url = f"tcp://{ip_address}:{port}"
        self.tcpsocket.connect(url)
        socket_id = self.tcpsocket.getsockopt(zmq.IDENTITY)
        ip_b = ip_address + ':' + port
        if ip_b not in self.tcp_ip_2_id_dict:
            try:
                logging.debug("Sending WHO to ID: %s", socket_id.hex())
                self.tcpsocket.send(socket_id, zmq.SNDMORE)
                self.tcpsocket.send_string('\tWHO\n')
                self.tcp_id_2_ip_dict[socket_id] = ip_address + ':' + port
                self.tcp_ip_2_id_dict[ip_address + ':' + port] = socket_id
            except zmq.error.ZMQError:
                logging.debug("Sending TX Error.")
                self.tcpsocket.send(b'')
        time.sleep(0.1)
        if socket_id not in self.socket_ids:
            logging.debug("Added Socket ID: %s", socket_id.hex())
            self.socket_ids.append(socket_id)
        return socket_id

    def _disconnect_remote_device(self, msg: dict):
        ip_key = msg['address'] + ':' + msg['port']
        if ip_key in self.tcp_ip_2_id_dict:
            self.tcpsocket.send(self.tcp_ip_2_id_dict[ip_key], zmq.SNDMORE)
            self.tcpsocket.send(b'', zmq.NOBLOCK)
            del self.tcp_ip_2_id_dict[ip_key]

    def _send_remote_device(self, r_device_id, msg):
        if r_device_id in self.remote_device_id_msg_dict:
            remote = self.remote_device_id_msg_dict[r_device_id]
            ip_address = remote['address']
            port = remote['port']
            url = f"tcp://{ip_address}:{port}"
            self.tcpsocket.connect(url)
            socket_id = self.tcpsocket.getsockopt(zmq.IDENTITY)
            self.tcpsocket.send(socket_id, zmq.SNDMORE)
            self.tcpsocket.send(msg)
            self.tcpsocket.send(socket_id, zmq.SNDMORE)
            self.tcpsocket.send(b'', zmq.NOBLOCK)

    def _service_zconf_message(self, rx_zconf_pull):
        message = rx_zconf_pull.recv()
        msg = json.loads(message)
        should_connect = False
        if msg['objectType'] in ['zeroConfAdd', 'zeroConfUpdate']:
            device_list = msg['deviceID'].split(',')
            for device_id in device_list:
                if len(device_id) > 0 and (device_id not in self.local_device_id_list) and (device_id not in self.remote_device_id_msg_dict):
                    self.remote_device_id_msg_dict[device_id] = msg
                    added = True
                    if device_id in self._device_id_action_station_list:
                        should_connect = True
                else:
                    added = False
            if added:
                self.remote_connection_dict[msg['connectionID']] = device_list
                self.remote_device_con_dict[msg['connectionID']] = msg
                added = False
                if should_connect:
                    self._connect_remote_device(msg)
                    should_connect = False
        elif msg['objectType'] == 'zeroConfDisconnect':
            try:
                for device_id in self.remote_connection_dict[msg['connectionID']]:
                    if device_id in self.remote_device_id_msg_dict:
                        self._disconnect_remote_device(self.remote_device_id_msg_dict[device_id])
                        del self.remote_device_id_msg_dict[device_id]
            except KeyError:
                return
            del self.remote_connection_dict[msg['connectionID']]
            del self.remote_device_con_dict[msg['connectionID']]

    def _add_device_rx(self, msg_dict):
        """Connect to another device"""
        device_id = msg_dict["deviceID"]
        logging.debug("TCP DEVICE CONNECT: %s", device_id)
        if device_id not in self._device_id_action_station_list:
            self._device_id_action_station_list.append(device_id)
        if device_id in self.remote_device_id_msg_dict:
            self._connect_remote_device(self.remote_device_id_msg_dict[device_id])
        logging.debug("device_ids to connect too: %s", self._device_id_action_station_list)

    def _del_device_rx(self, msg_dict):
        device_id = msg_dict["deviceID"]
        if device_id in self._device_id_action_station_list:
            logging.debug("TCP DEVICE_DISCONNECT: %s", device_id)
            if device_id in self.remote_device_id_msg_dict:
                self._disconnect_remote_device(self.remote_device_id_msg_dict[device_id])
            self._device_id_action_station_list.remove(device_id)
        logging.debug("device_ids to connect too: %s", self._device_id_action_station_list)

    def _tcp_command(self, msg_dict: dict):
        logging.debug("TCP CMD: %s", msg_dict)
        if msg_dict['msgType'] == 'connect':
            self._add_device_rx(msg_dict)
        if msg_dict['msgType'] == 'disconnect':
            self._del_device_rx(msg_dict)

    def _service_device_messaging(self):

        def _zmq_tcp_send(tcp_id, data: bytearray):
            logging.debug("TCP TX:\n%s", data.decode().rstrip())
            try:
                self.tcpsocket.send(tcp_id, zmq.SNDMORE)
                self.tcpsocket.send(data, zmq.NOBLOCK)
            except zmq.error.ZMQError as zmq_e:
                logging.debug("Sending TX Error: %s", zmq_e)
                #self.socket_ids.remove(tcp_id)
            except OSError as exc:
                logging.debug("Socket assignment error: %s", exc)

        try:
            [msg_to, data] = self.rx_zmq_sub.recv_multipart()
        except ValueError:
            logging.debug("TCP value error")
            return
        if not data:
            logging.debug("TCP no data error")
            return
        if msg_to == b'ALL':
            for tcp_id in self.socket_ids:
                _zmq_tcp_send(tcp_id, data)
        elif msg_to == b'COMMAND':
            self._tcp_command(json.loads(data))
            return
        else:
            dest = msg_to.split(b':')[-1]
            if dest in self.socket_ids:
                _zmq_tcp_send(dest, data)
            if dest in self.remote_device_id_msg_dict:
                self._send_remote_device(dest, data)

    def _service_tcp_messages(self, tx_zmq_pub):
        tcp_id = self.tcpsocket.recv()
        message = self.tcpsocket.recv()
        if tcp_id not in self.socket_ids and tcp_id not in self.tcp_id_2_ip_dict:
            logging.debug("Added Socket ID: %s", tcp_id.hex())
            self.socket_ids.append(tcp_id)
        if message:
            logging.debug("TCP RX: %s\n%s",tcp_id.hex(), message.decode().rstrip())
            msg_from = self.b_zmq_connection_uuid + b":" + tcp_id
            tx_zmq_pub.send_multipart([message, msg_from])
        else:
            if tcp_id in self.socket_ids:
                logging.debug("Removed Socket ID: %s", tcp_id.hex())
                self.socket_ids.remove(tcp_id)

    def run(self):
        self.tcpsocket = self.context.socket(zmq.STREAM)

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, COMMAND, and my zmq_connection_uuid
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "COMMAND")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "TCP")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)

        self.tcpsocket.bind(self.ext_url)
        self.tcpsocket.set(zmq.SNDTIMEO, 5)

        rx_zconf_pull = self.context.socket(zmq.PULL)
        rx_zconf_pull.bind("inproc://zconf")

        poller = zmq.Poller()
        poller.register(self.tcpsocket, zmq.POLLIN)
        poller.register(self.rx_zmq_sub, zmq.POLLIN)
        poller.register(rx_zconf_pull, zmq.POLLIN)

        self._send_announce()

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.tcpsocket in socks:
                self._service_tcp_messages(self.tx_zmq_pub)
            if self.rx_zmq_sub in socks:
                self._service_device_messaging()
            if rx_zconf_pull in socks:
                self._service_zconf_message(rx_zconf_pull)

        for tcp_id in self.socket_ids:
            self.tcpsocket.send(tcp_id, zmq.SNDMORE)
            self.tcpsocket.send(b'', zmq.NOBLOCK)

        self.tcpsocket.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        rx_zconf_pull.close()
