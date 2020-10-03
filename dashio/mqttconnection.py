import threading
import time
import paho.mqtt.client as mqtt
import ssl
import logging
from .iotcontrol.alarm import Alarm
from .iotcontrol.page import Page

# TODO: Add documentation


class mqttConnectionThread(threading.Thread):
    """Setups and manages a connection thread to the Dash Server."""

    def __on_connect(self, client, userdata, flags, rc):
        logging.debug("rc: %s", str(rc))

    def __on_message(self, client, obj, msg):
        data = str(msg.payload, "utf-8").strip()
        logging.debug("MQTT RX: %s", data)
        data_array = data.split("\t")
        cntrl_type = data_array[0]
        if cntrl_type == "CONNECT":
            self.send_data("\tCONNECT\t{}\t{}\t{}\n".format(self.name_cntrl.control_id, self.device_id, self.connection_id))
        elif cntrl_type == "WHO":
            self.send_data(self.who)
        elif cntrl_type == "STATUS":
            self.send_data(self.__make_status())
        elif cntrl_type == "CFG":
            self.send_data(self.__make_cfg())
        elif cntrl_type == "NAME":
            self.name_cntrl.message_rx_event(data_array[1:])
        else:
            try:
                try:
                    key = cntrl_type + "_" + data_array[1]
                except IndexError:
                    return
                self.control_dict[key].message_rx_event(data_array[2:])
            except KeyError:
                pass

    def __on_publish(self, client, obj, mid):
        self.watch_dog_counter = 1

    def __on_subscribe(self, client, obj, mid, granted_qos):
        logging.debug("Subscribed: %s %s", str(mid), str(granted_qos))

    def __on_log(self, client, obj, level, string):
        logging.debug(string)

    def __make_status(self):
        all_status = ""
        for key in self.control_dict.keys():
            all_status += self.control_dict[key].get_state()
        return all_status

    def __make_cfg(self):
        all_cfg = '\tCFG\tDVCE\t{{"numPages": {}}}\n'.format(self.number_of_pages)
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
        logging.debug("MQTT Tx: %s", data.rstrip())
        self.mqttc.publish(self.data_topic, data)

    def send_data(self, data):
        """Send data to the Dash server.

        Parameters
        ----------
        data : str
            Data to be sent to the server
        """

        logging.debug("MQTT Tx: %s", data.rstrip())
        self.mqttc.publish(self.data_topic, data)

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
        self.mqttc.publish(self.alarm_topic, payload)

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
        self, connection_id, device_id, name_control, host, port, username, password, use_ssl=False, watch_dog=60
    ):
        """
        Arguments:
            connection_id {str} --  The connection name as advertised to iotdashboard.
            device_id {str} -- A string to uniquely identify the device connection. (In case of other connections with the same name.)
            device_name {str} -- A string for iotdashboard to use as an alias for the connection.
            host {str} -- The server name of the mqtt host.
            port {int} -- Port number to connect to.
            username {str} -- username for the mqtt connection.
            password {str} -- password for the mqtt connection.

        Keyword Arguments:
            use_ssl {bool} -- Whether to use ssl for the connection or not. (default: {False})
            watch_dog {int} -- Time in seconds between watch dog signals to iotdashboard.
                               Set to 0 to not send watchdog signal. (default: {60})
        """

        threading.Thread.__init__(self, daemon=True)
        self.control_dict = {}
        self.alarm_dict = {}
        self.number_of_pages = 0
        self.LWD = "OFFLINE"
        self.watch_dog = watch_dog
        self.watch_dog_counter = 1  # If watch_dog is zero don't send anything
        self.running = True
        self.username = username
        self.name_cntrl = name_control
        self.connection_id = connection_id
        self.add_control(self.name_cntrl)
        self.who = "\tWHO\n"
        self.mqttc = mqtt.Client()

        # Assign event callbacks
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_publish = self.__on_publish
        self.mqttc.on_subscribe = self.__on_subscribe
        if use_ssl:
            self.mqttc.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )
            self.mqttc.tls_insecure_set(False)

        self.control_topic = "{}/{}/{}/control".format(username, connection_id, device_id)
        self.data_topic = "{}/{}/{}/data".format(username, connection_id, device_id)
        self.alarm_topic = "{}/{}/{}/alarm".format(username, connection_id, device_id)
        self.announce_topic = "{}/{}/{}/announce".format(username, connection_id, device_id)
        self.mqttc.on_log = self.__on_log
        self.mqttc.will_set(self.data_topic, self.LWD, qos=1, retain=False)
        # Connect
        self.mqttc.username_pw_set(username, password)
        self.mqttc.connect(host, port)
        self.host = host
        self.port = port
        self.device_id = device_id
        # Start subscribe, with QoS level 0
        self.mqttc.subscribe(self.control_topic, 0)

    def run(self):
        # Continue the network loop, exit when an error occurs
        rc = 0
        self.watch_dog_counter = 1  # If watch_dog is zero don't send watchdog message.
        self.mqttc.publish(self.announce_topic, "\tCONNECT\t{}\n".format(self.name_cntrl.control_id))
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
