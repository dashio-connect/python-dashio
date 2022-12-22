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
import threading
import time
import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL, BAD_CHARS
from .action_station import ActionStation
from .iotcontrol.alarm import Alarm
from .iotcontrol.device_view import DeviceView
from .load_config import encode_cfg64

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
            cntrl_type = data_array[1]
        except KeyError:
            return ""
        if cntrl_type in self._device_commands_dict:
            return self._device_commands_dict[cntrl_type](data_array)
        try:
            reply = self.control_dict[cntrl_type + "\t" + data_array[2]]._message_rx_event(data_array)
            if reply:
                return reply.replace("{device_id}", self.device_id)
        except (KeyError, IndexError):
            pass
        return ""

    def _make_connect(self, _):
        return self._device_id_str + "\tCONNECT\n"

    def _make_status(self, _):
        reply = f"\t{self.device_id}\tNAME\t{self._device_name}\n"
        for value in self.control_dict.values():
            try:
                reply += value.get_state().format(device_id=self.device_id)
            except (TypeError, KeyError):
                pass
        return reply

    def _make_cfg64(self, data):
        try:
            dashboard_id = data[2]
            #  no_views = data[3]
        except IndexError:
            return ""
        reply = self._device_id_str + f"\tCFG\t{dashboard_id}\tC64\t"
        cfg = {}
        cfg["CFG"] = self._cfg
        for control in self.control_dict.values():
            if control.cntrl_type == "ALM":
                continue
            if control.cntrl_type in ("BLE"):
                cfg[control.cntrl_type] = control.get_cfg64(data)
                continue
            if control.cntrl_type not in cfg:
                cfg[control.cntrl_type] = []
            cfg[control.cntrl_type].extend(control.get_cfg64(data))
        c64_json = encode_cfg64(cfg)
        reply += c64_json + "\n"
        return reply

    def _make_cfg(self, data):
        try:
            dashboard_id = data[2]
            #  no_views = data[3]
        except IndexError:
            return ""
        reply = self._device_id_str + f"\tCFG\t{dashboard_id}\tDVCE\t{json.dumps(self._cfg)}\n"
        dvvw_str = ""
        for control in self.control_dict.values():
            if control.cntrl_type == "ALM":
                continue
            if control.cntrl_type == "DVVW":
                cfg_list = control.get_cfg(data)
                for cfg in cfg_list:
                    dvvw_str += self._device_id_str + cfg
            else:
                cfg_list = control.get_cfg(data)
                #logging.debug("CFG: %s", cfg_list)
                for cfg in cfg_list:
                    reply += self._device_id_str + cfg
        reply += dvvw_str
        return reply

    def _send_alarm(self, alarm_id, message_header, message_body):
        payload = self._device_id_str + f"\tALM\t{alarm_id}\t{message_header}\t{message_body}\n"
        logging.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALL", payload.encode('utf-8')])

    def _send_data(self, data: str):
        if not data:
            return
        if isinstance(data, str):
            reply_send = data.format(device_id=self.device_id)
        elif isinstance(data, list):
            reply_send = "\t" + "\t".join(data) + "\n"
        try:
            self.tx_zmq_pub.send_multipart([b"ALL", reply_send.encode('utf-8')])
        except zmq.error.ZMQError:
            pass

    def _send_announce(self):
        payload = self._device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\n"
        logging.debug("ANNOUNCE: %s", payload)
        self.tx_zmq_pub.send_multipart([b"DASH", payload.encode('utf-8')])

    def is_control_loaded(self, control_type, control_id) -> bool:
        """Is the control loaded in the device?"""
        key = f"{control_type}\t{control_id}"
        return key in self.control_dict

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
        key = f"{iot_control.cntrl_type}\t{iot_control.control_id}"

        if key not in self.control_dict:
            self.inc_config_revision()
            if isinstance(iot_control, DeviceView):
                self._cfg["numDeviceViews"] += 1
            self.control_dict[key] = iot_control
            return True
        return False


    def remove_control(self, iot_control):
        """Remove a control a control to the device.

        Parameters
        ----------
            iot_control : iotControl
        """
        if isinstance(iot_control, DeviceView):
            self._cfg["numDeviceViews"] -= 1
        key = f"{iot_control.cntrl_type}\t{iot_control.control_id}"
        if key in self.control_dict:
            del self.control_dict[key]
        

    def _set_devicesetup(self, control_name: str, settable: bool):
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

    def set_wifi_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets wifi parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_devicesetup("wifi", True)
        self._wifi_rx_callback = callback

    def unset_wifi_callback(self):
        """
        Unset the wifi_rx_callback.
        """
        self._set_devicesetup("wifi", False)
        self._wifi_rx_callback = None

    def _wifi_rx_event(self, msg):
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
        self._set_devicesetup("dashio", True)
        self._dashio_rx_callback = callback

    def unset_dashio_callback(self):
        """
        Unset the dashio callback function.
        """
        self._set_devicesetup("dashio", False)
        self._dashio_rx_callback = None

    def _dashio_rx_event(self, msg):
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
        self._set_devicesetup("name", True)
        self._name_rx_callback = callback

    def unset_name_callback(self):
        """
        Unset the name callback function.
        """
        self._set_devicesetup("name", False)
        self._name_rx_callback = None

    def _name_rx_event(self, msg):
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
        self._set_devicesetup("tcp", True)
        self._tcp_rx_callback = callback

    def unset_tcp_callback(self):
        """
        Unset the tcp callback function.
        """
        self._set_devicesetup("tcp", False)
        self._tcp_rx_callback = None

    def _tcp_rx_event(self, msg):
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
        self._set_devicesetup("mqtt", True)
        self._mqtt_rx_callback = callback

    def unset_mqtt_callback(self):
        """
        Unset the mqtt callback function.
        """
        self._set_devicesetup("mqtt", False)
        self._mqtt_rx_callback = None

    def _mqtt_rx_event(self, msg):
        if self._mqtt_rx_callback(msg):
            data = self._device_id_str + "\tMQTT\n"
            self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def register_connection(self, connection):
        """Cennections register here"""
        if connection.zmq_connection_uuid not in self.connections_list:
            logging.debug("DEVICE REG CONECTION")
            self.connections_list.append(connection.zmq_connection_uuid)
            self.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=connection.zmq_connection_uuid))
            connection.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
            self._send_announce()
        if self._add_actions:
            self.action_station.register_connection(connection)

    def __init__(
        self,
        device_type: str,
        device_id: str,
        device_name: str,
        add_actions: bool = False,
        cfg_dict: dict = None,
        context: zmq.Context=None
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
                Setup dict to cfgRev, defaults None
            add_actions : boolean
                To include actions or not, defaults false
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
        self.device_type = device_type.translate(BAD_CHARS)
        self.device_id = device_id.translate(BAD_CHARS)
        self._b_device_id = self.device_id.encode('utf-8')
        self._device_name = device_name.strip()
        self._device_setup_list = []
        self.connections_list = []
        self._device_commands_dict = {}
        self._device_commands_dict['CONNECT'] = self._make_connect
        self._device_commands_dict['STATUS'] = self._make_status
        self._device_commands_dict['CFG'] = self._make_cfg
        self.control_dict = {}
        self._cfg = {}
        self._device_id_str = f"\t{device_id}"
        if cfg_dict is not None:
            self._cfg["cfgRev"] = cfg_dict['CFG']['cfgRev']
        self._cfg["numDeviceViews"] = 0
        self._add_actions = add_actions
        if self._add_actions:
            self._add_action_device_setup(True)
            self.action_station = ActionStation(self, context=self.context)
            time.sleep(0.5)
            self.action_station.device_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
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
        if self._add_actions:
            self.action_station.close()
        self.running = False

    def _local_command(self, msg_dict):
        if msg_dict['msgType'] == 'send_announce':
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
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                try:
                    [data, msg_from] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    logging.debug("Device value error")
                #logging.debug("DEVICE RX: %s ,%s", msg_from, data)
                if data == b"COMMAND":
                    msg_dict = json.loads(msg_from)
                    self._local_command(msg_dict)
                    continue
                reply = self._on_message(data)
                if reply != "":
                    # logging.debug("DEVICE TX: %s ,%s", msg_from, data)
                    self.tx_zmq_pub.send_multipart([msg_from, reply.encode('utf-8')])
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        self.context.term()
