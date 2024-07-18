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

from __future__ import annotations
import logging
import threading
import time
import json
import shortuuid
import zmq
import serial
from serial.serialutil import SerialException
from .constants import CONNECTION_PUB_URL
from .device import Device
from .iotcontrol.enums import ConnectionState

logger = logging.getLogger(__name__)

SERIAL_TX_URL = "inproc://DASHIO_CM_PUSH_PULL_{id}"


class DashIOCommsModuleConnection(threading.Thread):
    """Under Development! - Setups and manages a connection thread to iotdashboard via a DashIO Serial Comms Module."""

    def set_comms_module_passthough(self):
        """Set the comms module to passthrough."""
        if self._conn_state != ConnectionState.DISCONNECTED:
            message = f"\t{self._dcm_device_id}\tCTRL\tINIT\tPSTH\n"
            self._dcm_tx(message)

    def set_comms_module_normal(self) -> str:
        """Set the comms module to normal mode."""
        message = f"\t{self._dcm_device_id}\tCTRL\tINIT\tNML\n"
        return message

    def enable_comms_module_ble(self, enable: bool, timeout=None):
        """Enable/disable comms module BLE. If enabled with timeout the BLE will be enabled for the timeout given.
        Timeout values:
            * 0 = Button control no time out.
            * n > 0 = Turned off with timeout set to n rounded up to minimum 30 seconds, with button control."""
        if self._conn_state == ConnectionState.CONNECTED:
            if not enable:
                message = f"\t{self._dcm_device_id}\tCTRL\tBLE\tHLT\n"
                self._dcm_tx(message)
                return
            if timeout is not None:
                message = f"\t{self._dcm_device_id}\tCTRL\tBLE\t{timeout}\n"
            else:
                message = f"\t{self._dcm_device_id}\tCTRL\tBLE\n"
            self._dcm_tx(message)

    def enable_comms_module_tcp(self, enable: bool):
        """Enable/disable comms module TCP."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tCTRL\tTCP"
            if not enable:
                message += "\tHLT"
            message += '\n'
            self._dcm_tx(message)

    def enable_comms_module_dash(self, enable: bool):
        """Enable/Disable comms module DASH."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tCTRL\tMQTT"
            if not enable:
                message += "\tHLT"
            message += '\n'
            self._dcm_tx(message)

    def provision_comms_module_dash(self, user_name: str, password: str):
        """Provision username and password for comms module DASH connection."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tPROV\tDASHIO\t{user_name}\t{password}\n"
            message += '\n'
            self._dcm_tx(message)

    def provision_comms_module_tcp_port(self, port: int):
        """Provision the comms module TCP port."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tPROV\tTCP\t{port}\n"
            self._dcm_tx(message)

    def provision_comms_module_name(self, name: str):
        """Provision the comms module NAME."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tPROV\tNAME\t{name}\n"
            self._dcm_tx(message)

    def provision_comms_module_wifi(self, country_code: str, ssid: str, password: str):
        """Provision the comms module wifi country code, ssid, and password."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tPROV\tWIFI\t{ssid}\t{password}\t{country_code}\n"
            self._dcm_tx(message)

    def provision_save_to_flash(self):
        """Save Provision info to flash."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\\PROV\tSAVE\n"
            self._dcm_tx(message)

    def get_comms_module_active_connections(self):
        """Get the active connections from the comms module."""
        if self._conn_state == ConnectionState.CONNECTED:
            message = f"\t{self._dcm_device_id}\tCTRL\tCNCTN\n"
            self._dcm_tx(message)

    def _subscribe_comms_module_mqtt(self, device_id: str, device_type: str, device_name: str):
        if self._conn_state == ConnectionState.CONNECTED and self._dash_connected:
            message = f"\t{self._dcm_device_id}\tCTRL\tSUB\t{device_id}\t{device_type}\t{device_name}\n"
            self._dcm_tx(message)

    def reguest_comms_module_device_id(self):
        """Request the comms module DeviceID."""
        message = "\tCTRL\n"
        self._dcm_tx(message)

    def reboot_comms_module(self):
        """Request the comms module to reset."""
        self._conn_state = ConnectionState.CONNECTING
        message = f"\t{self._dcm_device_id}\tCTRL\tREBOOT\n"
        self._dcm_tx(message)

    def comms_module_sleep(self):
        """Request the comms module to go to sleep."""
        message = f"\t{self._dcm_device_id}\tCTRL\tSLEEP\n"
        self._dcm_tx(message)

    def _send_dash_announce(self, device_id: str):
        msg = {
            'msgType': 'send_announce',
            'connectionUUID': self.zmq_connection_uuid,
            'deviceID': device_id
        }
        logger.debug("DASH SEND ANNOUNCE: %s", msg)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg).encode()])

    def add_device(self, device: Device):
        """Add a device to the connection

        Parameters
        ----------
        device : dashio.Device
            Add a device to the connection.
        """
        if device.device_id not in self._device_id_list:
            device.register_connection(self)
            self._device_id_list.append(device.device_id)

            if self._conn_state == ConnectionState.CONNECTED and self._dash_username:
                self._send_dash_announce(device.device_id)

    def _dcm_crtl_reboot(self, msg):
        self._conn_state = ConnectionState.DISCONNECTED
        self.reguest_comms_module_device_id()
        self._conn_state = ConnectionState.CONNECTING

        if self._crtl_reboot_callback:
            self._crtl_reboot_callback(msg)

    def set_crtl_reboot_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL message REBOOT.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_reboot_callback = callback

    def unset_crtl_reboot_callback(self):
        """
        Unset the reboot callback function.
        """
        self._crtl_reboot_callback = None

    def set_crtl_init_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL message INIT.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_init_callback = callback

    def unset_crtl_init_callback(self):
        """
        Unset the INIT callback function.
        """
        self._crtl_init_callback = None

    def set_crtl_sleep_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL message SLEEP.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_sleep_callback = callback

    def unset_crtl_sleep_callback(self):
        """
        Unset the sleep callback function.
        """
        self._crtl_sleep_callback = None

    def set_crtl_dash_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL message MQTT.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_dash_callback = callback

    def unset_crtl_dash_callback(self):
        """
        Unset the dash callback function.
        """
        self._crtl_dash_callback = None

    def set_crtl_wifi_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL message WIFI.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_wifi_callback = callback

    def unset_crtl_wifi_callback(self):
        """
        Unset the WIFI callback function.
        """
        self._crtl_wifi_callback = None

    def _dcm_crtl_connection_callback(self, msg):
        logger.debug("Connections: %s:", msg)
        self._ble_enabled = False
        self._tcp_enabled = False
        self._dash_enabled = False
        if 'BLE' in msg:
            self._ble_enabled = True
        if 'TCP' in msg:
            self._tcp_enabled = True
        if 'MQTT' in msg:
            self._dash_enabled = True
        if self._ble_enabled != self._enable_ble:
            self.enable_comms_module_ble(self._enable_ble, self._ble_timeout)
        if self._tcp_enabled != self._enable_tcp:
            self.enable_comms_module_tcp(self._enable_tcp)
        if self._dash_enabled != self._enable_dash:
            self.enable_comms_module_dash(self._enable_dash)
        if self._crtl_cnctn_callback:
            self._crtl_cnctn_callback(msg)

    def _dcm_crtl_ble_callback(self, msg):
        if msg[3] == 'EN':
            self._ble_enabled = True
        elif msg[3] == 'HLT':
            self._ble_enabled = False
        if self._crtl_ble_callback:
            self._crtl_ble_callback(msg)

    def _dcm_crtl_tcp_callback(self, msg):
        logger.debug("Comms Module TCP: %s", msg)
        if msg[3] == 'EN':
            self._tcp_enabled = True
        elif msg[3] == 'HLT':
            self._tcp_enabled = False
        if self._crtl_tcp_callback:
            self._crtl_tcp_callback(msg)

    def _dashio_crtl_device_id_callback(self, msg):
        logger.debug("Comms Module Device ID: %s", msg[0])

        if self._dcm_device_id != msg[0] or self._conn_state != ConnectionState.CONNECTED:
            self._conn_state = ConnectionState.CONNECTING
            self._dcm_device_id = msg[0]
            self.set_comms_module_passthough()
        if self._crtl_device_id_callback:
            self._crtl_device_id_callback(msg)

    def _dcm_crtl_status_callback(self, msg):
        if self._crtl_status_callback:
            self._crtl_status_callback(msg)

    def _dcm_crtl_init_callback(self, msg):
        if self._conn_state == ConnectionState.CONNECTING:
            if msg[3] == 'PSTH':
                self._conn_state = ConnectionState.CONNECTED
                self.get_comms_module_active_connections()
        if self._crtl_init_callback:
            self._crtl_init_callback(msg)

    def _dcm_crtl_sleep_callback(self, msg):
        if self._crtl_sleep_callback:
            self._crtl_sleep_callback(msg)

    def _dcm_crtl_dash_callback(self, msg):
        logger.debug("Comms Module MQTT: %s", msg)
        if msg[3] == 'EN':
            self._dash_enabled = True
            self._dash_connected = False
        elif msg[3] == 'HLT':
            self._dash_enabled = False
            self._dash_connected = False
        elif msg[3] == 'CON':
            self._dash_connected = True
            for device_id in self._device_id_list:
                logger.debug("SUB: %s", device_id)
                self._send_dash_announce(device_id)
        if self._crtl_dash_callback:
            self._crtl_dash_callback(msg)

    def _dcm_crtl_wifi_callback(self, msg):
        logger.debug("Comms Module WIFI: %s", msg)
        if msg[3] == 'EN':
            self._wifi_connected = False
        elif msg[3] == 'HLT':
            self._wifi_connected = False
            self._dash_connected = False
        elif msg[3] == 'CON':
            self._wifi_connected = True

        if self._crtl_wifi_callback:
            self._crtl_wifi_callback(msg)

    def set_crtl_ble_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL BLE message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_ble_callback = callback

    def unset_crtl_ble_callback(self):
        """
        Unset BLE callback function.
        """
        self._crtl_ble_callback = None

    def set_crtl_tcp_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL BLE message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_tcp_callback = callback

    def unset_crtl_tcp_callback(self):
        """
        Unset TCP callback function.
        """
        self._crtl_tcp_callback = None

    def set_crtl_status_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL STS message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_status_callback = callback

    def unset_crtl_status_callback(self):
        """
        Unset status callback function.
        """
        self._crtl_status_callback = None

    def set_crtl_connection_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL CTCTN message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_cnctn_callback = callback

    def set_crtl_device_id_callback(self, callback):
        """
        Specify a callback function to be called when DashIO Comms module sends CRTL CTCTN message.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the DashIO comms module.
        """
        self._crtl_device_id_callback = callback

    def unset_crtl_connection_callback(self):
        """
        Unset connection callback function.
        """
        self._crtl_cnctn_callback = None

    def _init_serial(self):
        try:
            self.serial_com = serial.Serial(self.serial_port, self.baud_rate, timeout=1.0)
            self.serial_com.flush()
        except SerialException as e:
            logger.debug("Serial Err: %s", str(e))

    @property
    def enable_tcp(self) -> bool:
        """enable_tcp

        Returns
        -------
        bool
            If TCP should be enabled
        """
        return self._enable_tcp

    @enable_tcp.setter
    def enable_tcp(self, val: bool):
        if val != self._enable_tcp:
            self._enable_tcp = val
            self.enable_comms_module_tcp(self._enable_tcp)

    @property
    def enable_ble(self) -> bool:
        """enable_ble

        Returns
        -------
        bool
            If BLE should be enabled
        """
        return self._enable_ble

    @enable_ble.setter
    def enable_ble(self, val: bool):
        if val != self._enable_ble:
            self._enable_ble = val
            self.enable_comms_module_tcp(self._enable_ble)

    @property
    def enable_dash(self) -> bool:
        """enable_dash

        Returns
        -------
        bool
            If DASH should be enabled
        """
        return self._enable_dash

    @enable_dash.setter
    def enable_dash(self, val: bool):
        if val != self._enable_dash:
            self._enable_dash = val
            self.enable_comms_module_tcp(self._enable_dash)

    def __init__(
        self, serial_port='/dev/ttyUSB0',
        baud_rate=115200,
        enable_tcp=False,
        enable_dash=False,
        enable_ble=False,
        ble_timeout=None,
        context: zmq.Context | None = None
    ):
        """Serial Connection

        Parameters
        ---------
            serial_port : str, optional
                Serial port to use. Defaults to "/dev/ttyUSB0".
            baud_rate : int, optional
                Baud rate to use. Defaults to 115200.
            context : optional
                ZMQ context. Defaults to None.
        """

        threading.Thread.__init__(self, daemon=True)

        self.crtl_map = {
            'REBOOT': self._dcm_crtl_reboot,
            'CNCTN': self._dcm_crtl_connection_callback,
            'TCP': self._dcm_crtl_tcp_callback,
            'BLE': self._dcm_crtl_ble_callback,
            'STS': self._dcm_crtl_status_callback,
            'INIT': self._dcm_crtl_init_callback,
            'SLEEP': self._dcm_crtl_sleep_callback,
            'MQTT': self._dcm_crtl_dash_callback,
            'WIFI': self._dcm_crtl_wifi_callback,
        }

        self.context = context or zmq.Context.instance()
        self.zmq_connection_uuid = "DCM:" + shortuuid.uuid()

        self.serial_transmitter = self.context.socket(zmq.PUSH)
        self.serial_transmitter.connect(SERIAL_TX_URL.format(id=self.zmq_connection_uuid))

        self.b_zmq_connection_uuid = self.zmq_connection_uuid.encode()
        self._conn_state = ConnectionState.DISCONNECTED

        self._dcm_device_id = ""
        self._dash_username = ""

        self._enable_tcp = enable_tcp
        self._enable_dash = enable_dash
        self._enable_ble = enable_ble
        self._ble_timeout = ble_timeout

        self._crtl_reboot_callback = None
        self._crtl_cnctn_callback = None
        self._crtl_device_id_callback = None
        self._crtl_ble_callback = None
        self._crtl_tcp_callback = None
        self._crtl_status_callback = None
        self._crtl_init_callback = None
        self._crtl_sleep_callback = None
        self._crtl_dash_callback = None
        self._crtl_wifi_callback = None

        self._ble_enabled = False
        self._dash_enabled = False
        self._tcp_enabled = False

        self._wifi_connected = False
        self._dash_connected = False

        self.running = True
        self._device_id_list = []
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self._init_serial()
        self.start()

    def _dcm_tx(self, msg: str):
        self.serial_transmitter.send_string(msg)

    def close(self):
        """Close the connection."""
        self.running = False

    def run(self):
        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "DCM")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)

        #  Socket to receive SERIAL TX messages on
        serial_receiver = self.context.socket(zmq.PULL)
        serial_receiver.bind(SERIAL_TX_URL.format(id=self.zmq_connection_uuid))

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)
        poller.register(serial_receiver, zmq.POLLIN)
        self.reguest_comms_module_device_id()
        self._conn_state = ConnectionState.CONNECTING

        while self.running:
            try:
                socks = dict(poller.poll(1))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                try:
                    [msg_to, data] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    #  If there aren't two parts continue.
                    continue
                if not data:
                    continue
                dest = msg_to.split(b':')[-1]
                if dest == b"ANNOUNCE":
                    parts = data.strip().decode().split('\t')
                    self._subscribe_comms_module_mqtt(parts[0], parts[2], parts[3])
                    continue
                lines = data.split(b'\n')
                for line in lines:
                    if line:
                        try:
                            s_data = b'\t' + dest + line + b'\n'
                            logger.debug("SERIAL Tx →\n%s", s_data.decode().rstrip())
                            self.serial_com.write(s_data)
                        except SerialException as e:
                            logger.debug("Serial Error: %s", str(e))
                            time.sleep(1.0)
                            self._init_serial()
            if serial_receiver in socks:
                msg = serial_receiver.recv_string()
                logger.debug("SERIAL Tx →\n%s", msg.rstrip())
                try:
                    self.serial_com.write(msg.encode())
                except SerialException as e:
                    logger.debug("Serial Error: %s", str(e))
                    time.sleep(1.0)
                    self._init_serial()
            try:
                if self.serial_com.in_waiting > 0:
                    message = self.serial_com.readline()
                    if message.startswith(b'\t'):
                        try:
                            logger.debug("SERIAL Rx ←\n%s", message.rstrip().decode())
                            parts = message.strip().decode().split('\t')
                            if len(parts) == 2 and parts[1] == 'CTRL':
                                self._dashio_crtl_device_id_callback(parts)
                            elif len(parts) > 2 and parts[1] == 'CTRL':
                                try:
                                    self.crtl_map[parts[2]](parts)
                                except KeyError:
                                    logger.debug("Unknown CTRL: %s", message.rstrip().decode())
                                    continue
                            msg_from = self.b_zmq_connection_uuid + b":" + parts[0].encode()
                            tx_message = '\t' + '\t'.join(parts[1:]) + '\n'
                            self.tx_zmq_pub.send_multipart([tx_message.encode(), msg_from])
                        except UnicodeDecodeError:
                            logger.debug("SERIAL DECODE ERROR Rx:\n%s", message.hex())
            except OSError as e:
                logger.debug("Serial Error: %s", str(e))
                time.sleep(1.0)
                self._init_serial()

        self.serial_com.close()
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
