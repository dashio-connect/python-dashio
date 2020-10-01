import zmq
import threading
import logging
import time
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page
from .iotcontrol.name import Name

# “\t CONNECT \t Device_Name \t DeviceID \t Connection_Name \n”
class tcpConnectionThread(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __on_message(self, id, data):
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
            reply = "\tCONNECT\t{}\t{}\t{}\n".format(self.name_cntrl.control_id, self.device_id, self.connection_id)
        elif cntrl_type == "WHO":
            reply = self.who
        elif cntrl_type == "STATUS":
            reply = self.__make_status()
        elif cntrl_type == "CFG":
            reply = self.__make_cfg()
        else:
            try:
                key = cntrl_type + "_" + data_array[1]
            except IndexError:
                return
            try:
                self.control_dict[key].message_rx_event(data_array[1:])
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
        self.send_data(data)

    def send_data(self, data):
        """Send data to the Dash server.

        Parameters
        ----------
        data : str
            Data to be sent to the server
        """
        self.frontend.send_string(data)

    def add_control(self, iot_control):
        """Add a control to the connection.

        Parameters
        ----------
        iot_control : iotControl
        """
        if isinstance(iot_control, Alarm):
            pass
        else:
            if isinstance(iot_control, Page):
                self.number_of_pages += 1
            iot_control.message_tx_event += self.send_data
            key = iot_control.msg_type + "_" + iot_control.control_id
            self.control_dict[key] = iot_control

    def __init__(self, connection_id, device_id, device_name, context=None, url="tcp://*:5000", watch_dog=60):
        """
        Arguments:
            connection_id {str} --  The connection name as advertised to iotdashboard.
            device_id {str} -- A string to uniquely identify the device connection. (In case of other connections with the same name.)
            device_name {str} -- A string for iotdashboard to use as an alias for the connection.
            url {str} -- The address and port to set up a connection.

        Keyword Arguments:
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.tcpsocket = self.context.socket(zmq.STREAM)
        self.tcpsocket.bind(url)
        self.tcpsocket.set(zmq.SNDTIMEO, 5)

        url_internal = "inproc://{}".format(device_id)
        self.frontend = self.context.socket(zmq.PUB)
        self.frontend.bind(url_internal)

        self.backend = self.context.socket(zmq.SUB)
        self.backend.connect(url_internal)

        # Subscribe on everything
        self.backend.setsockopt(zmq.SUBSCRIBE, b"")

        self.poller = zmq.Poller()
        self.poller.register(self.tcpsocket, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

        self.control_dict = {}
        self.alarm_dict = {}
        self.socket_ids = []
        self.number_of_pages = 0
        self.watch_dog = watch_dog
        self.watch_dog_counter = 1  # If watch_dog is zero don't send anything
        self.running = True
        self.connection_id = connection_id
        self.name_cntrl = Name(device_name)
        self.device_id = device_id
        self.add_control(self.name_cntrl)
        self.who = "\tWHO\n"

    def run(self):
        def __zmq_tcp_send(id, data):
            try:
                self.tcpsocket.send(id, zmq.SNDMORE)
                self.tcpsocket.send_string(data, zmq.NOBLOCK)
            except zmq.error.ZMQError as e:
                logging.debug("Sending TX Error: " + str(e))
                self.socket_ids.remove(id)

        # Continue the network loop, exit when an error occurs
        rc = 0
        id = self.tcpsocket.recv()
        self.tcpsocket.recv()  # empty data here
        while self.running:
            socks = dict(self.poller.poll())

            if self.tcpsocket in socks:
                id = self.tcpsocket.recv()
                message = self.tcpsocket.recv_string()
                if id not in self.socket_ids:
                    logging.debug("Added Socket ID: " + str(id))
                    self.socket_ids.append(id)
                logging.debug("TCP ID: %s, RX: %s", str(id), message.rstrip())
                if message:
                    reply = self.__on_message(id, message.strip())
                    if reply:
                        logging.debug("TCP ID: %s, TX: %s", str(id), reply.rstrip())
                        __zmq_tcp_send(id, reply)
                else:
                    if id in self.socket_ids:
                        logging.debug("Removed Socket ID: " + str(id))
                        self.socket_ids.remove(id)
            if self.backend in socks:
                data = self.backend.recv_string()
                for id in self.socket_ids:
                    logging.debug("TCP ID: %s, Tx: %s", str(id), data.rstrip())
                    __zmq_tcp_send(id, data)

        for id in self.socket_ids:
            self._zmq_send(id, "")
        self.tcpsocket.close()
        self.context.term()
