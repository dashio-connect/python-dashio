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
import json
import logging
import threading
import time
import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL, BAD_CHARS
from .iotcontrol.alarm import Alarm
from .iotcontrol.device_view import DeviceView
from .iotcontrol.enums import ControlName
from .load_config import encode_cfg64
from .load_config import CONTROL_INSTANCE_DICT, CONFIG_INSTANCE_DICT


logger = logging.getLogger(__name__)


class Device(threading.Thread):
    """Dashio Device

    Attributes
    ----------
    device_type : str
        The type of device (e.g. TempSensor, GPS...).
    device_id : str
        A unique identifier for this device
    device_name : str
        The name for this device (E.g. GlassHouse, MothersZimmerFrame...)

    Methods
    -------
    add_control(iot_control) :
        Add a control to the device.

    remove_control(iot_control) :
        Remove a control from the device.

    get_control(control_type: str, control_id: str):
        returns the instance of a control loaded into the device.

    remove_control(control_type, control_id) :
        Removes the control from the device.

    is_control_loaded(iot_control) :
         Returns boolean if the control is loaded in the device.

    add_all_c64_controls(c64_dict: dict):
        Adds all controls defined in c64_dict into the device.

    set_wifi_callback(callback) :
        Set a callback function that is called when the DashIO app provides wifi provisioning information.

    unset_wifi_callback() :
        Clears the wifi callback.

    set_dashio_callback(callback) :
        Set a callback function that is called when the DashIO app provides Dash server provisioning information.

    unset_dashio_callback() :
        Clears the set Dash callback.

    set_name_callback(callback) :
        Set a callback function that is called when the DashIO app provides Name provisioning information.

    unset_name_callback() :
        Clears the set Name callback.

    set_tcp_callback(callback) :
         Set a callback function that is called when the DashIO app provides TCP provisioning information.

    unset_tcp_callback() :
        Clears the set TCP callback.

    set_mqtt_callback(callback) :
        Set a callback function that is called when the DashIO app provides MQTT provisioning information.

    unset_mqtt_callback() :
        Clears the set MQTT callback.

    request_clock() :
        Requests UTC Timestamp from the Dash Server.

    set_clock_callback(callback):
        Specify a callback function to be called when The Dash server sends clock data.

    unset_clock_callback():
        Unset the clock rx callback.

    request_ota_build_number() :
        Requests requests latest build number for over the air updates from the Dash Server

    request_ota(build_number, chunk_number) :
        Requests requests latest ota build from the Dash Server.

    set_ota_callback(callback) :
        Specify a callback function to be called when The Dash server sends ota data.
    """

    def _on_message(self, payload):
        data = str(payload, "utf-8").strip()
        command_array = data.split("\n")
        reply = ""
        for command in command_array:
            try:
                reply += self._on_command(command.strip())
            except TypeError:
                pass
        return reply

    def _on_command(self, data):
        data_array = data.split("\t")
        rx_device_id = data_array[0]
        if rx_device_id == "WHO":
            if 'cfgRev' in self._cfg:
                return self._device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\t{self._cfg['cfgRev']}\n"
            return self._device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\n"
        if rx_device_id != self.device_id:
            return ""
        try:
            ctrl_type = data_array[1]
        except KeyError:
            return ""
        if ctrl_type in self._device_commands_dict:
            return self._device_commands_dict[ctrl_type](data_array)
        try:
            reply = self.controls_dict[ctrl_type + "\t" + data_array[2]]._message_rx_event(data_array)
            if reply:
                return reply.replace("{device_id}", self.device_id)
        except (KeyError, IndexError):
            pass
        return ""

    def _make_connect(self, _):
        return self._device_id_str + "\tCONNECT\n"

    def _make_status(self, _):
        reply = f"\t{self.device_id}\tNAME\t{self._device_name}\n"
        for value in self.controls_dict.values():
            try:
                reply += value.get_state().replace("{device_id}", self.device_id)
            except (TypeError, KeyError):
                pass
        return reply

    def _make_cfg64(self, data):
        try:
            dashboard_id = data[2]
        except IndexError:
            return ""
        reply = self._device_id_str + f"\tCFG\t{dashboard_id}\tC64\t"
        cfg = {}
        cfg["CFG"] = self._cfg
        for control in self.controls_dict.values():
            if control.ctrl_type == "ALM":
                continue
            if control.ctrl_type in ("BLE"):
                cfg[control.ctrl_type] = control.get_cfg64(data)
                continue
            if control.ctrl_type not in cfg:
                cfg[control.ctrl_type] = []
            cfg[control.ctrl_type].extend(control.get_cfg64(data))
        c64_json = encode_cfg64(cfg)
        reply += c64_json + "\n"
        return reply

    def _server_clk(self, data):
        if self._clk_rx_callback is not None:
            self._clk_rx_callback(data)

    def _server_ota(self, data):
        if self._ota_rx_callback is not None:
            self._ota_rx_callback(data)

    def _make_cfg(self, data):
        try:
            dashboard_id = data[2]
            #  no_views = data[3]
        except IndexError:
            return ""
        reply = self._device_id_str + f"\tCFG\t{dashboard_id}\tDVCE\t{json.dumps(self._cfg)}\n"
        dvvw_str = ""
        for control in self.controls_dict.values():
            if control.ctrl_type == "ALM":
                continue
            if control.ctrl_type == "DVVW":
                cfg_list = control.get_cfg(data)
                for cfg in cfg_list:
                    dvvw_str += self._device_id_str + cfg
            else:
                cfg_list = control.get_cfg(data)
                for cfg in cfg_list:
                    reply += self._device_id_str + cfg
        reply += dvvw_str
        return reply

    def _send_alarm(self, alarm_id, message_header, message_body):
        payload = self._device_id_str + f"\tALM\t{alarm_id}\t{message_header}\t{message_body}\n"
        logger.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALL", payload.encode('utf-8')])

    def _send_data(self, data: str):
        if not data:
            return
        reply_send = ""
        if isinstance(data, str):
            reply_send = data.replace("{device_id}", self.device_id)
        elif isinstance(data, list):
            reply_send = "\t" + "\t".join(data) + "\n"
        try:
            self.tx_zmq_pub.send_multipart([b"ALL", reply_send.encode('utf-8')])
        except zmq.error.ZMQError:
            pass

    def storage_enable(self, control_type: ControlName, control_id: str) -> None:
        """Turn On Dash Server Storage for the Event Log, Map, or Time Graph control."""
        key = f"{control_type.value}\t{control_id}"
        if key not in self.controls_dict:
            return
        if control_type not in [ControlName.LOG, ControlName.MAP, ControlName.TGRPH]:
            return
        payload = self._device_id_str + f"\tSTE\t{control_type.value}\t{control_id}\n"
        logger.debug("STORAGE ENABLE: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def _send_announce(self):
        payload = self._device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def request_clock(self):
        """Requests UTC Timestamp from the Dash Server
        """
        payload = self._device_id_str + "\tCLK\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def request_ota_build_number(self):
        """Requests requests latest build number for over the air updates from the Dash Server
        """
        payload = self._device_id_str + f"\tOTA\t{self.device_type}\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def request_ota(self, build_number, chunk_number):
        """Requests requests latest ota build from the Dash Server
        """
        payload = self._device_id_str + f"\tOTA\t{self.device_type}\t{build_number}\t{chunk_number}\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def is_control_loaded(self, control_type, control_id: str) -> bool:
        """Is the control loaded in the device?"""
        key = f"{control_type}\t{control_id}"
        return key in self.controls_dict

    def add_all_c64_controls(self, c64_dict: dict, column_no=1):
        """Loads all the controls in cfg_dict into the device.

        Parameters
        ----------
        c64_dict : Dict
            dictionary of the CFG loaded by decode_cfg from a CFG64 or json
        column_no: Int From 1 to 3 (default 1).
            The DashIO app reports the size of the screen in no of columns. You can load a separate
            config for each reported column number.
        """
        if not 1 <= column_no <= 3:
            column_no = 1
        for control_type, control_list in c64_dict.items():
            if isinstance(control_list, list):
                for control in control_list:
                    key = f"{control_type}\t{control['controlID']}"
                    if self.is_control_loaded(control_type, control['controlID']):
                        cfg = CONFIG_INSTANCE_DICT[control_type].from_dict(control)
                        self.controls_dict[key].add_config(cfg, column_no=column_no)
                    else:
                        new_control = CONTROL_INSTANCE_DICT[control_type].from_cfg_dict(control, column_no=column_no)
                        self.add_control(new_control)
            elif control_type == "CFG" and isinstance(control_list, dict):
                if 'name' in control_list['deviceSetup']:
                    self._set_device_setup("name", True)
                    self.set_name_callback(self._name_callback)

    def add_control(self, iot_control):
        """Add a control to the device.

        Parameters
        ----------
            iot_control : iotControl
        """
        try:
            if isinstance(iot_control, Alarm):
                iot_control.add_transmit_message_callback(self._send_alarm)
            else:
                iot_control.add_transmit_message_callback(self._send_data)
        except AttributeError:
            pass
        key = f"{iot_control.ctrl_type}\t{iot_control.control_id}"

        if key not in self.controls_dict:
            if isinstance(iot_control, DeviceView):
                self._cfg["numDeviceViews"] += 1
            self.controls_dict[key] = iot_control
            return True
        return False

    def get_control(self, control_type: ControlName, control_id: str):
        """Get the control instance.

        Parameters
        ----------
            control_type : ControlName
                The type of control
            control_id : str
                The controlID of the control

        Returns
        -------
            Control | None
                The requested control or None if the control isn't available.
        """
        key = f"{control_type.value}\t{control_id}"
        return self.controls_dict.get(key, None)

    def remove_control(self, iot_control):
        """Remove a control a control to the device.

        Parameters
        ----------
            iot_control : iotControl
        """
        if isinstance(iot_control, DeviceView):
            self._cfg["numDeviceViews"] -= 1
        key = f"{iot_control.ctrl_type}\t{iot_control.control_id}"
        if key in self.controls_dict:
            del self.controls_dict[key]

    def _set_device_setup(self, control_name: str, settable: bool):
        if settable:
            self._device_commands_dict[control_name.upper()] = getattr(self, '_' + control_name + '_rx_event', None)
            if control_name not in self._device_setup_list:
                self._device_setup_list.append(control_name)
        else:
            try:
                del self._device_commands_dict[control_name.upper()]
            except KeyError:
                pass
            try:
                self._device_setup_list.remove(control_name)
            except ValueError:
                pass
        self._cfg["deviceSetup"] = ','.join(self._device_setup_list)

    def _add_action_device_setup(self, settable: bool):
        if settable:
            if 'actn' not in self._device_setup_list:
                self._device_setup_list.append('actn')
        else:
            try:
                del self._device_commands_dict['actn']
            except KeyError:
                pass
            try:
                self._device_setup_list.remove('actn')
            except ValueError:
                pass
        self._cfg["deviceSetup"] = ','.join(self._device_setup_list)

    def set_clock_callback(self, callback):
        """
        Specify a callback function to be called when The Dash server sends clock data.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from dash server.
                The callback must return a Boolean indicating success.
        """
        self._clk_rx_callback = callback

    def unset_clock_callback(self):
        """
        Unset the clock rx callback.
        """
        self._ota_rx_callback = None

    def set_ota_callback(self, callback):
        """
        Specify a callback function to be called when The Dash server sends ota data.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from dash server.
                The callback must return a Boolean indicating success.
        """
        self._clk_rx_callback = callback

    def unset_ota_callback(self):
        """
        Unset the ota rx callback.
        """
        self._ota_rx_callback = None

    def set_wifi_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets wifi parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("wifi", True)
        self._wifi_rx_callback = callback

    def unset_wifi_callback(self):
        """
        Unset the wifi_rx_callback.
        """
        self._set_device_setup("wifi", False)
        self._wifi_rx_callback = None

    def _wifi_rx_event(self, msg) -> str:
        if self._wifi_rx_callback is not None:
            if self._wifi_rx_callback(msg):
                data = self._device_id_str + "\tWIFI\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def set_dashio_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets dashio parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("dashio", True)
        self._dashio_rx_callback = callback

    def unset_dashio_callback(self):
        """
        Unset the dashio callback function.
        """
        self._set_device_setup("dashio", False)
        self._dashio_rx_callback = None

    def _dashio_rx_event(self, msg):
        if self._dashio_rx_callback is not None:
            if self._dashio_rx_callback(msg):
                data = self._device_id_str + "\tDASHIO\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def set_name_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets dashio parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return the new name.
        """
        self._set_device_setup("name", True)
        self._name_rx_callback = callback

    def unset_name_callback(self):
        """
        Unset the name callback function.
        """
        self._set_device_setup("name", False)
        self._name_rx_callback = None

    def _name_callback(self, msg) -> str:
        logger.debug("Name msg: %s", msg)
        return msg[2]

    def _name_rx_event(self, msg) -> str:
        if self._name_rx_callback is not None:
            name = self._name_rx_callback(msg)
            if name:
                self._device_name = name
                data = self._device_id_str + f"\tNAME\t{name}\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def set_tcp_callback(self, callback):
        """Specify a callback function to be called when IoTDashboard sets tcp parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("tcp", True)
        self._tcp_rx_callback = callback

    def unset_tcp_callback(self):
        """
        Unset the tcp callback function.
        """
        self._set_device_setup("tcp", False)
        self._tcp_rx_callback = None

    def _tcp_rx_event(self, msg):
        if self._tcp_rx_callback is not None:
            if self._tcp_rx_callback(msg):
                data = self._device_id_str + "\tTCP\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
            return ""

    def set_mqtt_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets mqtt parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("mqtt", True)
        self._mqtt_rx_callback = callback

    def unset_mqtt_callback(self):
        """
        Unset the mqtt callback function.
        """
        self._set_device_setup("mqtt", False)
        self._mqtt_rx_callback = None

    def _mqtt_rx_event(self, msg):
        if self._mqtt_rx_callback is not None:
            if self._mqtt_rx_callback(msg):
                data = self._device_id_str + "\tMQTT\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def register_connection(self, connection):
        """Connections registered here"""
        if connection.zmq_connection_uuid not in self.connections_list:
            logger.debug("DEVICE REG CONECTION")
            self.connections_list.append(connection.zmq_connection_uuid)
            self.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=connection.zmq_connection_uuid))
            connection.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

    def de_register_connection(self, connection):
        """Connections unregistered here"""
        if connection.zmq_connection_uuid in self.connections_list:
            logger.debug("DEVICE DE-REG CONECTION")
            self.connections_list.remove(connection.zmq_connection_uuid)
            self.rx_zmq_sub.disconnect(CONNECTION_PUB_URL.format(id=connection.zmq_connection_uuid))
            connection.rx_zmq_sub.disconnect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

    def __init__(
        self,
        device_type: str,
        device_id: str,
        device_name: str,
        cfg_dict: dict | None = None,
        context: zmq.Context | None = None
    ) -> None:
        """DashDevice

        Parameters
        ----------
            device_type : str
                A Short description of the device type.
            device_id : str
                A unique identifier for this device
            device_name : str
                The name for this device
            cfg_dict : dict optional
                Setup dict to cfgRev and adds controls defined in cfg_dict, defaults None
            context : optional
                ZMQ context. Defaults to None.
        """
        threading.Thread.__init__(self, daemon=True)

        self.zmq_connection_uuid = "DVCE:" + shortuuid.uuid()
        self._b_zmq_connection_uuid = self.zmq_connection_uuid.encode()
        self.context = context or zmq.Context.instance()
        self._wifi_rx_callback = None
        self._dashio_rx_callback = None
        self._name_rx_callback = None
        self._tcp_rx_callback = None
        self._mqtt_rx_callback = None
        self._clk_rx_callback = None
        self._ota_rx_callback = None
        self.device_type = device_type.translate(BAD_CHARS)
        self.device_id = device_id.translate(BAD_CHARS)
        self._b_device_id = self.device_id.encode('utf-8')
        self._device_name = device_name.strip()
        self._device_setup_list = []
        self.connections_list = []
        self._device_commands_dict = {}
        self._device_commands_dict['CONNECT'] = self._make_connect
        self._device_commands_dict['STATUS'] = self._make_status
        self._device_commands_dict['CFG'] = self._make_cfg64
        self._device_commands_dict['CLK'] = self._server_clk
        self._device_commands_dict['OTA'] = self._server_ota
        self.controls_dict = {}
        self._cfg = {}
        self._cfg["deviceSetup"] = ''
        self._device_id_str = f"\t{device_id}"
        self._cfg["numDeviceViews"] = 0
        if cfg_dict is not None:
            self._cfg["cfgRev"] = cfg_dict['CFG']['cfgRev']
            self.add_all_c64_controls(cfg_dict)
            self.use_cfg64()

        self.running = True
        time.sleep(0.5)
        self.start()

    def use_cfg64(self):
        """Generate a CFG64 formated CFG message
        """
        self._device_commands_dict['CFG'] = self._make_cfg64

    def use_cfg(self):
        """Generate JSON formated CFG messages
        """
        self._device_commands_dict['CFG'] = self._make_cfg

    @property
    def number_of_device_views(self) -> int:
        """Number of device views registered for the device

        Returns
        -------
        int
            Number of device views
        """
        return self._cfg["numDeviceViews"]

    @number_of_device_views.setter
    def number_of_device_views(self, val: int):
        self._cfg["numDeviceViews"] = val

    @property
    def config_revision(self) -> int:
        """Sets the cfgRev number. Increment this number to indicate a new CFG

        Returns
        -------
        int
            The cfgRev number
        """
        return self._cfg["cfgRev"]

    @config_revision.setter
    def config_revision(self, val: int):
        self._cfg["cfgRev"] = val

    def inc_config_revision(self):
        """Incements the configuration revision."""
        if "cfgRev" in self._cfg:
            self._cfg["cfgRev"] = self._cfg["cfgRev"] + 1
        else:
            self._cfg["cfgRev"] = 1

    @property
    def device_name(self) -> str:
        """Device name

        Returns
        -------
        str
            The device name
        """
        return self._device_name

    @device_name.setter
    def device_name(self, val: str):
        self._device_name = val
        self._send_data(f"\t{{device_id}}\tNAME\t{self._device_name}\t")

    def close(self):
        """Close the device"""
        self.running = False

    def _local_command(self, msg_dict):
        logging.debug("LOCAL COMMAND: %s", msg_dict)
        if msg_dict.get('msgType', '') == 'send_announce' and msg_dict.get('deviceID', '') == self.device_id:
            self._send_announce()

    def run(self):
        # Continue the network loop, exit when an error occurs

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"\tWHO")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"COMMAND")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self._b_zmq_connection_uuid)
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "\t" + self.device_id)

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(1))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                try:
                    [data, msg_from] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    logger.debug("Device value error")
                #  logger.debug("DEVICE RX: %s ,%s", msg_from, data)
                if data == b"COMMAND":
                    msg_dict = json.loads(msg_from)
                    self._local_command(msg_dict)
                    continue
                reply = self._on_message(data)
                if reply != "":
                    #  logger.debug("DEVICE TX: %s ,%s", msg_from, data)
                    self.tx_zmq_pub.send_multipart([msg_from, reply.encode('utf-8')])
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        self.context.term()
