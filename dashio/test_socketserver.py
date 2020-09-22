import socketserver
import threading
import time
import ssl
import logging
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page
from .iotcontrol.name import Name

# TODO: Add documentation


class mqttConnectionThread(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").rstrip()
        logging.debug("RX: %s", data)
        data_array = data.split("\t")
        cntrl_type = data_array[1]
        if cntrl_type == "WHO":
            self.mqttc.publish(self.data_topic, self.who)
        elif cntrl_type == "STATUS":
            self.mqttc.publish(self.data_topic, self.__make_status())
        elif cntrl_type == "CFG":
            self.mqttc.publish(self.data_topic, self.__make_cfg())
        else:
            key = cntrl_type + "_" + data_array[2]
            self.control_dict[key].message_rx_event(data_array[2:])

    def __make_status(self):
        all_status = ""
        for key in self.control_dict.keys():
            all_status += self.control_dict[key].get_state()
        logging.debug(all_status)
        return all_status

    def __make_cfg(self):
        all_cfg = ""
        all_cfg += '\tCFG\tCFG\t{{"numPages": {}}}\n'.format(self.number_of_pages)
        for key in self.control_dict.keys():
            all_cfg += self.control_dict[key].get_cfg()
        for key in self.alarm_dict.keys():
            all_cfg += self.alarm_dict[key].get_cfg()
        logging.debug(all_cfg)
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
        self.mqttc.publish(self.data_topic, data)

    def send_data(self, data):
        """Send data to the Dash server.

        Parameters
        ----------
        data : str
            Data to be sent to the server
        """

        logging.debug("Tx: %s", data)
        self.mqttc.publish(self.data_topic, data)


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

    def __init__(
        self, connection_name, device_id, device_name, host='', port=5000, watch_dog=60
    ):
        """
        Arguments:
            connection_name {str} --  The connection name as advertised to iotdashboard.
            device_id {str} -- A string to uniquely identify the device connection. (In case of other connections with the same name.)
            device_name {str} -- A string for iotdashboard to use as an alias for the connection.
            host {str} -- The server name of the mqtt host.
            port {int} -- Port number to connect to.

        Keyword Arguments:
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
        """

        threading.Thread.__init__(self)
        self.control_dict = {}
        self.alarm_dict = {}
        self.number_of_pages = 0
        self.LWD = "OFFLINE"
        self.watch_dog = watch_dog
        self.watch_dog_counter = 1  # If watch_dog is zero don't send anything
        self.running = True
        self.name = connection_name
        self.username = username
        self.name_cntrl = Name(device_name)
        self.device_name = device_name
        self.add_control(self.name_cntrl)
        self.who = "\tWHO\n"
        self.mqttc = mqtt.Client()

        # Assign event callbacks
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_publish = self.__on_publish
        self.mqttc.on_subscribe = self.__on_subscribe
        if ssl:
            self.mqttc.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )
            self.mqttc.tls_insecure_set(False)

        self.control_topic = "{}/{}/{}/control".format(username, connection_name, device_id)
        self.data_topic = "{}/{}/{}/data".format(username, connection_name, device_id)
        self.alarm_topic = "{}/{}/{}/alarm".format(username, connection_name, device_id)
        self.announce_topic = "{}/{}/{}/announce".format(username, connection_name, device_id)
        self.mqttc.on_log = self.__on_log
        self.mqttc.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        self.mqttc.username_pw_set(username, password)
        self.mqttc.connect(host, port)
        self.host = host
        self.port = port
        # Start subscribe, with QoS level 0
        self.mqttc.subscribe(self.control_topic, 0)

    def run(self):
        # Continue the network loop, exit when an error occurs
        rc = 0
        self.watch_dog_counter = 1  # If watch_dog is zero don't send watchdog message.
        self.mqttc.publish(self.announce_topic, "\tCONNECT\t{}\n".format(self.device_name))
        while self.running:
            rc = self.mqttc.loop()
            if rc != 0:
                connect_error = True
                while connect_error:  # Incase the server goes down for a reboot
                    time.sleep(60.0)
                    try:
                        self.mqttc.connect(self.host, self.port)
                        connect_error = False
                    except ConnectionError:
                        connect_error = True
                self.mqttc.subscribe(self.control_topic, 0)
                logging.info("Reconnecting to MQTT")
            self.watch_dog_counter += 1
            if self.watch_dog_counter == (self.watch_dog + 1):
                self.watch_dog_counter = 1
                self.mqttc.publish(self.data_topic, self.who)

        self.mqttc.publish(self.announce_topic, "disconnect")


class MyTCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))

        data_str = str(self.data, "utf-8").rstrip()
        print(data_str)
        reply = ''
        if cntrl_type == "CONNECT":

        elif cntrl_type == "WHO":
            self.mqttc.publish(self.data_topic, self.who)
        elif cntrl_type == "STATUS":
            self.mqttc.publish(self.data_topic, self.__make_status())
        elif cntrl_type == "CFG":
            self.mqttc.publish(self.data_topic, self.__make_cfg())
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write(self.data.upper())


if __name__ == "__main__":
    HOST, PORT = "", 5000

    # Create the server, binding to localhost on port 5000
    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
