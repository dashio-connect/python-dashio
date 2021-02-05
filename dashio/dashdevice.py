import logging
import zmq
import threading
import json

from .iotcontrol.name import Name
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page
from .iotcontrol.event import Event

class dashDevice(threading.Thread):

    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __on_message(self, payload):
        data = str(payload, "utf-8").strip()
        command_array = data.split("\n")
        reply = ""
        for ca in command_array:
            try:
                reply += self.__on_command(ca.strip())
            except TypeError:
                pass
        return reply

    def __on_command(self, data):
        data_array = data.split("\t")
        rx_device_id = data_array[0]
        # logging.debug('Device RX: %s', rx_device_id)
        reply = ""
        if rx_device_id == "WHO":
            reply = self.device_id_str + "\tWHO\t{}\t{}\n".format(self.device_type, self.device_name_cntrl.control_id)
            return reply
        elif rx_device_id != self.device_id:
            return reply
        cntrl_type = data_array[1]
        if cntrl_type == "CONNECT":
            reply = self.connect
        elif cntrl_type == "STATUS":
            reply = self.__make_status()
        elif cntrl_type == "CFG":
            reply = self.__make_cfg(data_array[2], data_array[3])
        elif cntrl_type == "NAME":
            if self._set_name:
                self.device_name_cntrl.message_rx_event(data_array[2:])
        elif cntrl_type == "WIFI":
            if self._set_wifi:
                self.wifi_rx_event(data_array)
        elif cntrl_type == "DASH":
            if self._set_dash:
                self.dash_rx_event(data_array)
        else:
            try:
                key = cntrl_type + "_" + data_array[2]
            except IndexError:
                return reply
            try:
                self.control_dict[key].message_rx_event(data_array)
            except KeyError:
                pass
        return reply

    def __make_status(self):
        reply = ""
        for key in self.control_dict.keys():
            try:
                reply += self.control_dict[key].get_state().format(device_id=self.device_id)
            except TypeError:
                pass
        return reply

    def __make_cfg(self, page_x, page_y):
        reply = ""
        if self.number_of_pages:
            reply = self.device_id_str + '\tCFG\tDVCE\t' + json.dumps(self._cfg) + "\n"
        for key in self.control_dict.keys():
            reply += self.device_id_str + self.control_dict[key].get_cfg(page_x, page_y)
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
        data = self.device_id_str + "\tMSSG\t{}\t{}\t{}\n".format(title, header, message)
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

        payload = self.device_id_str + "\t{}\t{}\t{}\n".format(alarm_id, message_header, message_body)
        logging.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALARM", b'0', payload.encode('utf-8')])

    def send_data(self, data: str):
        """Send data.

        Parameters
        ----------
        data : str
            Data to be sent
        """
        reply_send = data.format(device_id=self.device_id)
        try:
            self.tx_zmq_pub.send_multipart([b"ALL", b'0', reply_send.encode('utf-8')])
        except zmq.error.ZMQError:
            pass

    def add_control(self, iot_control):
        """Add a control to the connection.

        Parameters
        ----------
        iot_control : iotControl
        """
        if isinstance(iot_control, Alarm):
            iot_control.message_tx_event += self.send_alarm
            key = iot_control.msg_type + "_" + iot_control.control_id
            self.alarm_dict[key] = iot_control
        else:
            if isinstance(iot_control, Page):
                self.number_of_pages += 1
            iot_control.message_tx_event += self.send_data
            key = iot_control.msg_type + "_" + iot_control.control_id
            self.control_dict[key] = iot_control

    def add_connection(self, device):
        tx_url_internal = "inproc://RX_{}".format(device.connection_id)
        rx_url_internal = "inproc://TX_{}".format(device.connection_id)
        self.tx_zmq_pub.connect(tx_url_internal)
        self.rx_zmq_sub.connect(rx_url_internal)
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, device.connection_id.encode('utf-8'))

    def __set_devicesetup(self):
        device_setup = ""
        if self._set_dash:
            device_setup += "dashio"
        if self._set_name:
            if self._set_dash:
                device_setup += ",name"
            else:
                device_setup += "name"
        if self._set_wifi:
            if self._set_dash or self._set_name:
                device_setup += ",wifi"
            else:
                device_setup += "wifi"
        self._cfg["deviceSetup"] = device_setup

    def __init__(self,
                 device_type,
                 device_id,
                 device_name,
                 edit_lock=False,
                 set_name=False,
                 set_wifi=False,
                 set_dash=False,
                 context=None) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = context or zmq.Context.instance()
        self.wifi_rx_event = Event()
        self.dash_rx_event = Event()
        self.device_type = device_type.strip()
        self.device_id = device_id.strip()
        self.device_name_cntrl = Name(device_name.strip())
        self.control_dict = {}
        self.alarm_dict = {}
        self._cfg = {}
        self.add_control(self.device_name_cntrl)
        self.device_id_str = "\t{}".format(device_id)
        self.connect = self.device_id_str + "\tCONNECT\n"
        self.number_of_pages = 0

        self.edit_lock = edit_lock
        self._set_name = set_name
        self._set_wifi = set_wifi
        self._set_dash = set_dash
        self.__set_devicesetup()
        self.running = True
        self.start()

    @property
    def edit_lock(self) -> bool:
        return self._cfg["editLock"]

    @edit_lock.setter
    def edit_lock(self, val: bool):
        self._cfg["editLock"] = val

    @property
    def number_of_pages(self) -> int:
        return self._cfg["numPages"]

    @number_of_pages.setter
    def number_of_pages(self, val: int):
        self._cfg["numPages"] = val

    @property
    def set_name(self) -> bool:
        return self._set_name

    @set_name.setter
    def set_name(self, val: bool):
        self._set_name = val
        self.__set_devicesetup()

    @property
    def set_wifi(self) -> bool:
        return self._set_wifi

    @set_wifi.setter
    def set_wifi(self, val: bool):
        self._set_wifi = val
        self.__set_devicesetup()

    @property
    def set_dash(self) -> bool:
        return self._set_dash

    @set_dash.setter
    def set_dash(self, val: bool):
        self._set_dash = val
        self.__set_devicesetup()

    def close(self):
        self.running = False

    def run(self):
        # Continue the network loop, exit when an error occurs

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"")

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
                    reply = self.__on_message(msg[2])
                    if reply:
                        self.tx_zmq_pub.send_multipart([msg[0], msg[1], reply.encode('utf-8')])

        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
        self.context.term()
