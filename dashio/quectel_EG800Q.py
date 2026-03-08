"""
MIT License

Copyright (c) 2025 DashIO-Connect

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
import threading
import serial  # type: ignore

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


class EG800Q:
    """EG800Q AT Interface"""
    MAX_MESSAGE_LEN = 10000
    CHECK_CONNECTION_INTERVAL_S = 30
    SHUTDOWN_WAIT_S = 10

    _on_ok_callback = None
    _on_enter_callback = None  # ??? This can be removed

    _imei = ""  # Use imei as the client ID for MQTT

    _on_receive_incoming_message_callback: Callable[[str], None] | None = None
    _on_mqtt_connect_callback: Callable[[bool, ErrorState], None] | None = None
    _on_mqtt_subscribe_callback:  Callable[[str, int], None] | None = None
    on_mqtt_publish_callback: Callable[[str, int, int], None] | None = None

    _check_connection_second_count = 0
    _at_timeout_s = 10
    _char_buffer = ""
    _chars_to_read = 0
    _start_read = False

    start_time = time.time()

    _tx_lines = []
    _tx_message = ""

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
    _will_message = "OFFLINE"
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
        """EG800Q AT Interface

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

    def run(self):
        self.start_serial()
        self._serial_at.flush()
        self._sched = Schedular("LTE Connection Schedular")
        self._sched.add_timer(0.001, 0.0, self._run_processing)
        self._sched.add_timer(1.0, 0.25, self._run_one_second_module_tasks)
        # self._sched.add_timer(1.0, 0.5, self._run_one_second_mqtt_tasks)
        # self._sched.add_timer(1.0, 0.75, self._run_one_second_gnss_tasks)

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
        self._mqtt_subscribe(topic)

    def publish_message(self, topic: str, message: str):
        """Publish a message"""
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
            logger.debug("CMD: %s", command)

            return True
        else:
            return False

    def _custom_at_cmd(self, cmd: str, on_ok_callback: Callable[[], None], on_enter_callback: Callable[[], None] | None, timeout_s: int = 10):
        if not self._run_at_callbacks:
            self._on_ok_callback = on_ok_callback
            self._on_enter_callback = on_enter_callback
            self._at_timeout_s = timeout_s
            self._run_at_callbacks = True

            command = f"AT#{cmd}\r\n"
            self.write_serial_buffer(command.encode())
            logger.debug("CMD: %s", command)

            return True
        else:
            return False

    def _reset_timers(self):
        self._at_timer_s = -1
        self._mqtt_reconnect_timer_s = -1
        self._shut_down_timer_s = -1

        self._mqtt_state = MqttState.MQTT_DISCONNECTED
        self._gnss_state = GnssState.GNSS_OFF

    def _on_mqtt_connected(self):
        self._mqtt_reconnect_fail_counter = 0

        self._mqtt_state = MqttState.MQTT_CONNECTED

        if self._on_mqtt_connect_callback is not None:
            self._on_mqtt_connect_callback(True, self._error_state)

        self._error_state = ErrorState.ERR_NONE

    def _run_processing(self, cookie: Any):
        self._process_at_commands()
        # Messaging
        if self._mqtt_state == MqttState.MQTT_CONNECTED and not self._run_at_callbacks:
            if not self._start_read:  # Wait for any received message being downloaded.
                if self._messages_dict:
                    self._messages_dict_lock.acquire()
                    d_topic = list(self._messages_dict.keys())[0]
                    self._mqtt_publish(d_topic, self._messages_dict[d_topic])
        return True

    def _process_at_commands(self):
        try:
            if self._serial_at.in_waiting > 0:
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

                data = data.replace('\r', '')

                if (have_message) and data:
                    logger.debug("RSP: %s", data)

                    if self._start_read and self._chars_to_read > 0:
                        if len(data) != (self._chars_to_read - 1):  # The /n has already been removed
                            logger.debug("Invalid message length")  # ???
                        elif self._on_receive_incoming_message_callback is not None:
                            self._on_receive_incoming_message_callback(data)
                        self._start_read = False
                        self._chars_to_read = 0
                    elif data.startswith("<<<"):
                        self._start_read = True
                    elif data.startswith("OK"):
                        logger.debug('\n')

                        if self._run_at_callbacks:
                            self._run_at_callbacks = False
                            if self._on_ok_callback is not None:
                                self._on_ok_callback()
                    elif data.startswith("ERROR"):
                        self._start_read = False  # Just in case
                        if self._run_at_callbacks:
                            self._run_at_callbacks = False
                            logger.debug("Callback - Houston - we have a problem ERROR")
                            logger.debug("AT Error")
                    else:
                        data_arr = data.split(':')
                        if len(data_arr) > 1:
                            result_str = data_arr[1]
                            result_str = result_str.strip()

                        if data.startswith("+CPIN:"):
                            if result_str.startswith("READY"):  # Module has started up and is ready for AT commands
                                self.write_serial_buffer("ATE0\r\n".encode())  # Echo off
                                self._run_at_callbacks = False
                                self._lte_state = LteState.SIM_READY

                        elif data.startswith(("+CREG:", "+CEREG:")):  # Network Registration Status
                            result_arr = result_str.split(',')
                            if len(result_arr) == 1:  # Unsolicited response
                                status = int(result_arr[0])
                                if status == 1 or status == 5 or status == 6:
                                    if self._lte_state != LteState.LTE_CONNECTED:
                                        self._lte_state = LteState.LTE_CONNECTED
                                        self._disconnect_timer_s = 0
                                        self._check_apn()
                            else:  # Request response
                                self._run_at_callbacks = False
                                status = int(result_arr[1])
                                if status == 1 or status == 5 or status == 6:
                                    if self._lte_state != LteState.LTE_CONNECTED:
                                        self._lte_state = LteState.LTE_CONNECTED
                                        self._disconnect_timer_s = 0
                                    self._check_apn()
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
                        elif data.startswith("+CGSN:"):
                            self._imei = "IMEI" + result_str
                            logger.debug("Found IMEI: %s", self._imei)
                        elif data.startswith("+COPS:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 3:
                                logger.debug("Carrier: %s", result_arr[2])
                        elif data.startswith("+CGDCONT:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 3:
                                found_apn = result_arr[2].replace('"', '')
                                if int(result_arr[0]) == 1 and result_arr[1] == '"IP"' and found_apn == self._apn:
                                    self._check_pdp_context()
                                else:
                                    self._start_pdp_context()
                        elif data.startswith("#SGACT:"):  # ??? Not used
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                if result_arr[0] == "1" and result_arr[1] == "1":
                                    self._mqtt_check_enbled()
                                else:
                                    self._start_pdp_context()
                        # MQTT
                        elif data.startswith("#MQEN:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 2:
                                if int(result_arr[0]) == 1:
                                    if int(result_arr[1]) == 1:
                                        self._mqtt_check_config()
                                    else:
                                        self._mqtt_enable()
                        elif data.startswith("#MQCFG:"):
                            result_arr = result_str.split(',')
                            if len(result_arr) >= 5:
                                if int(result_arr[0]) == 1:
                                    found_host = result_arr[1].replace('"', '')
                                    if found_host == self._host:
                                        self._mqtt_check_conn_status()
                                    else:
                                        self._mqtt_configure()
                        elif data.startswith("#MQCONN:"):
                            result_arr = result_str.split(',')
                            if int(result_arr[0]) == 1:
                                if result_arr[1].startswith("DISCONNECT"):
                                    self._mqtt_configure_conn()
                                elif result_arr[1] == "0":  # Disconnected
                                    self._mqtt_configure_conn()
                                else:
                                    self._mqtt_check_read()
                        elif data.startswith("#MQREAD:"):
                            result_arr = result_str.replace('"', '').split(',')
                            if int(result_arr[0]) == 1:
                                if len(result_arr) == 2:
                                    num_unread = int(result_arr[1])
                                    if num_unread > 0:
                                        logger.debug("Messages unread: %s", num_unread)  # ???
                                        self._mqtt_read(1, 1)  # Try readin the first slot - but it may be in any slot
                                else:
                                    self._chars_to_read = int(result_arr[2])
                        elif data.startswith("#MQRING:"):
                            result_arr = result_str.replace('"', '').split(',')
                            if len(result_arr) == 1:
                                if int(result_arr[0]) == 0:
                                    logger.debug("MQTT buffer is full - do something drastic")  # ???
                            elif int(result_arr[0]) == 1:
                                logger.debug("Messages incoming")  # ???
                                self._mqtt_read(1, int(result_arr[1]))
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
            # ???self.write_serial_buffer("AT+CGMM\r\n".encode())
            self.write_serial_buffer("AT+CPIN?\r\n".encode())
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
        if self._custom_at_cmd("SHDN", self._reset_timers, None, 120):
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

    def _check_apn(self):
        self._protected_at_cmd("CGDCONT?", self._print_ok, None)

    def _check_pdp_context(self):
        self._custom_at_cmd("SGACT?", self._print_ok, None)

    def _get_imei(self):
        self._protected_at_cmd("CGSN=1", self._set_unsolicited_network_reg_messages, None)

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
        self._custom_at_cmd("SGACT=1,1", self._get_carrier, None)

    def _get_carrier(self):
        self._protected_at_cmd("COPS?", self._mqtt_check_enbled, None)

# ----- MQTT -----
    def _mqtt_check_enbled(self):
        self._custom_at_cmd("MQEN?", self._print_ok, None)

    def _mqtt_enable(self):
        self._custom_at_cmd("MQEN=1,1", self._mqtt_check_enbled, None)

    def _mqtt_check_config(self):
        self._custom_at_cmd("MQCFG?", self._print_ok, None)

    def _mqtt_configure(self):
        temp_str = f'MQCFG=1,"{self._host}",{self._port},1,1,1'
        self._custom_at_cmd(temp_str, self._mqtt_check_conn_status, None)

    def _mqtt_check_conn_status(self):
        self._custom_at_cmd('MQCONN?', self._print_ok, None)

    def _mqtt_configure_conn(self):  # Not bothering checking this one
        self._custom_at_cmd('MQCFG2=1,60,1', self._mqtt_config_lwt, None)  # Keep alive and clean session

    def _mqtt_config_lwt(self):
        if self._will_message and self._will_topic:
            temp_str = f'MQWCFG=1,1,1,2,{self._will_topic},{self._will_message}'
            self._custom_at_cmd(temp_str, self._mqtt_connect, None)
        else:
            self._mqtt_connect()

    def _req_mqtt_reconnect(self):
        logger.debug("MQTT Connect Fail - Reconnect")  # ???
        self._mqtt_state = MqttState.MQTT_DISCONNECTED

        self._mqtt_reconnect_fail_counter += 1
        if self._mqtt_reconnect_fail_counter > 5:  # After 5 tries, go for a reset
            self._mqtt_reconnect_fail_counter = 0
            self._req_reset_module(ErrorState.ERR_MQTT_RECONNECT_FAIL_RESET)
        else:
            self._mqtt_reconnect_timer_s = 0  # Restart timer

    def _mqtt_disconnect(self):
        if self._custom_at_cmd("MQDISC=1", self._print_ok, None):
            self._mqtt_state = MqttState.MQTT_DISCONNECTING

# ---- MQTT Connect -----
    def _mqtt_connect(self):
        connect_str = f'MQCONN=1,{self._imei},{self._username},{self._password}'
        if self._custom_at_cmd(connect_str, self._mqtt_connect_OK, None, 60):  # Allow 60s for MQTT to connect
            self._mqtt_state = MqttState.MQTT_CONNECTING

    def _mqtt_connect_OK(self):
        self._on_mqtt_connected()

# ---- MQTT Subscribe -----
    def _mqtt_subscribe(self, topic: str):
        temp_str = f'MQSUB=1,{topic},2'  # qos = 2
        self._custom_at_cmd(temp_str, self._mqtt_subscribe_OK(topic), None)

    def _mqtt_subscribe_OK(self, topic):
        if self._on_mqtt_subscribe_callback is not None:
            self._on_mqtt_subscribe_callback(topic, self._error_state)

# ----- MQTT Publish ------
    def _mqtt_publish(self, topic: str, message: str):
        logger.debug("MQTT Publish: %s, %s", topic, message)  # ???
        temp_str = f'MQPUBS=1,{topic},0,2,{message}'  # qos = 2
        if self._custom_at_cmd(temp_str, self._mqtt_publish_OK(topic), None):
            if topic in self._messages_dict:
                del self._messages_dict[topic]
                self._messages_dict_lock.release()

    def _mqtt_publish_OK(self, topic):
        if self.on_mqtt_publish_callback is not None:
            self.on_mqtt_publish_callback(topic, "message_send_id", self._error_state)

# ----- MQTT Read ------
    def _mqtt_check_read(self):
        self._custom_at_cmd("MQREAD?", self._print_ok, None)

    def _mqtt_read(self, instance: int, mdl: int):
        temp_str = f'MQREAD={instance},{mdl}'
        self._custom_at_cmd(temp_str, self._print_ok, None)

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
