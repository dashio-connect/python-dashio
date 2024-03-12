
from __future__ import annotations
import serial
import time
import logging
from enum import Enum
from .schedular import Schedular

logger = logging.getLogger(__name__)


#  TODO In the serial init add AT+CGMM and throw an exception if you don't get a response or the correct response.
#  TODO don't setup LWT unless will topic and message is setup. Remove offlineMessage


class LTE_State(Enum):
    MODULE_STARTUP = 0
    SIM_READY = 1
    LTE_DISCONNECTED = 2
    LTE_CONNECTED = 3
    MODULE_REQ_RESET = 4
    MODULE_RESETTING = 5
    MODULE_REQ_SHUTDOWN = 6
    MODULE_SHUTTING_DOWN = 7
    MODULE_SHUTDOWN = 8


class MQTT_State(Enum):
    MQTT_DISCONNECTED = 0
    MQTT_REQ_CONNECT = 1
    MQTT_CONNECTING = 2
    MQTT_CONNECTED = 5
    MQTT_REQ_DISCONNECT = 6
    MQTT_DISCONNECTING = 7


class GNSS_State(Enum):
    GNSS_OFF = 0
    GNSS_REQ_POWERUP = 1
    GNSS_POWERING_UP = 2
    GNSS_REQ_DATA = 3
    GNSS_REQ_SHUTDOWN = 4
    GNSS_SHUTDOWN = 5


class ERROR_State(Enum):
    ERR_NONE = 0
    ERR_REBOOT = 1
    ERR_STARTUP_TIMEOUT = 2
    ERR_NO_CARRIER_TIMEOUT = 3
    ERR_LTE_CONNECT_FAIL_RESET = 4
    ERR_LTE_DISCONNECT_RESET = 5
    ERR_MQTT_RECONNECT_FAIL_RESET = 6
    ERR_MQTT_CONNECTION_LOST = 7
    ERR_AT_TIMEOUT_RESET = 8


class SIM767X:
    MAX_MESSAGE_LEN = 10000
    CHECK_CONNECTION_INTERVAL_S = 30
    SHUTDOWN_WAIT_S = 10

    on_ok_callback = None
    on_enter_callback = None

    imei = ""  # Use imei as the client ID for MQTT

    on_receive_incoming_message_callback = None
    on_mqtt_connect_callback = None
    on_mqtt_subscribe_callback = None
    on_mqtt_publish_callback = None

    check_connection_second_count = 0
    at_timeout_s = 10
    chars = ""
    incoming_message = False
    more_data_coming = 0

    start_time = time.time()

    tx_message = ""
    rx_message = ""

    at_timeout_s = 10
    at_timer_s = -1
    shut_down_timer_s = -1
    mqtt_reconnect_timer_s = -1
    mqtt_reconnect_fail_counter = 0
    disconnect_timer_s = 0
    run_at_callbacks = False

    lte_state = LTE_State.MODULE_STARTUP
    error_state = ERROR_State.ERR_REBOOT
    mqtt_state = MQTT_State.MQTT_DISCONNECTED

    will_topic = ""
    will_message = ""
    mqtt_is_publishing = False
    pub_topic = ""
    sub_topic = ""
    mqtt_is_subscribing = False
    message_send_id = -1
    last_command = ""  # ??? is this being used anymore
    messages_dict = {}

    username = ""
    password = ""

    gnss_data_callback = None
    gnss_interval = 60
    gnss_one_shot = False
    gnss_interval_timer_s = 0
    gnss_retry_counter = 0
    gnss_state = GNSS_State.GNSS_SHUTDOWN

    def __init__(self, _serial, _network, _apn, _baud_rate):
        self.network = _network
        self.apn = _apn
        self.serial_at = serial.Serial(_serial, _baud_rate)
        self.serial_at.flush()
        sched = Schedular("LTE Connection Schedular")
        sched.add_timer(0.001, 0.0, self.run)
        sched.add_timer(1.0, 0.25, self.run_one_second_module_tasks)
        sched.add_timer(1.0, 0.5, self.run_one_second_mqtt_tasks)
        sched.add_timer(1.0, 0.75, self.run_one_second_gnss_tasks)

    def mqtt_setup(self,  host, port, username, password):
        self.username = username
        self.password = password
        self.host = host
        self.port = port

    def set_callbacks(self, on_mqtt_connect, on_mqtt_subscribe, receive_incoming_message):
        self.on_mqtt_connect_callback = on_mqtt_connect
        self.on_mqtt_subscribe_callback = on_mqtt_subscribe
        self.on_receive_incoming_message_callback = receive_incoming_message

    def subscribe(self, topic):
        self.sub_topic = topic

    def publish_message(self, topic, message):
        if topic not in self.messages_dict.keys():
            self.messages_dict[topic] = message
        else:
            self.messages_dict[topic] += message

    def protected_at_cmd(self, cmd, on_ok_callback, on_enter_callback, timeout_s=10):
        if not self.run_at_callbacks:
            self.on_ok_callback = on_ok_callback
            self.on_enter_callback = on_enter_callback
            self.at_timeout_s = timeout_s
            self.run_at_callbacks = True

            command = f"AT+{cmd}\r\n"
            self.serial_at.write(command.encode())

            return True
        else:
            return False

    def reset_timers(self):
        self.at_timer_s = -1
        self.mqtt_reconnect_timer_s = -1
        self.shut_down_timer_s = -1

        self.mqtt_is_publishing = False
        self.mqtt_is_subscribing = False
        self.mqtt_state = MQTT_State.MQTT_DISCONNECTED
        self.gnss_state = GNSS_State.GNSS_OFF

    def on_mqtt_connected(self):
        self.mqtt_state = MQTT_State.MQTT_CONNECTED

        if self.on_mqtt_connect_callback is not None:
            self.on_mqtt_connect_callback(True, self.error_state)

        self.error_state = ERROR_State.ERR_NONE

    def run(self, cookie):
        self.process_at_commands()
        # Messaging
        if self.mqtt_state == MQTT_State.MQTT_CONNECTED and not self.run_at_callbacks:
            if not self.mqtt_is_subscribing and not self.mqtt_is_publishing and not self.incoming_message:  # Wait for any received message being downloaded.
                if self.sub_topic:
                    self.mqtt_req_subscribe()
                elif self.messages_dict:
                    d_topic = list(self.messages_dict.keys())[0]
                    self.mqtt_request_publish(d_topic, self.messages_dict[d_topic])
        return True

    def process_at_commands(self):
        if self.serial_at.in_waiting > 0:
            if self.more_data_coming > 0:  # Required because we can read the message through AT faster than it may arrive.
                self.read_message(self.more_data_coming)
            else:
                data = ""
                have_message = False
                while self.serial_at.in_waiting > 0 and not have_message:
                    chars_in = self.serial_at.read().decode()
                    if '\n' in chars_in:
                        chars_arr = chars_in.split('\n')
                        self.chars += chars_arr[0]
                        data = self.chars
                        self.chars = ""
                        have_message = True
                        break
                    else:
                        self.chars += chars_in
                        if self.chars.startswith(">"):
                            data = ">"
                            self.chars = ""
                            have_message = True

                data = data.replace('\r', '')

                if (have_message or data.startswith(">")) and data:
                    logger.debug("CMD: %s", data)

                    if data.startswith("OK"):
                        logger.debug('\n')

                        if self.run_at_callbacks:
                            self.run_at_callbacks = False
                            if self.on_ok_callback is not None:
                                self.on_ok_callback()
                    elif data.startswith("ERROR"):
                        self.more_data_coming = 0  # Just in case
                        if self.run_at_callbacks:
                            self.run_at_callbacks = False
                            logger.debug("Callback - Houston - we have a problem ERROR")
                            logger.debug("AT Error")
                    elif data.startswith(">"):
                        if self.run_at_callbacks:
                            if self.on_enter_callback is not None:
                                self.on_enter_callback()
                    else:
                        data_arr = data.split(':')
                        if len(data_arr) > 1:
                            result_str = data_arr[1]
                            result_str = result_str.strip()

                        if data.startswith("+CPIN:"):
                            if result_str.startswith("READY"):  # Module has started up and is ready for AT commands
                                self.run_at_callbacks = False
                                self.lte_state = LTE_State.SIM_READY

                        elif data.startswith("+CREG:") or data.startswith("+CEREG:") or data.startswith("+CGREG:"):  # Network Registration Status
                            result_arr = result_str.split(',')
                            if len(result_arr) == 1:  # Unsolicited response
                                status = int(result_arr[0])
                                if status == 1 or status == 5:
                                    if self.lte_state != LTE_State.LTE_CONNECTED:
                                        self.lte_state = LTE_State.LTE_CONNECTED
                                        self.disconnect_timer_s = 0
                                        self.start_pdp_context()
                            else:  # Request response
                                status = int(result_arr[1])
                                if status == 1 or status == 5:
                                    if self.lte_state != LTE_State.LTE_CONNECTED:
                                        self.lte_state = LTE_State.LTE_CONNECTED
                                        self.disconnect_timer_s = 0
                                        self.start_pdp_context()
                                else:  # Only do this for request response (i.e. when monitoring)
                                    self.lte_state = LTE_State.LTE_DISCONNECTED
                                    self.mqtt_state = MQTT_State.MQTT_DISCONNECTED
                                    self.error_state = ERROR_State.ERR_LTE_CONNECT_FAIL_RESET
                        elif data.startswith("+CGEV:"):
                            if result_str.startswith("ME PDN ACT"):  # AcT = 0 (GSM)
                                logger.debug("ME PDN ACT")
                            elif result_str.startswith("EPS PDN ACT"):  # AcT = 7 (EUTRAN)
                                logger.debug("EPS PDN ACT")
                            elif result_str.startswith("ME PDN DEACT"):
                                logger.debug("ME PDN DEACT")
                            elif result_str.startswith("NW PDN DEACT"):
                                logger.debug("NW PDN DEACT")
                        elif data.startswith("+SIMEI:"):
                            self.imei = "IMEI" + result_str
                        elif data.startswith("+COPS:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 3:
                                logger.debug("Carrier: %s", result_arr[2])
                        # MQTT
                        elif data.startswith("+CMQTTSTART:"):
                            error = int(result_str)
                            if error == 0:
                                self.mqtt_acquire_client()
                            else:
                                logger.debug("MQTT Start: %s", error)
                                self.lte_state = LTE_State.MODULE_REQ_RESET
                        elif data.startswith("+CMQTTCONNECT:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                error = int(result_arr[1])
                                if error == 0:
                                    self.on_mqtt_connected()
                                    self.mqtt_reconnect_fail_counter = 0
                                else:
                                    logger.debug("MQTT Cnct: %s", error)
                                    self.req_mqtt_reconnect()
                        elif data.startswith("+CMQTTSUB:"):
                            self.mqtt_is_subscribing = False
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                error = int(result_arr[1])
                                if self.on_mqtt_subscribe_callback is not None:
                                    self.on_mqtt_subscribe_callback(self.sub_topic, error)

                                if error == 0:
                                    self.sub_topic = ""
                                else:
                                    logger.debug("MQTT Sub: %s", error)
                                    self.req_mqtt_reconnect()
                        elif data.startswith("+CMQTTPUB:"):
                            self.mqttIsPublishing = False
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                error = int(result_arr[1])
                                if error == 0:
                                    if self.pub_topic in self.messages_dict:
                                        del self.messages_dict[self.pub_topic]  # ??? This should really be after successful publish
                                else:
                                    logger.debug("MQTT Pub: %s", error)
                                    self.req_mqtt_reconnect()

                                if self.on_mqtt_publish_callback is not None:
                                    self.on_mqtt_publish_callback(self.pub_topic, self.message_send_id, error)  # Do before topic is cleared below
                                self.messageSendID = -1  # Probably don't need this

                                self.pub_topic = ""
                                self.tx_message = ""
                        elif data.startswith("+CMQTTRXTOPIC:"):
                            # No need to do anything with the received topic as there shoud only be one topic.
                            pass
                        elif data.startswith("+CMQTTRXSTART:"):
                            self.incoming_message = True
                            self.rx_message = ""
                        elif data.startswith("+CMQTTRXPAYLOAD:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                self.read_message(int(result_arr[1]))
                        elif data.startswith("+CMQTTRXEND:"):
                            self.more_data_coming = 0
                            self.incoming_message = False

                            if self.rx_message:
                                if self.on_receive_incoming_message_callback is not None:
                                    self.on_receive_incoming_message_callback(self.rx_message)
                                self.rxMessage = ""
                        elif data.startswith("+CMQTTDISC:"):
                            self.mqtt_state = MQTT_State.MQTT_DISCONNECTED
                            if self.shut_down_timer_s >= 0:
                                self.lte_state = LTE_State.MODULE_REQ_SHUTDOWN
                        elif data.startswith("+CMQTTCONNLOST:"):
                            self.mqtt_state = MQTT_State.MQTT_DISCONNECTED
                            if self.on_mqtt_connect_callback is not None:
                                self.on_mqtt_connect_callback(False, ERROR_State.ERR_MQTT_CONNECTION_LOST)

                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                error = int(result_arr[1])
                                logger.debug("MQTT Cnct Lost: %s", error)
                                self.req_mqtt_reconnect()
                        # GNSS
                        elif data.startswith("+CGNSSINFO:"):
                            self.process_gnss_data(result_str)

    def read_message(self, message_len):
        chars_in = self.serial_at.read().decode()
        self.rx_message += chars_in
        self.more_data_coming = message_len - len(chars_in)

    def run_one_second_module_tasks(self, cookie):
        if self.shut_down_timer_s >= 0:
            logger.debug("Shutdown Ttimers: %ss", self.shut_down_timer_s)
            self.shut_down_timer_s += 1
            if self.shut_down_timer_s == self.SHUTDOWN_WAIT_S:
                self.mqtt_state = MQTT_State.MQTT_REQ_DISCONNECT
            if self.shut_down_timer_s == self.SHUTDOWN_WAIT_S + 5:  # Allow 5 seconds to disconnect before shutdown
                self.shut_down_timer_s = -1  # Turn off timer
                self.lte_state = LTE_State.MODULE_REQ_SHUTDOWN

        # LTE State
        if self.lte_state == LTE_State.MODULE_STARTUP:
            logger.debug("Disconnect Timers: %s.", self.disconnect_timer_s)
            self.disconnect_timer_s += 1
            if self.disconnect_timer_s > 60:  # One min
                self.disconnect_timer_s = 0
                self.run_at_callbacks = False
                self.req_reset_module(ERROR_State.ERR_STARTUP_TIMEOUT)
        elif self.lte_state == LTE_State.SIM_READY:
            self.lte_state = LTE_State.LTE_DISCONNECTED
            self.reset_timers()
            self.disconnect_timer_s = 0

            self.get_imei()
        elif self.lte_state == LTE_State.LTE_DISCONNECTED:
            logger.debug("Disconnect Timers: %s^", self.disconnect_timer_s)
            self.disconnect_timer_s += 1
            if self.disconnect_timer_s > 300:  # Five mins
                self.disconnect_timer_s = 0
                self.req_reset_module(ERROR_State.ERR_NO_CARRIER_TIMEOUT)
        elif self.lte_state == LTE_State.MODULE_REQ_RESET:
            self.reset_module()
        elif self.lte_state == LTE_State.MODULE_REQ_SHUTDOWN:
            self.shutdown_module()

        # Check Connection
        self.check_connection_second_count += 1
        if self.check_connection_second_count > self.CHECK_CONNECTION_INTERVAL_S:
            self.check_connection_second_count = 0
            if self.lte_state == LTE_State.LTE_CONNECTED:
                self.check_connection()

        if self.run_at_callbacks:
            if self.at_timer_s >= 0:  # i.e. -1 is timer turned off
                self.at_timer_s += 1
                if self.at_timer_s > self.at_timeout_s:
                    self.at_timer_s = -1  # Turn off timer
                    self.run_at_callbacks = False
                    logger.debug("Callback - Houston - we have a problem TIMEOUT")
                    self.timeout_error_command = self.last_command
                    self.req_reset_module(ERROR_State.ERR_AT_TIMEOUT_RESET)
        return True

    def run_one_second_mqtt_tasks(self, cookie):
        if self.mqtt_state == MQTT_State.MQTT_REQ_CONNECT:
            self.mqtt_connect()
        elif self.mqtt_state == MQTT_State.MQTT_REQ_DISCONNECT:
            self.mqtt_disconnect()

        if self.mqtt_reconnect_timer_s >= 0:
            self.mqtt_reconnect_timer_s += 1
            logger.debug("mqttReconnectTimers: %sm.", self.mqtt_reconnect_timer_s)
            if self.mqtt_reconnect_timer_s >= 10:
                self.mqtt_reconnect_timer_s = -1  # Turn off timer
                logger.debug("MQTT Reconnect")
                self.req_mqtt_connect()
        return True

    def run_one_second_gnss_tasks(self, cookie):
        if self.gnss_state == GNSS_State.GNSS_REQ_POWERUP:
            self.power_up_gnss()
        elif self.gnss_state == GNSS_State.GNSS_REQ_DATA:
            self.gnss_interval_timer_s += 1
            logger.debug("gnssIntervalTimerS: %s", self.gnss_interval_timer_s)
            if self.gnss_interval_timer_s >= self.gnss_interval:
                self.gnss_interval_timer_s = 0
                self.get_gnss_info()
        elif self.gnss_state == GNSS_State.GNSS_REQ_SHUTDOWN:
            self.power_down_gnss()
        return True

    def power_down_module(self):
        self.lte_state = LTE_State.MODULE_SHUTTING_DOWN
        self.shut_down_timer_s = 0  # Start shutdown counter

    def shutdown_module(self):
        if self.protected_at_cmd("CPOF", lambda: self.reset_timers(), lambda: None, 120):
            self.shut_down_timer_s = -1
            self.lte_state = LTE_State.MODULE_SHUTDOWN

    def req_reset_module(self, error_state):
        self.error_state = error_state
        self.lte_state = LTE_State.MODULE_REQ_RESET

    def reset_module(self):
        if self.protected_at_cmd("CRESET", lambda: self.reset_timers(), lambda: None, 120):
            self.lte_state = LTE_State. MODULE_RESETTING

    def print_ok(self):
        logger.debug("OK ACK")

    def check_connection(self):
        self.protected_at_cmd("CREG?", lambda: self.print_ok(), lambda: None)

    def get_imei(self):
        self.protected_at_cmd("SIMEI?", lambda: self.set_unsolicited_network_reg_messages(), lambda: None)

    def set_unsolicited_network_reg_messages(self):
        self.protected_at_cmd("CREG=1", lambda: self.set_carrier, lambda: None)

    def set_carrier(self):
        if self.network is not None:
            carrier_str = f'AT+COPS=4,2,"{self.network}"'  # 1 = manual (4 = manual/auto), 2 = short format. For One NZ SIM cards not roaming in NZ, Could take up to 60s
            self.serial_at.write(carrier_str.encode())  # ??? Maybe should be protected

    def start_pdp_context(self):
        context_str = f'CGDCONT=1,"IP","{self.apn}"'
        self.protected_at_cmd(context_str, lambda: self.activate_context(), lambda: None)

    def activate_context(self):
        self.protected_at_cmd("CGACT=1,1", lambda: self.get_carrier(), lambda: None)

    def get_carrier(self):
        self.protected_at_cmd("COPS?", lambda: self.mqtt_start(), lambda: None)

# ----- MQTT -----
    def req_mqtt_reconnect(self):
        self.mqtt_is_publishing = False
        self.mqtt_state = MQTT_State.MQTT_DISCONNECTED

        self.mqtt_reconnect_fail_counter += 1
        if self.mqtt_reconnect_fail_counter > 5:  # After 5 tries, go for a reset
            self.mqtt_reconnect_fail_counter = 0
            self.req_reset_module(ERROR_State.ERR_MQTT_RECONNECT_FAIL_RESET)
        else:
            self.mqtt_reconnect_timer_s = 0  # Restart timer

    def mqtt_disconnect(self):
        if self.protected_at_cmd("CMQTTDISC=0,60", lambda: self.print_ok(), lambda: None):  # clientIndex = 0, timeout (force disconnect to attempt to clear out any buffers etc.)
            self.mqtt_state = MQTT_State.MQTT_DISCONNECTING

    def mqtt_start(self):
        self.protected_at_cmd("CMQTTSTART", lambda: self.print_ok(), lambda: None, 60)

    def mqtt_acquire_client(self):
        temp_str = f'CMQTTACCQ=0,"{self.imei}",1'  # clientIndex = 0, cliendID, serverType 1 = SSL/TLS, 0 = TCP
        self.protected_at_cmd(temp_str, lambda: self.mqtt_config_ssl(), lambda: None)

    def mqtt_config_ssl(self):
        self.protected_at_cmd("CMQTTSSLCFG=0,0", lambda: self.mqtt_request_will_toic(), lambda: None)  # sessionID = 0, sslIndex = 0

# ---- MQTT LWT -----

    def mqtt_request_will_toic(self):
        if self.will_message and self.will_topic:
            self.protected_at_cmd(f"CMQTTWILLTOPIC=0,{str(len(self.will_topic))}", lambda: self.mqtt_request_will_message(), lambda: self.mqtt_enter_will_toic())  # clientIndex = 0
        else:
            self.mqtt_connect()

    def mqtt_enter_will_toic(self):
        self.serial_at.write((self.will_topic).encode())

    def mqtt_request_will_message(self):
        temp_str = f'CMQTTWILLMSG=0,{str(len(self.will_message))},2'
        self.protected_at_cmd(temp_str, lambda: self.req_mqtt_connect(), lambda: self.mqtt_enter_will_message())  # clientIndex = 0, qos = 2

    def mqtt_enter_will_message(self):
        self.serial_at.write(self.will_message.encode())

    def req_mqtt_connect(self):
        self.mqtt_state = MQTT_State.MQTT_REQ_CONNECT

# ---- MQTT Connect -----
    def mqtt_connect(self):
        connect_str = f'"CMQTTCONNECT=0,"tcp://{self.host}:{str(self.port)}",60,1,"{self.username}","{self.password}"'
        if self.protected_at_cmd(connect_str, lambda: self.print_ok(), lambda: None, 60):  # Allow 60s for MQTT to connect
            self.mqtt_state = MQTT_State.MQTT_CONNECTING

# ---- MQTT Subscribe -----
    def mqtt_req_subscribe(self):
        if self.protected_at_cmd(f'CMQTTSUB=0,{str(len(self.sub_topic))},2', lambda: self.print_ok(), lambda: self.mqtt_enter_sub_topic()):  # clientIndex = 0
            self.mqtt_is_subscribing = True

    def mqtt_enter_sub_topic(self):
        logger.debug("Sub Topic: %s", self.sub_topic)
        self.serial_at.write(self.sub_topic.encode())

# ----- MQTT Publish ------
    def mqtt_request_publish(self, topic, message):
        self.pub_topic = topic
        self.tx_message = message
        if self.tx_message:
            if self.lte_state == LTE_State.MODULE_SHUTTING_DOWN:
                self.shut_down_timer_s = 0  # Reset shutdown timer as there is a message to send
            if self.protected_at_cmd(f"CMQTTTOPIC=0,{str(len(self.pub_topic))}", lambda: self.mqtt_request_payload(), lambda: self.mqtt_enter_pub_topic()):  # clientIndex = 0
                return True
            else:
                return False
        else:
            return True

    def mqtt_enter_pub_topic(self):
        logger.debug("Pub Topic: %s", self.pub_topic)
        self.serial_at.write(self.pub_topic.encode())

    def mqtt_request_payload(self):
        self.protected_at_cmd(f"CMQTTPAYLOAD=0,{str(len(self.tx_message))}", lambda: self.mqtt_publish(), lambda: self.mqtt_enter_message())  # clientIndex = 0

    def mqtt_enter_message(self):
        logger.debug("Publish Message: %s\n%s", self.pub_topic, self.tx_message)
        self.serial_at.write(self.tx_message.encode())

    def mqtt_publish(self):
        if self.protected_at_cmd("CMQTTPUB=0,2,60", lambda: self.print_ok(), lambda: None):  # clientIndex = 0
            self.mqtt_is_publishing = True  # Block further publishing until publish succeeds or fails.

# --------- GNSS ----------
    def gnss_start(self, interval, one_shot):
        if self.gnss_data_callback is not None:
            self.gnss_interval = interval
            self.gnss_one_shot = one_shot
            self.gnss_state = GNSS_State.GNSS_REQ_POWERUP

    def power_up_gnss(self):
        if self.protected_at_cmd("CGNSSPWR=1", lambda: self.enable_gnss(), lambda: None):
            self.gnss_state = GNSS_State.GNSS_POWERING_UP

    def get_gnss_info(self):
        if self.gnss_state == GNSS_State.GNSS_REQ_DATA:
            self.protected_at_cmd("CGNSSINFO", lambda: self.print_ok(), lambda: None)

    def power_down_gnss(self):
        if self.protected_at_cmd("CGNSSPWR=0", lambda: self.print_ok(), lambda: None):
            self.gnss_state = GNSS_State.GNSS_SHUTDOWN

# GNSS Callbacks
    def enable_gnss(self):
        self.protected_at_cmd("CGPSHOT", lambda: self.set_gnss_ready(), lambda: None)

    def set_gnss_ready(self):
        self.gnss_retry_counter = 0
        self.gnss_state = GNSS_State.GNSS_REQ_DATA

    def process_gnss_data(self, nmea_string):
        if len(nmea_string) < 20:  # Make sure it has sensible data
            if self.gnss_one_shot:
                self.gnss_retry_counter += 1
                if self.gnss_retry_counter >= 5:  # Only try 5 times
                    self.gnss_state = GNSS_State.GNSS_REQ_SHUTDOWN
        else:
            if self.gnss_data_callback is not None:
                self.gnss_data_callback(nmea_string)
                if self.gnss_one_shot:
                    self.gnss_state = GNSS_State.GNSS_REQ_SHUTDOWN
