import logging
import zmq
import threading

from .iotcontrol.name import Name
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page

from .mqttconnection import mqttConnectionThread
from .tcpconnection import tcpConnectionThread
from .dashconnection import dashConnectionThread


class dashDevice(threading.Thread):

    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __on_message(self, id, payload):
        data = str(payload, "utf-8").strip()
        command_array = data.split("\n")
        reply = ""
        for ca in command_array:
            try:
                reply += self.__on_command(id, ca.strip())
            except TypeError:
                pass
        return reply

    def __on_command(self, id, data):
        data_array = data.split("\t")
        cntrl_type = data_array[0]
        reply = ""
        if cntrl_type == "CONNECT":
            reply = "\tCONNECT\t{}\t{}\t{}\n".format(self.name_control.control_id, self.device_id, id.decode("utf-8"))
        elif cntrl_type == "WHO":
            reply = self.who
        elif cntrl_type == "STATUS":
            reply = self.__make_status()
        elif cntrl_type == "CFG":
            reply = self.__make_cfg()
        elif cntrl_type == "NAME":
            self.name_cntrl.message_rx_event(data_array[1:])
        else:
            try:
                key = cntrl_type + "_" + data_array[1]
            except IndexError:
                return
            try:
                self.control_dict[key].message_rx_event(data_array[2:])
            except KeyError:
                pass
        return reply

    def __make_status(self):
        reply = ""
        for key in self.control_dict.keys():
            try:
                reply += self.control_dict[key].get_state()
            except TypeError:
                pass
        return reply

    def __make_cfg(self):
        reply = '\tCFG\tDVCE\t{{"numPages": {}}}\n'.format(self.number_of_pages)
        for key in self.control_dict.keys():
            reply += self.control_dict[key].get_cfg()
        for key in self.alarm_dict.keys():
            reply += self.alarm_dict[key].get_cfg()
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
        data = "\tMSSG\t{}\t{}\t{}\n".format(title, header, message)
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

        payload = "\t{}\t{}\t{}\n".format(alarm_id, message_header, message_body)
        logging.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALL", b'0', payload.encode('utf-8')])

    def __send_connect(self):
        data = "\tCONNECT\t{}\n".format(self.name_control.control_id)
        self.tx_zmq_pub.send_multipart([b'ANNOUNCE', b'', data.encode('utf-8')])

    def send_data(self, data):
        """Send data to the Dash server.

        Parameters
        ----------
        data : str
            Data to be sent to the server
        """
        self.tx_zmq_pub.send_multipart([b"ALL", b'0', data.encode('utf-8')])

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

    def __init__(self, device_type, device_id, device_name) -> None:
        threading.Thread.__init__(self, daemon=True)

        self.context = zmq.Context.instance()

        tx_url_internal = "inproc://RX_{}".format(device_id)
        rx_url_internal = "inproc://TX_{}".format(device_id)

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(tx_url_internal)

        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.bind(rx_url_internal)
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"")

        self.poller = zmq.Poller()
        self.poller.register(self.rx_zmq_sub, zmq.POLLIN)

        self.device_type = device_type
        self.device_id = device_id
        self.name_control = Name(device_name)
        self.num_mqtt_connections = 0
        self.num_dash_connections = 0
        self.connections = {}
        self.control_dict = {}
        self.alarm_dict = {}
        self.who = "\tWHO\n"
        self.number_of_pages = 0
        self.running = True
        self.start()

    def add_mqtt_connection(self, username, password, host, port, use_ssl=False):
        self.num_mqtt_connections += 1
        connection_id = self.device_type + "_MQTT" + str(self.num_mqtt_connections)
        new_mqtt_con = mqttConnectionThread(connection_id, self.device_id, host, port, username, password, use_ssl, self.context)
        new_mqtt_con.add_control(self.name_control)
        self.connections[connection_id] = new_mqtt_con

    def add_tcp_connection(self, url, port):
        connection_id = self.device_type + "_TCP:{}".format(str(port))
        new_tcp_con = tcpConnectionThread(connection_id, self.device_id, url, port, self.context)
        self.connections[connection_id] = new_tcp_con

    def add_dash_connection(self, username, password, host="dash.dashio.io", port=8883):
        self.num_dash_connections += 1
        connection_id = self.device_type + "_DASH" + str(self.num_dash_connections)
        new_dash_con = dashConnectionThread(connection_id, self.device_id, username, password, host, port, self.context)
        self.connections[connection_id] = new_dash_con
        self.__send_connect()

    def close(self):
        for conn in self.connections:
            self.connections[conn].running = False

    def run(self):
        # Continue the network loop, exit when an error occurs
        while self.running:
            socks = dict(self.poller.poll())
            if self.rx_zmq_sub in socks:
                msg = self.rx_zmq_sub.recv_multipart()
                if len(msg) == 3:
                    reply = self.__on_message(msg[0], msg[2])
                    if reply:
                        self.tx_zmq_pub.send_multipart([msg[0], msg[1], reply.encode('utf-8')])

        self.mqttc.publish(self.announce_topic, "disconnect")
        self.mqttc.loop_stop()
