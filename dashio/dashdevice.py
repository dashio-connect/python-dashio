import json
import logging
import threading

import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL
from .iotcontrol.alarm import Alarm
from .iotcontrol.event import Event
from .iotcontrol.controls_box import ControlsBox


class DashDevice(threading.Thread):

    """Device for IoTDashboard."""

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
        # logging.debug('Device RX: %s', rx_device_id)
        if rx_device_id == "WHO":
            return self.device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\n"
        if rx_device_id != self.device_id:
            return ""
        try:
            cntrl_type = data_array[1]
        except KeyError:
            return ""
        if cntrl_type == "CONNECT":
            return self.connect
        if cntrl_type == "STATUS":
            return self._make_status()
        if cntrl_type == "CFG":
            return self._make_cfg(data_array)
        if cntrl_type in self._device_commands_dict:
            self._device_commands_dict[cntrl_type](data_array)
        else:
            try:
                self.control_dict[cntrl_type + "_" + data_array[2]].message_rx_event(data_array)
            except (KeyError, IndexError):
                pass
        return ""

    def _make_status(self):
        reply = f"\t{self.device_id}\tNAME\t{self._device_name}\n"
        for key in self.control_dict:
            try:
                reply += self.control_dict[key].get_state().format(device_id=self.device_id)
            except (TypeError, KeyError):
                pass
        return reply

    def _make_cfg(self, data):
        reply = self.device_id_str + '\tCFG\tDVCE\t' + json.dumps(self._cfg) + "\n"
        for key in self.control_dict:
            reply += self.device_id_str + self.control_dict[key].get_cfg(data[2], data[3])
        return reply

    def send_popup_message(self, title, header, message):
        """Send a popup message to the Dash server.

        Parameters
        ----------
        title : str
            Title of the message.
        header : str
            Header of the message.
        message : str
            Message body.
        """
        data = self.device_id_str + f"\tMSSG\t{title}\t{header}\t{message}\n"
        self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])

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

        payload = self.device_id_str + f"\t{alarm_id}\t{message_header}\t{message_body}\n"
        logging.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALARM", b'0', payload.encode('utf-8')])

    def _send_data(self, data: str):
        """Send data.

        Parameters
        ----------
        data : str
            Data to be sent
        """
        if not data:
            return
        reply_send = data.format(device_id=self.device_id)
        try:
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', reply_send.encode('utf-8')])
        except zmq.error.ZMQError:
            pass

    def _send_announce(self):
        payload = self.device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\n"
        logging.debug("ANNOUNCE: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", b'0', payload.encode('utf-8')])

    def add_control(self, iot_control):
        """Add a control to the device.

        Parameters
        ----------
        iot_control : iotControl
        """
        if isinstance(iot_control, ControlsBox):
            self._cfg["numCtrlsBoxes"] += 1
        try:
            if isinstance(iot_control, Alarm):
                iot_control.message_tx_event += self.send_alarm
            else:
                iot_control.message_tx_event += self._send_data
        except AttributeError:
            pass
        key = iot_control.msg_type + "_" + iot_control.control_id
        self.control_dict[key] = iot_control

    def add_connection(self, connection):
        """Add a connection to the device

        Args:
            connection ([type]): [description]
        """
        self.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=connection.connection_id))
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, connection.connection_id.encode('utf-8'))

    def _set_devicesetup(self, control_name: str, settable: bool):
        if settable:
            self._device_commands_dict[control_name.upper()] = getattr(self, control_name + '_rx_event', None)
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

    def __init__(self,
                 device_type: str,
                 device_id: str,
                 device_name: str,
                 edit_lock=False,
                 name_setable=False,
                 wifi_setable=False,
                 dashio_setable=False,
                 tcp_setable=False,
                 mqtt_setable=False,
                 context=None) -> None:
        """DashDevice

        Args:
            device_type (str): A Short description of the device type.
            device_id (str): A unique identifier for this device
            device_name (str): The name for this device
            edit_lock (bool, optional): Enables/Disables editing in IoTDashboard. Defaults to False.
            name_setable (bool, optional): Allows IoT Dashboard to set the device name. Defaults to False.
            wifi_setable (bool, optional): Allows IOT Dashboard to set the wifi parameters. Defaults to False.
            dashio_setable (bool, optional): Allows IOT Dashboard to set the dash server connection parameters. Defaults to False.
            tcp_setable (bool, optional): Allows IOT Dashboard to set the tcp connection parameters. Defaults to False.
            mqtt_setable (bool, optional): Allows IOT Dashboard to set the mqtt connection parameters.. Defaults to False.
            context ([type], optional): [description]. Defaults to None.
        """
        threading.Thread.__init__(self, daemon=True)

        self.zmq_pub_id = shortuuid.uuid()
        self._b_zmq_pub_id = self.zmq_pub_id.encode('utf-8')
        self.context = context or zmq.Context.instance()
        self.wifi_rx_event = Event()
        self.dash_rx_event = Event()
        self.name_rx_event = Event()
        self.tcp_rx_event = Event()
        self.mqtt_rx_event = Event()
        self.device_type = device_type.strip()
        self.device_id = device_id.strip()
        self._b_device_id = self.device_id.encode('utf-8')
        self._device_name = device_name.strip()
        self._device_setup_list = []
        self._device_commands_dict = {}
        self.control_dict = {}
        self._cfg = {}
        self.device_id_str = f"\t{device_id}"
        self.connect = self.device_id_str + "\tCONNECT\n"
        self._cfg["numCtrlsBoxes"] = 0

        self.edit_lock = edit_lock
        self.name_setable = name_setable
        self.wifi_setable = wifi_setable
        self.dashio_setable = dashio_setable
        self.tcp_setable = tcp_setable
        self.mqtt_setable = mqtt_setable
        self.running = True
        self.start()

    @property
    def edit_lock(self) -> bool:
        """Enables/Disables editing in IoTDashboard

        Returns:
            bool:
        """
        return self._cfg["editLock"]

    @edit_lock.setter
    def edit_lock(self, val: bool):
        self._cfg["editLock"] = val

    @property
    def number_of_controls_boxes(self) -> int:
        return self._cfg["numCtrlsBoxes"]

    @number_of_controls_boxes.setter
    def number_of_controls_boxes(self, val: int):
        self._cfg["numCtrlsBoxes"] = val

    @property
    def name_setable(self) -> bool:
        return self._name_setable

    @name_setable.setter
    def name_setable(self, val: bool):
        self._name_setable = val
        self._set_devicesetup("name", val)

    @property
    def wifi_setable(self) -> bool:
        return self._wifi_setable

    @wifi_setable.setter
    def wifi_setable(self, val: bool):
        self._wifi_setable = val
        self._set_devicesetup("wifi", val)

    @property
    def dashio_setable(self) -> bool:
        return self._dashio_setable

    @dashio_setable.setter
    def dashio_setable(self, val: bool):
        self._dashio_setable = val
        self._set_devicesetup("dashio", val)

    @property
    def tcp_setable(self) -> bool:
        return self._tcp_setable

    @tcp_setable.setter
    def tcp_setable(self, val: bool):
        self._tcp_setable = val
        self._set_devicesetup("tcp", val)

    @property
    def mqtt_setable(self) -> bool:
        return self._mqtt_setable

    @mqtt_setable.setter
    def mqtt_setable(self, val: bool):
        self._mqtt_setable = val
        self._set_devicesetup("mqtt", val)

    @property
    def device_name(self) -> str:
        return self._device_name

    @device_name.setter
    def device_name(self, val: str):
        self._device_name = val
        self._send_data(f"\t{{device_id}}\tNAME\t{self._device_name}\t")

    def close(self):
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
