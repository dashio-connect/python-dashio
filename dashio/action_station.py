"""action_station.py

Copyright (c) 2022, DashIO-Connect

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
import json
import logging
import threading
import time
import sys
import shortuuid
import zmq


from .constants import CONNECTION_PUB_URL, MEMORY_REQ_URL, TASK_PULL
from .action_station_services.task_service import TaskService
from .action_station_services.timer_service import TimerService, make_timer_config
from .action_station_services.as_servicel import make_test_config
from .action_station_services.modbus_service import ModbusService, make_modbus_config
from .action_station_services.clock_servicel import ClockService, make_clock_config
from .load_config import CONTROL_INSTANCE_DICT, CONFIG_INSTANCE_DICT, decode_cfg64, encode_cfg64


class ActionStation(threading.Thread):
    """_summary_

    Parameters
    ----------
    threading : _type_
        _description_
    """
    def _service_actn_commands(self, payload: bytearray, msg_from: bytearray):
        data = str(payload, "utf-8").strip()
        data_array = data.split("\t")
        try:
            command = data_array[2]
        except (KeyError, IndexError):
            return
        if command in self._action_station_commands:
            reply = self._action_station_commands[command](data_array)
            self.tx_zmq_pub.send_multipart([msg_from, reply.encode()])

    def save_action(self, filename: str, actions_dict: dict):
        """_summary_

        Parameters
        ----------
        filename : str
            Save the Actions
        """
        with open(filename, 'w', encoding='ASCII') as outfile:
            json.dump(actions_dict, outfile, indent=4)

    def load_action(self, filename: str):
        """load action_station from a file.

        Parameters
        ----------
        filename : str
            Filename of the file where the Actions are stored.
        """
        action_station_dict = {}
        try:
            with open(filename, 'r', encoding='ASCII') as infile:
                action_station_dict = json.load(infile)

        except FileNotFoundError:
            pass
        return action_station_dict

    def register_connection(self, connection):
        """Cennections register here"""
        if connection.zmq_connection_uuid not in self.connections_list:
            logging.debug("AS REG CONNECTION")
            self.connections_list.append(connection.zmq_connection_uuid)
            self.connection_zmq_sub.connect(CONNECTION_PUB_URL.format(id=connection.zmq_connection_uuid))
            connection.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
            self._connect_all_ext_devices()

    def _rm_old_action_station_gui_controls(self):
        old_controls = self._action_station_layout
        if old_controls is not None:
            old_cfg_dict = decode_cfg64(old_controls["provisioning"])
            for control_type, control_list in old_cfg_dict.items():
                if isinstance(control_list, list):
                    for control in control_list:
                        logging.debug("Deleting: %s, %s", control_type, control['controlID'])
                        key = f"{control_type}\t{control['controlID']}"
                        try:
                            del self.device.control_dict[key]
                            if control_type == 'DVVW':
                                self.device.number_of_device_views = self.device.number_of_device_views - 1
                        except KeyError:
                            logging.debug("Error deleting control: %s, %s", control_type, control['controlID'])

    def _delete_gui_configs(self, cfg_dict: dict):
        modified = False
        for control_type, control_list in cfg_dict.items():
            if isinstance(control_list, list):
                for control in control_list:
                    key = f"{control_type}\t{control['controlID']}"
                    if self.device.is_control_loaded(control_type, control['controlID']):
                        modified = True
                        logging.debug("Deleting layouts: %s, %s", control_type, control['controlID'])
                        try:
                            self.device.control_dict[key].del_configs_columnar()
                        except KeyError:
                            logging.debug("Error deleting layout: %s, %s", control_type, control['controlID'])
        return modified

    def _update_gui_controls(self, cfg_dict: dict):
        new_cfg_dict = {}
        new_cfg_dict["CFG"] = self.device._cfg
        added_control_ids = []
        modified = False
        for control_type, control_list in cfg_dict.items():
            if isinstance(control_list, list):
                for control in control_list:
                    key = f"{control_type}\t{control['controlID']}"
                    if self.device.is_control_loaded(control_type, control['controlID']):
                        # load new config into control
                        logging.debug("Adding layouts: %s, %s", control_type, control['controlID'])
                        cfg = CONFIG_INSTANCE_DICT[control_type].from_dict(control)
                        self.device.control_dict[key].add_config_columnar(cfg)
                        modified = True
                        if control['controlID'] in added_control_ids:
                            # Add the next config to the control
                            new_cfg_dict[control_type].append(control)
                    else:
                        # Create a new control.
                        g_control = CONTROL_INSTANCE_DICT[control_type].from_cfg_dict(control)
                        self.device.add_control(g_control)
                        added_control_ids.append(control['controlID'])
                        if control_type not in new_cfg_dict:
                            new_cfg_dict[control_type] = []
                        logging.debug("Added control: %s", control_type + ":" + control["controlID"])
                        new_cfg_dict[control_type].append(control)
                        modified = True
        return modified, new_cfg_dict

    def load_all_controls_from_config(self, cfg_dict) -> dict:
        """Loads all the controls in cfg_dict into device and returns a dictionary of the control objects

        Parameters
        ----------
        device : Dashio.Device
            The device to attach the controls to
        cfg_dict : Dict
            dictionary of the CFG loaded by decode_cfg from a CFG64 or json

        Returns
        -------
        dict
            Dictionary of the control objects
        """

        new_c64 = ""
        modified = False
        modified = self._delete_gui_configs(cfg_dict)
        self._rm_old_action_station_gui_controls()
        modified, new_cfg_dict = self._update_gui_controls(cfg_dict)
        if modified:
            self.device.inc_config_revision()
        if new_cfg_dict:
            # logging.debug("New C64:\n%s", json.dumps(new_cfg_dict, indent=4))
            new_c64 = encode_cfg64(new_cfg_dict)
        return new_c64


    def add_gui_controls(self, g_object: dict):
        """Add a GUI control"""
        cfg_dict = decode_cfg64(g_object["provisioning"])
        new_c64 = self.load_all_controls_from_config(cfg_dict)
        g_object["provisioning"] = new_c64
        self._action_station_layout = g_object
        # there can only be one C64

    def close(self):
        """Close the action_station json filename
        """
        self.save_action(self._json_filename, self.action_station_dict)
        for control in self.thread_dicts.values():
            control.close()
        self.running = False

    def _connect_all_ext_devices(self):
        for device_id in self.remote_device_ids:
            self._connect_device_id(device_id)

    def _connect_device_id(self, device_id):
        msg_dict = {
            'msgType': 'connect',
            'deviceID': device_id
        }
        logging.debug("AS CONNECT: %s", device_id)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg_dict).encode()])

    def _disconnect_device_id(self, device_id):
        msg_dict = {
            'msgType': 'disconnect',
            'deviceID': device_id
        }
        logging.debug("AS DISCONNECT: %s", device_id)
        self.tx_zmq_pub.send_multipart([b"COMMAND", json.dumps(msg_dict).encode()])

    def _start_control(self, t_object: dict):
        if t_object['uuid'] in self.thread_dicts:
            self.thread_dicts[t_object['uuid']].close()
            time.sleep(0.1)
        logging.debug("INIT TASK %s", t_object['uuid'])
        self.thread_dicts[t_object['uuid']] = self.service_objects_defs[t_object['objectType']](self.device_id, self.zmq_service_uuid, t_object, self.context)
        return True

    def _list_command(self, data):
        j_object_list = []
        for j_object in self.configured_services.values():
            action_pair = {
                "name": j_object['name'],
                "uuid": j_object['uuid'],
                "objectType": j_object['objectType'],
                "revision": j_object.get('revision', 1)
            }
            j_object_list.append(action_pair)
        # TODO delete this for loop
        for j_object in self.configs.values():
            action_pair = {
                "name": j_object['name'],
                "uuid": j_object['uuid'],
                "objectType": j_object['objectType'],
                "revision": j_object.get('revision', 1)
            }
            j_object_list.append(action_pair)
        result = {
            'objectType': "LIST_RESULT",
            'list': j_object_list
        }
        reply = f"\t{self.device_id}\tACTN\tLIST\t{json.dumps(result)}\n"
        return reply

    def _list_configs_command(self, data):
        j_object_list = []
        for j_object in self.configs.values():
            if j_object['objectType'] == "CONFIG":
                j_object_list.append(j_object)
        result = {
            'objectType': "LIST_RESULT",
            'list': j_object_list
        }
        reply = f"\t{self.device_id}\tACTN\tLIST_CONFIGS\t{json.dumps(result)}\n"
        return reply

    def _list_tasks_command(self, data):
        j_object_list = []
        for j_object in self.configured_services.values():
            if j_object['objectType'] == "TASK":
                action_pair = {
                    "name": j_object['name'],
                    "uuid": j_object['uuid'],
                    "objectType": j_object['objectType'],
                    "revision": j_object.get('revision', 1)
                }
                j_object_list.append(action_pair)
        result = {
            'objectType': "LIST_RESULT",
            'list': j_object_list
        }
        reply = f"\t{self.device_id}\tACTN\tLIST_TASKS\t{json.dumps(result)}\n"
        return reply

    def _get_command(self, data):
        payload = json.loads(data[3])
        j_object = self.configured_services.get(payload["uuid"], {})
        reply = f"\t{self.device_id}\tACTN\tGET\t{json.dumps(j_object)}\n"
        return reply

    def _delete_command(self, data):
        logging.debug("DELETE: %s", data)
        payload = json.loads(data[3])
        result = {
            'objectType': "DELETE_RESULT",
            'uuid': payload['uuid'],
            'result': False
        }
        try:
            store_obj = self.configured_services[payload["uuid"]]
            if store_obj['objectType'] in self.service_objects_defs:
                self.thread_dicts[payload['uuid']].close()
                time.sleep(0.1)
                del self.thread_dicts[payload['uuid']]
            if store_obj['objectType'] == "DVCE_CONFIG":
                self._rm_old_action_station_gui_controls()
                self._action_station_layout = None
            del self.configured_services[payload["uuid"]]

            result['result'] = True
        except KeyError as error:
            logging.debug("Key Error: %s", error)
            result['result'] = False
        reply = f"\t{self.device_id}\tACTN\tDELETE\t{json.dumps(result)}\n"
        self.save_action(self._json_filename,  self.action_station_dict)
        return reply

    def _rx_command(self, msg):
        msg_dict = json.loads(msg)
        logging.debug("AS RX CMD: %s", msg_dict)

    def _update_command(self, data):
        payload = json.loads(data[3])
        result = {
            'objectType': "UPDATE_RESULT",
            'uuid': payload['uuid'],
            'result': False
        }
        try:
            if payload['objectType'] in self.service_objects_defs:
                self.configured_services[payload['uuid']] = payload
                result['result'] = self._start_control(payload)
            if payload['objectType'] == 'DVCE_CONFIG':
                result['result'] = True
                self.add_gui_controls(payload)
                self.configured_services[payload['uuid']] = payload
        except KeyError as error:
            msg = "UPDATE: payload has no objectType"
            logging.debug("%s, %s", msg, error)
            result['message'] = msg
        if result['result']:
            self.save_action(self._json_filename,  self.action_station_dict)
        reply = f"\t{self.device_id}\tACTN\tUPDATE\t{json.dumps(result)}\n"
        return reply

    def _run_command(self, data):
        # payload = json.loads(data[3])
        reply = ""
        return reply

    def __init__(self, device, max_actions=100, number_timers=10, memory_storage_size=0, context: zmq.Context=None):
        """Action Station"""
        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self.device_id = device.device_id
        self.device = device
        self._json_filename = f"{self.device_id}_Actions.json"

        self.configured_services = {}
        self.configs = {}
        self.memory_tasks = {}
        self.remote_device_ids = []
        self.connections_list = []
        self._action_station_layout = None
        self.action_station_dict = self.load_action(self._json_filename)
        self.max_actions = max_actions

        self.service_objects_defs = {
            'TASK': TaskService,
            'TMR': TimerService,
            'MDBS': ModbusService,
            'CLK': ClockService
        }
        self.thread_dicts = {} # For the Instantiated control and task objects.

        self._action_station_commands = {
            "LIST": self._list_command,
            "LIST_TASKS": self._list_tasks_command,
            "LIST_CONFIGS": self._list_configs_command,
            "GET": self._get_command,
            "DELETE": self._delete_command,
            "UPDATE": self._update_command,
            "RUN": self._run_command
        }
        timer_cfg = make_timer_config(number_timers)
        test_cfg = make_test_config(1)
        modbus_cfg = make_modbus_config(1)
        clock_cfg = make_clock_config(1)
        self.configs[timer_cfg['uuid']] = timer_cfg
        self.configs[test_cfg['uuid']] = test_cfg
        self.configs[modbus_cfg['uuid']] = modbus_cfg
        self.configs[clock_cfg['uuid']] = clock_cfg
        self.zmq_service_uuid =  "SRVC:" + shortuuid.uuid()
        if not self.action_station_dict:
            self.zmq_connection_uuid = "ACTN:" + shortuuid.uuid()
            self.action_station_dict['actionStationID'] = self.zmq_connection_uuid
            self.action_station_dict['services'] = self.configured_services
            self.action_station_dict['tasksMemory'] = self.memory_tasks
        else:
            try:
                self.zmq_connection_uuid = self.action_station_dict['actionStationID']
                self.configured_services = self.action_station_dict['services']
                self.memory_tasks = self.action_station_dict['tasksMemory']
            except KeyError:
                sys.exit(f"Old json formatted file. Please delete '{self._json_filename}' and restart")

        self.running = True
        self.start()

    def run(self):

        self.zmq_service_pub = self.context.socket(zmq.PUB)

        self.zmq_service_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_service_uuid))

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

        self.device_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.device_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.device_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.zmq_connection_uuid)

        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")
        self.connection_zmq_sub = self.context.socket(zmq.SUB)
        self.connection_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "COMMAND")
        self.connection_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "\t") # - All valid DashIO messaging

        # Socket to receive messages on
        task_receiver = self.context.socket(zmq.PULL)
        task_receiver.bind(TASK_PULL.format(id=self.zmq_service_uuid))

        memory_socket = self.context.socket(zmq.REP)
        memory_socket.bind(MEMORY_REQ_URL.format(id=self.device_id))

        poller = zmq.Poller()
        poller.register(self.device_zmq_sub, zmq.POLLIN)
        poller.register(self.connection_zmq_sub, zmq.POLLIN)
        poller.register(task_receiver, zmq.POLLIN)
        poller.register(memory_socket, zmq.POLLIN)

        for j_object in self.configured_services.values():
            if j_object['objectType'] == "DVCE_CONFIG":
                self.add_gui_controls(j_object)
            else:
                self._start_control(j_object)

        while self.running:
            try:
                socks = dict(poller.poll(20))
            except zmq.error.ContextTerminated:
                break
            if self.device_zmq_sub in socks:
                try:
                    [_, msg] = self.device_zmq_sub.recv_multipart()
                except ValueError:
                    # If there aren't two parts continue.
                    pass
                if msg:
                    logging.debug("ActionStation Device RX:\n%s", msg.decode().rstrip())
                    self.zmq_service_pub.send_multipart([msg, self.device_id.encode()])

            if self.connection_zmq_sub in socks:
                msg, msg_from = self.connection_zmq_sub.recv_multipart()
                # logging.debug("ActionStation Connection RX:\n%s, %s", msg_from, msg.decode())
                if msg[0] == b"COMMAND":
                    self._rx_command(msg_from)
                    continue
                if msg.startswith(f"\t{self.device_id}\tACTN".encode()):
                    self._service_actn_commands(msg, msg_from)
                    continue
                self.zmq_service_pub.send_multipart([msg, msg_from])

            if task_receiver in socks:
                msg_to, msg = task_receiver.recv_multipart()
                self.tx_zmq_pub.send_multipart([msg_to, msg])
                if msg_to == b'COMMAND':
                    msg_dict = json.loads(msg)
                    if msg_dict['msgType'] == 'connect':
                        if msg_dict['deviceID'] not in self.remote_device_ids:
                            logging.debug("Added remote deviceID: %s", msg_dict['deviceID'])
                            self.remote_device_ids.append(msg_dict['deviceID'])

            if memory_socket in socks:
                message = memory_socket.recv_multipart()
                logging.debug("MEM Rx: %s", message)
                if len(message) == 3:
                    if message[0] == b'SET':
                        self.memory_tasks[message[1].decode()]=message[2].decode()
                        logging.debug("MEM Tx: SET: %s, TO: %s", message[1], message[2])
                        memory_socket.send_multipart([message[0], message[1], message[2]])
                    if message[0] == b'GET':
                        logging.debug("MEM Tx: GET: %s, RTN: %s", message[1], message[1])
                        memory_socket.send_multipart([message[0], message[1], self.memory_tasks[message[1].decode()].encode()])
                #  Send error reply back to client
                else:
                    memory_socket.send_multipart([b'ERROR',b'ERROR',b'ERROR'])


        self.tx_zmq_pub.close()
        self.device_zmq_sub.close()
        memory_socket.close()
        task_receiver.close()
