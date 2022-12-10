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
import socket
import threading
import shortuuid
import zmq
import time
import logging
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf


class ZeroConfDashTCPListener:
    """A zeroc conf listener"""
    def __init__(self, service_type: str, connection_uuid: str, context: zmq.Context):
        self.context = context
        self.service_type = service_type
        self.connection_uuid = connection_uuid
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.connect("inproc://zconf")

    def _send_msg(self, msg: dict):
        """Send a message"""
        logging.debug("ZCONF: %s", json.dumps(msg))
        self.zmq_socket.send(json.dumps(msg).encode())

    def _send_info(self, connection_uuid, info):
        try:
            device_ids = info.properties[b'deviceID'].decode()
        except KeyError:
            device_ids = ''
        for address in info.addresses:
            msg = {
                'objectType': 'zeroConfUpdate',
                'address': socket.inet_ntoa(address),
                'deviceID': device_ids,
                'connectionID': connection_uuid,
                'port': str(info.port)
            }
            self._send_msg(msg)

    def remove_service(self, zeroconf, service_type, name):
        """Remove service"""
        connection_uuid  = name.split("._", 1)[0]
        if service_type == self.service_type and connection_uuid != self.connection_uuid:
            msg = {
                'objectType': 'zeroConfDisconnect',
                'connectionID': connection_uuid
            }
            self._send_msg(msg)

    def add_service(self, zeroconf, service_type, name):
        """add service"""
        connection_uuid  =name.split(".", 1)[0]
        if service_type == self.service_type and connection_uuid != self.connection_uuid:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                self._send_info(connection_uuid, info)

    def update_service(self, zeroconf, service_type, name):
        """update service"""
        connection_uuid  =name.split(".", 1)[0]
        if service_type == self.service_type and connection_uuid != self.connection_uuid:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                self._send_info(connection_uuid, info)


class ZeroconfService(threading.Thread):


    def _get_ext_ip_address(self):
        """Find the external IP address."""
        test_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            test_s.connect(('10.255.255.255', 1))
            i_address = test_s.getsockname()[0]
        except socket.error:
            i_address = '127.0.0.1'
        finally:
            test_s.close()
        return i_address


    def _zconf_update_zmq(self):
        zconf_desc = {
            'connectionUUID': self.connection_uuid,
            'deviceID': ','.join(self.device_id_list)
        }
        zconf_info = ServiceInfo(
            self.fully_qualified_name,
            f"{self.connection_uuid}._DashIO._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip_address)],
            port=self.local_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.update_service(zconf_info)

    def add_device(self, device_id):
        """Add a device_id to the advertiser"""
        if device_id not in self.device_id_list:
            self.device_id_list.append(device_id)
            self._zconf_update_zmq()

    def remove_device_id(self, device_id):
        """Remove a device_id from the advertiser"""
        if device_id in self.device_id_list:
            self.device_id_list.remove(device_id)
            self._zconf_update_zmq()

    def close(self):
        self.zeroconf.remove_all_service_listeners()
        self.zeroconf.unregister_all_services()
        self.zeroconf.close()

    def __init__(self, connection_uuid: str, ip_address: str, port: int, context=None):
        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.connection_uuid = connection_uuid
        self.fully_qualified_name = "_DashIO._tcp.local."
        host_name = socket.gethostname()
        host_list = host_name.split(".")
        # rename for .local mDNS advertising
        self.host_name = f"{host_list[0]}.local"
        self.local_ip_address = ip_address
        self.local_port = port
        self.zeroconf = Zeroconf()
        self.listener = ZeroConfDashTCPListener(self.fully_qualified_name, self.connection_uuid, self.context)
        self.device_id_list = []
        self.start()

    def run(self):
        self.browser = ServiceBrowser(self.zeroconf, self.fully_qualified_name, self.listener)
        zconf_desc = {
            'connectionUUID': self.connection_uuid,
            'deviceID': ','.join(self.device_id_list)
        }
        zconf_info = ServiceInfo(
            self.fully_qualified_name,
            f"{self.connection_uuid}._DashIO._tcp.local.",
            addresses=[socket.inet_aton(self.local_ip_address)],
            port=self.local_port,
            properties=zconf_desc,
            server=self.host_name + ".",
        )
        self.zeroconf.update_service(zconf_info)
