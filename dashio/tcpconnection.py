import zmq
import threading
import logging
import time
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page
from .iotcontrol.name import Name


class tcpConnectionThread(threading.Thread):
    """Setups and manages a connection thread to iotdashboard via TCP."""

    def __on_message(self, data):
        data_array = data.split("\t")
        cntrl_type = data_array[0]
        reply = ""
        if cntrl_type == "CONNECT":
            reply = "\tCONNECT\t{}\t{}\t{}\n".format(self.device_name, self.device_id, self.name)
        elif cntrl_type == "WHO":
            reply = self.who
        elif cntrl_type == "STATUS":
            reply = self.__make_status()
        elif cntrl_type == "CFG":
            reply = self.__make_cfg()
        else:
            key = cntrl_type + "_" + data_array[1]
            try:
                self.control_dict[key].message_rx_event(data_array[1:])
            except KeyError:
                pass
        return reply

    def __make_status(self):
        all_status = ""
        for key in self.control_dict.keys():
            try:
                all_status += self.control_dict[key].get_state()
            except TypeError:
                pass
        return all_status

    def __make_cfg(self):
        all_cfg = ""
        all_cfg += '\tCFG\tCFG\t{{"numPages": {}}}\n'.format(self.number_of_pages)
        for key in self.control_dict.keys():
            all_cfg += self.control_dict[key].get_cfg()
        for key in self.alarm_dict.keys():
            all_cfg += self.alarm_dict[key].get_cfg()
        return all_cfg

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
        logging.debug("Tx: %s", data)
        for id in self.socket_ids:
            self.socket.send(id, zmq.SNDMORE)
            self.socket.send_string(data)

    def send_data(self, data):
        """Send data to the Dash server.

        Parameters
        ----------
        data : str
            Data to be sent to the server
        """

        for id in self.socket_ids:

            logging.debug("ID: %s, Tx: %s", str(id), data)
            try:
                self.socket.send(id, zmq.SNDMORE)
                self.socket.send_string(data)
            except zmq.error.ZMQError:
                pass

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

    def __init__(self, connection_name, device_id, device_name, context=None, url="tcp://*:5000", watch_dog=60):
        """
        Arguments:
            connection_name {str} --  The connection name as advertised to iotdashboard.
            device_id {str} -- A string to uniquely identify the device connection. (In case of other connections with the same name.)
            device_name {str} -- A string for iotdashboard to use as an alias for the connection.
            url {str} -- The address and port to set up a connection.

        Keyword Arguments:
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
        """

        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.socket = self.context.socket(zmq.STREAM)
        self.socket.bind(url)

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.control_dict = {}
        self.alarm_dict = {}
        self.socket_ids = []
        self.number_of_pages = 0
        self.watch_dog = watch_dog
        self.watch_dog_counter = 1  # If watch_dog is zero don't send anything
        self.running = True
        self.name = connection_name
        self.name_cntrl = Name(device_name)
        self.device_name = device_name
        self.device_id = device_id
        self.add_control(self.name_cntrl)
        self.who = "\tWHO\n"
        self.connect = "\tCONNECT\t{}\t{}\t{}\n".format(device_name, device_id, connection_name)

    def run(self):
        # Continue the network loop, exit when an error occurs
        rc = 0
        id = self.socket.recv()
        self.socket.recv()  # empty data here
        while self.running:
            socks = dict(self.poller.poll())

            if self.socket in socks:
                id = self.socket.recv()
                if id not in self.socket_ids:
                    logging.debug("Added Socket ID: " + str(id))
                    self.socket_ids.append(id)
                data = self.socket.recv()
                message = str(data, "utf-8")
                logging.debug("RX: " + message)
                if message:
                    reply = self.__on_message(message.strip())
                    if reply:
                        logging.debug("TX: " + reply)
                        self.socket.send(id, zmq.SNDMORE)
                        self.socket.send_string(reply)
                else:
                    if id in self.socket_ids:
                        logging.debug("Removed Socket ID: " + str(id))
                        self.socket_ids.remove(id)
            time.sleep(0.1)

        for id in self.socket_ids:
            try:
                self.socket.send(id, zmq.SNDMORE)
                self.socket.send_string("")
            except zmq.error.ZMQError:
                pass
        self.socket.close()
        self.context.term()
