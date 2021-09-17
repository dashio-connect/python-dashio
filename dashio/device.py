"""device.py"""
import json
import logging
import threading

import shortuuid
import zmq

from .constants import DEVICE_PUB_URL, BAD_CHARS
from .iotcontrol.alarm import Alarm
from .iotcontrol.device_view import DeviceView


class Device(threading.Thread):
    """Dashio Device

    Attributes
    ----------
    device_type (str) :
        The type of device (e.g. TempSensor, GPS...).
    device_id (str) :
        A unique identifier for this device
    device_name (str) :
        The name for this device (E.g. GlassHouse, MothersZimmerFrame...)

    Methods
    -------
    send(header, body) :
        Send an alarm with a header and body.

    send_alarm(alarm_id, message_header, message_body) :
        Sends and alarm notification to DashIO apps registered on the DashIO server.
        Notifications are only sent if the device is connected to the DashIO server with a DashConnection.

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

    set_mqtt_callback(callback)
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
            self._control_dict[cntrl_type + "_" + data_array[2]].message_rx_event(data_array)
        except (KeyError, IndexError):
            pass
        return ""

    def _make_connect(self, _):
        return self._device_id_str + "\tCONNECT\n"

    def _make_status(self, _):
        reply = f"\t{self.device_id}\tNAME\t{self._device_name}\n"
        for key in self._control_dict:
            try:
                reply += self._control_dict[key].get_state().format(device_id=self.device_id)
            except (TypeError, KeyError):
                pass
        return reply

    def _make_cfg(self, data):
        reply = self._device_id_str + '\tCFG\tDVCE\t' + json.dumps(self._cfg) + "\n"
        for key in self._control_dict:
            reply += self._device_id_str + self._control_dict[key].get_cfg(data[2])
        return reply

    def send_alarm(self, alarm_id, message_header, message_body):
        """Send an Alarm to the Dash server.

        Parameters
        ----------
        alarm_id : str
            An identifier used by iotdashboard to manage the alarm. It should be unique for each connection.
        message_header : str
            Title for the Alarm.
        message_body : str
            The text body of the Alarm.
        """
        payload = self._device_id_str + f"\t{alarm_id}\t{message_header}\t{message_body}\n"
        logging.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALARM", b'0', payload.encode('utf-8')])

    def _send_data(self, data: str):
        if not data:
            return
        reply_send = data.format(device_id=self.device_id)
        try:
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', reply_send.encode('utf-8')])
        except zmq.error.ZMQError:
            pass

    def _send_announce(self):
        payload = self._device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\n"
        logging.debug("ANNOUNCE: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", b'0', payload.encode('utf-8')])

    def add_control(self, iot_control):
        """Add a control to the device.

        Parameters
        ----------
            iot_control : iotControl
        """
        if isinstance(iot_control, DeviceView):
            self._cfg["numDeviceViews"] += 1
        try:
            if isinstance(iot_control, Alarm):
                iot_control.message_tx_event += self.send_alarm
            else:
                iot_control.message_tx_event += self._send_data
        except AttributeError:
            pass
        key = iot_control.cntrl_type + "_" + iot_control.control_id
        self._control_dict[key] = iot_control

    def _set_devicesetup(self, control_name: str, settable: bool):
        if settable:
            self._device_commands_dict[control_name.upper()] = getattr(self, '_' + control_name + '_rx_event', None)
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
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])
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
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])
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
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])
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
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])
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
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])
        return ""

    def __init__(self,
                 device_type: str,
                 device_id: str,
                 device_name: str,
                 context=None) -> None:
        """DashDevice

        Parameters
        ----------
            device_type : str
                A Short description of the device type.
            device_id : str
                A unique identifier for this device
            device_name : str
                The name for this device
            context : optional
                ZMQ context. Defaults to None.
        """
        threading.Thread.__init__(self, daemon=True)

        self.zmq_pub_id = shortuuid.uuid()
        self._b_zmq_pub_id = self.zmq_pub_id.encode('utf-8')
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
        self._device_commands_dict = {}
        self._device_commands_dict['CONNECT'] = self._make_connect
        self._device_commands_dict['STATUS'] = self._make_status
        self._device_commands_dict['CFG'] = self._make_cfg
        self._control_dict = {}
        self._cfg = {}
        self._device_id_str = f"\t{device_id}"
        self._cfg["numDeviceViews"] = 0
        self.running = True
        self.start()

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
        """Close the connection"""
        self.running = False

    def run(self):
        # Continue the network loop, exit when an error occurs

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(DEVICE_PUB_URL.format(id=self.zmq_pub_id))
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "COMMAND")

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.rx_zmq_sub in socks:
                msg = self.rx_zmq_sub.recv_multipart()
                if len(msg) == 3:
                    if msg[0] == b"COMMAND":
                        if msg[2] == b'send_announce':
                            self._send_announce()
                        continue
                    reply = self._on_message(msg[2])
                    if reply:
                        self.tx_zmq_pub.send_multipart([msg[0], msg[1], reply.encode('utf-8')])

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        self.context.term()
