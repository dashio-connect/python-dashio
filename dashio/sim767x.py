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

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Callable
import textwrap
import threading
import serial

from .schedular import Schedular

logger = logging.getLogger(__name__)


#  TODO In the serial init add AT+CGMM and throw an exception if you don't get a response or the correct response.
#  TODO Need to include hardwired powerup/reset control

class LteState(Enum):
    """LTE STate"""
    MODULE_STARTUP = 0
    SIM_READY = 1
    LTE_DISCONNECTED = 2
    LTE_CONNECTED = 3
    MODULE_REQ_RESET = 4
    MODULE_RESETTING = 5
    MODULE_REQ_SHUTDOWN = 6
    MODULE_SHUTTING_DOWN = 7
    MODULE_SHUTDOWN = 8


class MqttState(Enum):
    """MQTT STate"""
    MQTT_DISCONNECTED = 0
    MQTT_REQ_CONNECT = 1
    MQTT_CONNECTING = 2
    MQTT_CONNECTED = 5
    MQTT_REQ_DISCONNECT = 6
    MQTT_DISCONNECTING = 7


class GnssState(Enum):
    """GNSS State"""
    GNSS_OFF = 0
    GNSS_REQ_POWERUP = 1
    GNSS_POWERING_UP = 2
    GNSS_REQ_DATA = 3
    GNSS_REQ_SHUTDOWN = 4
    GNSS_SHUTDOWN = 5


class ErrorState(Enum):
    """Error State"""
    ERR_NONE = 0
    ERR_REBOOT = 1
    ERR_STARTUP_TIMEOUT = 2
    ERR_NO_CARRIER_TIMEOUT = 3
    ERR_LTE_CONNECT_FAIL_RESET = 4
    ERR_LTE_DISCONNECT_RESET = 5
    ERR_MQTT_RECONNECT_FAIL_RESET = 6
    ERR_MQTT_CONNECTION_LOST = 7
    ERR_AT_TIMEOUT_RESET = 8


class Sim767x:
    """SIM767x AT Interface"""
    MAX_MESSAGE_LEN = 10000
    CHECK_CONNECTION_INTERVAL_S = 30
    SHUTDOWN_WAIT_S = 10

    _on_ok_callback = None
    _on_enter_callback = None

    _imei = ""  # Use imei as the client ID for MQTT

    _on_receive_incoming_message_callback: Callable[[str], None] | None = None
    _on_mqtt_connect_callback: Callable[[bool, ErrorState], None] | None = None
    _on_mqtt_subscribe_callback:  Callable[[str, int], None] | None = None
    on_mqtt_publish_callback: Callable[[str, int, int], None] | None = None

    _check_connection_second_count = 0
    _at_timeout_s = 10
    _char_buffer = ""
    _incoming_message = False
    _more_data_coming = 0

    start_time = time.time()

    _tx_lines = []
    _tx_message = ""
    _rx_message = ""

    _at_timeout_s = 10
    _at_timer_s = -1
    _shut_down_timer_s = -1
    _mqtt_reconnect_timer_s = -1
    _mqtt_reconnect_fail_counter = 0
    _disconnect_timer_s = 0
    _run_at_callbacks = False

    _lte_state = LteState.MODULE_STARTUP
    _error_state = ErrorState.ERR_REBOOT
    _mqtt_state = MqttState.MQTT_DISCONNECTED

    _will_topic = ""
    _will_message = ""
    _mqtt_is_publishing = False
    _pub_topic = ""
    _sub_topic = ""
    _mqtt_is_subscribing = False
    _message_send_id = -1
    _last_command = ""  # ??? is this being used anymore
    _messages_dict = {}
    _messages_dict_lock = threading.Lock()

    _username = ""
    _password = ""

    _gnss_data_callback = None
    _gnss_interval: int = 60
    _gnss_one_shot = False
    _gnss_interval_timer_s = 0
    _gnss_retry_counter = 0
    _gnss_state = GnssState.GNSS_SHUTDOWN

    def __init__(self, serial_port: str, network: str, apn: str, baud_rate: int):
        """SIM767x AT Interface

        Parameters
        ----------
        serial_port : str
            The serial port to use
        network : str
            The network
        apn : str
            The APN
        baud_rate : int
            Baud rate of the Serial connection
        """

        self._serial_port = serial_port
        self._network = network
        self._apn = apn
        self._baud_rate = baud_rate
        self.start_serial()
        self._serial_at.flush()
        self._sched = Schedular("LTE Connection Schedular")
        self._sched.add_timer(0.001, 0.0, self._run_processing)
        self._sched.add_timer(1.0, 0.25, self._run_one_second_module_tasks)
        self._sched.add_timer(1.0, 0.5, self._run_one_second_mqtt_tasks)
        self._sched.add_timer(1.0, 0.75, self._run_one_second_gnss_tasks)

    def start_serial(self):
        self._serial_at = serial.Serial(self._serial_port, self._baud_rate)

    def write_serial_buffer(self, data: bytes, chunk_size=64):
        """
        Writes data to a serial port while preventing buffer overrun.

        Args:
        - data: Data to be written to the serial port.
        - chunk_size: Maximum chunk size to write at a time.
        """
        total_bytes_written = 0
        while total_bytes_written < len(data):
            chunk = data[total_bytes_written: total_bytes_written + chunk_size]
            bytes_written = self._serial_at.write(chunk)
            if bytes_written is not None:
                total_bytes_written += bytes_written
            # Optional: Add a delay if needed between chunks
            time.sleep(0.1)
        return total_bytes_written

    def close(self):
        """Close"""
        self._sched.stop()

    def mqtt_setup(self,  host: str, port: int, username: str, password: str):
        """Set up MQTT Connection

        Parameters
        ----------
        host : str
            Host to connect to
        port : int
            Port to use
        username : str
            username
        password : str
            password
        """
        self._username = username
        self._password = password
        self._host = host
        self._port = port

    @property
    def on_mqtt_connect_callback(self) -> Callable[[bool, ErrorState], None] | None:
        """The callback called when connected to a mqtt host.

        Expected signature is:
            message_callback(bool, ErrorState)
        """
        return self._on_mqtt_connect_callback

    @on_mqtt_connect_callback.setter
    def on_mqtt_connect_callback(self, func: Callable[[bool, ErrorState], None] | None) -> None:
        self._on_mqtt_connect_callback = func

    @property
    def on_mqtt_subscribe_callback(self) -> Callable[[str, int], None] | None:
        """The callback called when a topic is subscribed.

        Expected signature is:
            message_callback(str, ErrorState)
        """
        return self._on_mqtt_subscribe_callback

    @on_mqtt_subscribe_callback.setter
    def on_mqtt_subscribe_callback(self, func: Callable[[str, int], None]) -> None:
        self._on_mqtt_subscribe_callback = func

    @property
    def on_receive_incoming_message_callback(self) -> Callable[[str], None] | None:
        """The callback called when a message has been received on a topic
        that the client subscribes to.

        Expected signature is:
            message_callback(str, ErrorState)
        """
        return self._on_receive_incoming_message_callback

    @on_receive_incoming_message_callback.setter
    def on_receive_incoming_message_callback(self, func:  Callable[[str], None]) -> None:
        self._on_receive_incoming_message_callback = func

    def set_callbacks(self, on_mqtt_connect: Callable[[bool, ErrorState], None], on_mqtt_subscribe: Callable[[str, int], None], receive_incoming_message: Callable[[str], None]):
        """Setup the callbacks

        Parameters
        ----------
        on_mqtt_connect : Callable[[bool, ErrorState], None]
            The callback called when connected to a mqtt host.
        on_mqtt_subscribe : Callable[[str, int], None]
            The callback called when a topic is subscribed.
        receive_incoming_message : Callable[[str], None]
            The callback called when a message has been received on a topic
            that the client subscribes to.
        """
        self._on_mqtt_connect_callback = on_mqtt_connect
        self._on_mqtt_subscribe_callback = on_mqtt_subscribe
        self._on_receive_incoming_message_callback = receive_incoming_message

    def subscribe(self, topic: str):
        """Subscribe to a topic"""
        self._sub_topic = topic

    def publish_message(self, topic: str, message: str):
        """Publis a message"""
        with self._messages_dict_lock:
            if topic not in self._messages_dict:
                self._messages_dict[topic] = message
            else:
                self._messages_dict[topic] += message

    def _protected_at_cmd(self, cmd: str, on_ok_callback: Callable[[], None], on_enter_callback: Callable[[], None] | None, timeout_s: int = 10):
        if not self._run_at_callbacks:
            self._on_ok_callback = on_ok_callback
            self._on_enter_callback = on_enter_callback
            self._at_timeout_s = timeout_s
            self._run_at_callbacks = True

            command = f"AT+{cmd}\r\n"
            self.write_serial_buffer(command.encode())
            # self._serial_at.write(command.encode())

            return True
        else:
            return False

    def _reset_timers(self):
        self._at_timer_s = -1
        self._mqtt_reconnect_timer_s = -1
        self._shut_down_timer_s = -1

        self._mqtt_is_publishing = False
        self._mqtt_is_subscribing = False
        self._mqtt_state = MqttState.MQTT_DISCONNECTED
        self._gnss_state = GnssState.GNSS_OFF

    def _on_mqtt_connected(self):
        self._mqtt_state = MqttState.MQTT_CONNECTED

        if self._on_mqtt_connect_callback is not None:
            self._on_mqtt_connect_callback(True, self._error_state)

        self._error_state = ErrorState.ERR_NONE

    def _run_processing(self, cookie: Any):
        self._process_at_commands()
        # Messaging
        if self._mqtt_state == MqttState.MQTT_CONNECTED and not self._run_at_callbacks:
            if not self._mqtt_is_subscribing and not self._mqtt_is_publishing and not self._incoming_message:  # Wait for any received message being downloaded.
                if self._sub_topic:
                    self._mqtt_req_subscribe()
                if self._messages_dict:
                    self._messages_dict_lock.acquire()
                    d_topic = list(self._messages_dict.keys())[0]
                    self._mqtt_request_publish(d_topic, self._messages_dict[d_topic])
        return True

    def _process_at_commands(self):
        try:
            if self._serial_at.in_waiting > 0:
                if self._more_data_coming > 0:  # Required because we can read the message through AT faster than it may arrive.
                    self._read_message(self._more_data_coming)
                else:
                    data = ""
                    have_message = False
                    result_str = ""
                    while self._serial_at.in_waiting > 0 and not have_message:
                        chars_in = self._serial_at.read().decode()
                        if '\n' in chars_in:
                            chars_arr = chars_in.split('\n')
                            self._char_buffer += chars_arr[0]
                            data = self._char_buffer
                            self._char_buffer = ""
                            have_message = True
                            break
                        self._char_buffer += chars_in
                        if self._char_buffer.startswith(">"):
                            data = ">"
                            self._char_buffer = ""
                            have_message = True

                    data = data.replace('\r', '')

                    if (have_message or data.startswith(">")) and data:
                        logger.debug("CMD: %s", data)

                        if data.startswith("OK"):
                            logger.debug('\n')

                            if self._run_at_callbacks:
                                self._run_at_callbacks = False
                                if self._on_ok_callback is not None:
                                    self._on_ok_callback()
                        elif data.startswith("ERROR"):
                            self._more_data_coming = 0  # Just in case
                            if self._run_at_callbacks:
                                self._run_at_callbacks = False
                                logger.debug("Callback - Houston - we have a problem ERROR")
                                logger.debug("AT Error")
                        elif data.startswith(">"):
                            if self._run_at_callbacks:
                                if self._on_enter_callback is not None:
                                    self._on_enter_callback()
                        else:
                            data_arr = data.split(':')
                            if len(data_arr) > 1:
                                result_str = data_arr[1]
                                result_str = result_str.strip()

                            if data.startswith("+CPIN:"):
                                if result_str.startswith("READY"):  # Module has started up and is ready for AT commands
                                    self._run_at_callbacks = False
                                    self._lte_state = LteState.SIM_READY

                            elif data.startswith("SIM7672G"):
                                self._run_at_callbacks = False
                                self._lte_state = LteState.SIM_READY

                            elif data.startswith(("+CREG:", "+CEREG:", "+CGREG:")):  # Network Registration Status
                                result_arr = result_str.split(',')
                                if len(result_arr) == 1:  # Unsolicited response
                                    status = int(result_arr[0])
                                    if status == 1 or status == 5 or status == 6:
                                        if self._lte_state != LteState.LTE_CONNECTED:
                                            self._lte_state = LteState.LTE_CONNECTED
                                            self._disconnect_timer_s = 0
                                            self._start_pdp_context()
                                else:  # Request response
                                    self._run_at_callbacks = False
                                    status = int(result_arr[1])
                                    if status == 1 or status == 5 or status == 6:
                                        if self._lte_state != LteState.LTE_CONNECTED:
                                            self._lte_state = LteState.LTE_CONNECTED
                                            self._disconnect_timer_s = 0
                                        self._check_pdp_context()
                                    else:  # Only do this for request response (i.e. when monitoring)
                                        self._lte_state = LteState.LTE_DISCONNECTED
                                        self._mqtt_state = MqttState.MQTT_DISCONNECTED
                                        self._error_state = ErrorState.ERR_LTE_CONNECT_FAIL_RESET
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
                                self._imei = "IMEI" + result_str
                            elif data.startswith("+COPS:"):
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 3:
                                    logger.debug("Carrier: %s", result_arr[2])
                            elif data.startswith("+CGACT:"):
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 2:
                                    if result_arr[0] == "1":  # pdp context 0
                                        if result_arr[0] == "1":
                                            self._check_MQTT_client()
                                        else:
                                            self._start_pdp_context()
                            # MQTT
                            elif data.startswith("+CMQTTACCQ:"):
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 3:
                                    if result_arr[0] == "0":  # clientIndex 0
                                        if result_arr[1] and (self._imei in result_arr[1]):
                                            if (self._mqtt_state == MqttState.MQTT_DISCONNECTED):
                                                logger.debug("MQTT already connected - will reset module")
                                                self.reset_module()
                                        else:
                                            self._mqtt_start()
                            elif data.startswith("+CMQTTSTART:"):
                                error = int(result_str)
                                if error == 0:
                                    self._mqtt_acquire_client()
                                else:
                                    logger.debug("MQTT Start: %s", error)
                                    self._lte_state = LteState.MODULE_REQ_RESET
                            elif data.startswith("+CMQTTCONNECT:"):
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 2:
                                    error = int(result_arr[1])
                                    if error == 0:
                                        self._on_mqtt_connected()
                                        self._mqtt_reconnect_fail_counter = 0
                                    else:
                                        logger.debug("MQTT Cnct: %s", error)
                                        self._req_mqtt_reconnect()
                            elif data.startswith("+CMQTTSUB:"):
                                self._mqtt_is_subscribing = False
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 2:
                                    error = int(result_arr[1])
                                    if self._on_mqtt_subscribe_callback is not None:
                                        self._on_mqtt_subscribe_callback(self._sub_topic, error)

                                    if error == 0:
                                        self._sub_topic = ""
                                    else:
                                        logger.debug("MQTT Sub: %s", error)
                                        self._req_mqtt_reconnect()
                            elif data.startswith("+CMQTTPUB:"):
                                self._mqtt_is_publishing = False
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 2:
                                    error = int(result_arr[1])
                                    if error == 0:
                                        if self._pub_topic in self._messages_dict:
                                            del self._messages_dict[self._pub_topic]
                                            self._messages_dict_lock.release()
                                        if self.mqtt_is_finished():
                                            self._pub_topic = ""
                                            self._tx_message = ""
                                    else:
                                        logger.debug("MQTT Pub: %s", error)
                                        self._req_mqtt_reconnect()
                                        self._pub_topic = ""
                                        self._tx_message = ""

                                    if self.on_mqtt_publish_callback is not None:
                                        self.on_mqtt_publish_callback(self._pub_topic, self._message_send_id, error)  # Do before topic is cleared below
                                    self._message_send_id = -1  # Probably don't need this
                            elif data.startswith("+CMQTTRXTOPIC:"):
                                # No need to do anything with the received topic as there shoud only be one topic.
                                pass
                            elif data.startswith("+CMQTTRXSTART:"):
                                self._incoming_message = True
                                self._rx_message = ""
                            elif data.startswith("+CMQTTRXPAYLOAD:"):
                                result_arr = result_str.split(',')
                                if len(result_arr) >= 2:
                                    self._read_message(int(result_arr[1]))
                            elif data.startswith("+CMQTTRXEND:"):
                                self._more_data_coming = 0
                                self._incoming_message = False

                                if self._rx_message:
                                    if self._on_receive_incoming_message_callback is not None:
                                        self._on_receive_incoming_message_callback(self._rx_message)
                                    self._rx_message = ""
                            elif data.startswith("+CMQTTDISC:"):
                                self._mqtt_state = MqttState.MQTT_DISCONNECTED
                                if self._shut_down_timer_s >= 0:
                                    self._lte_state = LteState.MODULE_REQ_SHUTDOWN
                            elif data.startswith("+CMQTTCONNLOST:"):
                                self._mqtt_state = MqttState.MQTT_DISCONNECTED
                                if self._on_mqtt_connect_callback is not None:
                                    self._on_mqtt_connect_callback(False, ErrorState.ERR_MQTT_CONNECTION_LOST)

                                result_arr = result_str.split(',')
                                if len(result_arr) >= 2:
                                    error = int(result_arr[1])
                                    logger.debug("MQTT Cnct Lost: %s", error)
                                    self._req_mqtt_reconnect()
                            # GNSS
                            elif data.startswith("+CGNSSINFO:"):
                                self._process_gnss_data(result_str)
        except serial.SerialException:
            logger.debug("Lost Serial Connection, will try again")
            self._serial_at.close()
            time.sleep(2)

            self._serial_at.open()
            self._reset_timers()
            self._lte_state = LteState.MODULE_STARTUP
            self._check_connection()

    def _read_message(self, message_len: int):
        chars_in = self._serial_at.read().decode()
        self._rx_message += chars_in
        self._more_data_coming = message_len - len(chars_in)

    def _run_one_second_module_tasks(self, cookie: Any):
        if self._shut_down_timer_s >= 0:
            logger.debug("Shutdown Timer: %ss", self._shut_down_timer_s)
            self._shut_down_timer_s += 1
            if self._shut_down_timer_s == self.SHUTDOWN_WAIT_S:
                self._mqtt_state = MqttState.MQTT_REQ_DISCONNECT
            if self._shut_down_timer_s == self.SHUTDOWN_WAIT_S + 5:  # Allow 5 seconds to disconnect before shutdown
                self._shut_down_timer_s = -1  # Turn off timer
                self._lte_state = LteState.MODULE_REQ_SHUTDOWN

        # LTE State
        if self._lte_state == LteState.MODULE_STARTUP:
            self.write_serial_buffer("AT+CGMM\r\n".encode())
            logger.debug("Startup Timer: %s.", self._disconnect_timer_s)
            self._disconnect_timer_s += 1
            if self._disconnect_timer_s > 60:  # One min
                self._disconnect_timer_s = 0
                self._run_at_callbacks = False
                self._req_reset_module(ErrorState.ERR_STARTUP_TIMEOUT)
        elif self._lte_state == LteState.SIM_READY:
            self._lte_state = LteState.LTE_DISCONNECTED
            self._reset_timers()
            self._disconnect_timer_s = 0

            self._get_imei()
        elif self._lte_state == LteState.LTE_DISCONNECTED:
            logger.debug("MQTT Disconnected Timer: %s^", self._disconnect_timer_s)
            self._disconnect_timer_s += 1
            if self._disconnect_timer_s > 300:  # Five mins
                self._disconnect_timer_s = 0
                self._req_reset_module(ErrorState.ERR_NO_CARRIER_TIMEOUT)
        elif self._lte_state == LteState.MODULE_REQ_RESET:
            self.reset_module()
        elif self._lte_state == LteState.MODULE_REQ_SHUTDOWN:
            self.shutdown_module()

        # Check Connection
        self._check_connection_second_count += 1
        if self._check_connection_second_count > self.CHECK_CONNECTION_INTERVAL_S:
            self._check_connection_second_count = 0
            if self._lte_state == LteState.LTE_CONNECTED:
                self._check_connection()

        if self._run_at_callbacks:
            if self._at_timer_s >= 0:  # i.e. -1 is timer turned off
                self._at_timer_s += 1
                if self._at_timer_s > self._at_timeout_s:
                    self._at_timer_s = -1  # Turn off timer
                    self._run_at_callbacks = False
                    logger.debug("Callback - Houston - we have a problem TIMEOUT")
                    self.timeout_error_command = self._last_command
                    self._req_reset_module(ErrorState.ERR_AT_TIMEOUT_RESET)
        return True

    def _run_one_second_mqtt_tasks(self, cookie: Any):
        if self._mqtt_state == MqttState.MQTT_REQ_CONNECT:
            self._mqtt_connect()
        elif self._mqtt_state == MqttState.MQTT_REQ_DISCONNECT:
            self._mqtt_disconnect()

        if self._mqtt_reconnect_timer_s >= 0:
            self._mqtt_reconnect_timer_s += 1
            logger.debug("mqttReconnectTimers: %sm.", self._mqtt_reconnect_timer_s)
            if self._mqtt_reconnect_timer_s >= 10:
                self._mqtt_reconnect_timer_s = -1  # Turn off timer
                logger.debug("MQTT Reconnect")
                self._req_mqtt_connect()
        return True

    def _run_one_second_gnss_tasks(self, cookie: Any):
        if self._gnss_state == GnssState.GNSS_REQ_POWERUP:
            self._power_up_gnss()
        elif self._gnss_state == GnssState.GNSS_REQ_DATA:
            self._gnss_interval_timer_s += 1
            logger.debug("gnssIntervalTimerS: %s", self._gnss_interval_timer_s)
            if self._gnss_interval_timer_s >= self._gnss_interval:
                self._gnss_interval_timer_s = 0
                self._get_gnss_info()
        elif self._gnss_state == GnssState.GNSS_REQ_SHUTDOWN:
            self._power_down_gnss()
        return True

    def power_down_module(self):
        """Power down the module"""
        self._lte_state = LteState.MODULE_SHUTTING_DOWN
        self._shut_down_timer_s = 0  # Start shutdown counter

    def shutdown_module(self):
        """Shutdown the module"""
        if self._protected_at_cmd("CPOF", self._reset_timers, None, 120):
            self._shut_down_timer_s = -1
            self._lte_state = LteState.MODULE_SHUTDOWN

    def _req_reset_module(self, error_state: ErrorState):
        self._error_state = error_state
        self._lte_state = LteState.MODULE_REQ_RESET

    def reset_module(self):
        """Reset Module"""
        if self._protected_at_cmd("CRESET", self._reset_timers, None, 120):
            self._lte_state = LteState. MODULE_RESETTING

    def _print_ok(self):
        logger.debug("OK ACK")

    def _check_connection(self):
        self._protected_at_cmd("CREG?", self._print_ok, None)

    def _check_pdp_context(self):
        self._protected_at_cmd("CGACT?", self._print_ok, None)

    def _check_MQTT_client(self):
        self._protected_at_cmd("CMQTTACCQ?", self._print_ok, None)

    def _get_imei(self):
        self._protected_at_cmd("SIMEI?", self._set_unsolicited_network_reg_messages, None)

    def _set_unsolicited_network_reg_messages(self):
        self._protected_at_cmd("CREG=1", self._get_network_reg_status, None)

    def _get_network_reg_status(self):
        self._protected_at_cmd("CREG?", self._set_carrier, None)

    def _set_carrier(self):
        if self._network:
            carrier_str = f'AT+COPS=4,2,"{self._network}\r\n"'  # 1 = manual (4 = manual/auto), 2 = short format. For One NZ SIM cards not roaming in NZ, Could take up to 60s
            self.write_serial_buffer(carrier_str.encode())  # ??? Maybe should be protected

    def _start_pdp_context(self):
        context_str = f'CGDCONT=1,"IP","{self._apn}"'
        self._protected_at_cmd(context_str, self._activate_context, None)

    def _activate_context(self):
        self._protected_at_cmd("CGACT=1,1", self._get_carrier, None)

    def _get_carrier(self):
        self._protected_at_cmd("COPS?", self._mqtt_start, None)

# ----- MQTT -----
    def _req_mqtt_reconnect(self):
        self._mqtt_is_publishing = False
        self._mqtt_state = MqttState.MQTT_DISCONNECTED

        self._mqtt_reconnect_fail_counter += 1
        if self._mqtt_reconnect_fail_counter > 5:  # After 5 tries, go for a reset
            self._mqtt_reconnect_fail_counter = 0
            self._req_reset_module(ErrorState.ERR_MQTT_RECONNECT_FAIL_RESET)
        else:
            self._mqtt_reconnect_timer_s = 0  # Restart timer

    def _mqtt_disconnect(self):
        if self._protected_at_cmd("CMQTTDISC=0,60", self._print_ok, None):  # clientIndex = 0, timeout (force disconnect to attempt to clear out any buffers etc.)
            self._mqtt_state = MqttState.MQTT_DISCONNECTING

    def _mqtt_start(self):
        self._protected_at_cmd("CMQTTSTART", self._print_ok, None, 60)

    def _mqtt_acquire_client(self):
        temp_str = f'CMQTTACCQ=0,{self._imei},1'  # clientIndex = 0, cliendID, serverType 1 = SSL/TLS, 0 = TCP
        self._protected_at_cmd(temp_str, self._mqtt_config_ssl, None)

    def _mqtt_config_ssl(self):
        self._protected_at_cmd("CMQTTSSLCFG=0,0", self._mqtt_request_will_toic, None)  # sessionID = 0, sslIndex = 0

# ---- MQTT LWT -----

    def _mqtt_request_will_toic(self):
        if self._will_message and self._will_topic:
            self._protected_at_cmd(f"CMQTTWILLTOPIC=0,{str(len(self._will_topic))}", self._mqtt_request_will_message, self._mqtt_enter_will_toic)  # clientIndex = 0
        else:
            self._mqtt_connect()

    def _mqtt_enter_will_toic(self):
        self.write_serial_buffer(self._will_topic.encode())
        # self._serial_at.write(self._will_topic.encode())

    def _mqtt_request_will_message(self):
        temp_str = f'CMQTTWILLMSG=0,{str(len(self._will_message))},2'
        self._protected_at_cmd(temp_str, self._req_mqtt_connect, self._mqtt_enter_will_message)  # clientIndex = 0, qos = 2

    def _mqtt_enter_will_message(self):
        self.write_serial_buffer(self._will_topic.encode())
        # self._serial_at.write(self._will_message.encode())

    def _req_mqtt_connect(self):
        self._mqtt_state = MqttState.MQTT_REQ_CONNECT

# ---- MQTT Connect -----
    def _mqtt_connect(self):
        connect_str = f'CMQTTCONNECT=0,"tcp://{self._host}:{str(self._port)}",60,1,"{self._username}","{self._password}"'
        if self._protected_at_cmd(connect_str, self._print_ok, None, 60):  # Allow 60s for MQTT to connect
            self._mqtt_state = MqttState.MQTT_CONNECTING

# ---- MQTT Subscribe -----
    def _mqtt_req_subscribe(self):
        if self._protected_at_cmd(f'CMQTTSUB=0,{str(len(self._sub_topic))},2', self._print_ok, self._mqtt_enter_sub_topic):  # clientIndex = 0
            self._mqtt_is_subscribing = True

    def _mqtt_enter_sub_topic(self):
        logger.debug("Sub Topic: %s", self._sub_topic)
        self.write_serial_buffer(self._sub_topic.encode())
        # self._serial_at.write(self._sub_topic.encode())

# ----- MQTT Publish ------
    def _mqtt_request_publish(self, topic: str, message: str):
        self._pub_topic = topic

        if len(message) > 380:
            self._tx_lines = textwrap.wrap(message, width=380, replace_whitespace=False,  drop_whitespace=False, expand_tabs=False)
            self._tx_message = self._tx_lines.pop(0)
        else:
            self._tx_message = message

        if self._tx_message:
            if self._lte_state == LteState.MODULE_SHUTTING_DOWN:
                self._shut_down_timer_s = 0  # Reset shutdown timer as there is a message to send
            self._protected_at_cmd(f"CMQTTTOPIC=0,{str(len(self._pub_topic))}", self._mqtt_request_payload, self._mqtt_enter_pub_topic)  # clientIndex = 0

    def _mqtt_enter_pub_topic(self):
        logger.debug("Pub Topic: %s", self._pub_topic)
        self.write_serial_buffer(self._pub_topic.encode())
        #  self._serial_at.write(self._pub_topic.encode())

    def _mqtt_request_payload(self):
        self._protected_at_cmd(f"CMQTTPAYLOAD=0,{str(len(self._tx_message))}", self._mqtt_publish, self._mqtt_enter_message)  # clientIndex = 0

    def _mqtt_enter_message(self):
        logger.debug("Publish Message: %s\n%s", self._pub_topic, self._tx_message)
        self.write_serial_buffer(self._tx_message.encode())
        #  self._serial_at.write(self._tx_message.encode())

    def _mqtt_publish(self):
        if self._protected_at_cmd("CMQTTPUB=0,2,60", self._print_ok, None):  # clientIndex = 0
            self._mqtt_is_publishing = True  # Block further publishing until publish succeeds or fails.

    def mqtt_is_finished(self):
        if len(self._tx_lines) > 0:
            self.tx_message = self._tx_lines.pop(0)
            self._protected_at_cmd(f"CMQTTTOPIC=0,{str(len(self._pub_topic))}", self._mqtt_request_payload, self._mqtt_enter_pub_topic)  # clientIndex = 0
            return False
        return True

# --------- GNSS ----------
    def gnss_start(self, interval: int, one_shot: bool):
        """Start GNSS

        Parameters
        ----------
        interval : int
            Interval in secs ?
        one_shot : bool
            If oneshot.
        """
        if self._gnss_data_callback is not None:
            self._gnss_interval = interval
            self._gnss_one_shot = one_shot
            self._gnss_state = GnssState.GNSS_REQ_POWERUP

    def _power_up_gnss(self):
        if self._protected_at_cmd("CGNSSPWR=1", self._enable_gnss, None):
            self._gnss_state = GnssState.GNSS_POWERING_UP

    def _get_gnss_info(self):
        if self._gnss_state == GnssState.GNSS_REQ_DATA:
            self._protected_at_cmd("CGNSSINFO", self._print_ok, None)

    def _power_down_gnss(self):
        if self._protected_at_cmd("CGNSSPWR=0", self._print_ok, None):
            self._gnss_state = GnssState.GNSS_SHUTDOWN

# GNSS Callbacks
    def _enable_gnss(self):
        self._protected_at_cmd("CGPSHOT", self._set_gnss_ready, None)

    def _set_gnss_ready(self):
        self._gnss_retry_counter = 0
        self._gnss_state = GnssState.GNSS_REQ_DATA

    def _process_gnss_data(self, nmea_string: str):
        if len(nmea_string) < 20:  # Make sure it has sensible data
            if self._gnss_one_shot:
                self._gnss_retry_counter += 1
                if self._gnss_retry_counter >= 5:  # Only try 5 times
                    self._gnss_state = GnssState.GNSS_REQ_SHUTDOWN
        else:
            if self._gnss_data_callback is not None:
                self._gnss_data_callback(nmea_string)
                if self._gnss_one_shot:
                    self._gnss_state = GnssState.GNSS_REQ_SHUTDOWN
