"""action_station.py

Copyright (c) 2022, Douglas Otwell, DashIO

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

import shortuuid
import zmq

from .constants import CONNECTION_PUB_URL, DEVICE_PUB_URL
from .action_station_controls.tasks import task_runner
from .action_station_controls.timer_control import make_timer_config

class ActionControl():
    """A CFG control class to store Action information
    """

    def get_state(self) -> str:
        """Returns controls state. Not used for this control

        Returns
        -------
        str
            Not used in this control
        """
        return ""

    def get_cfg(self, data) -> str:
        """Returns the CFG string for this TCP control

        Returns
        -------
        str
            The CFG string for this control
        """
        try:
            dashboard_id = data[2]
        except IndexError:
            return ""
        cfg_str = f"\tCFG\t{dashboard_id}\t{self.cntrl_type}\t{json.dumps(self._cfg)}\n"
        return cfg_str

    def get_cfg64(self, data) -> dict:
        """Returns the CFG dict for this TCP control

        Returns
        -------
        dict
            The CFG string for this control
        """
        return self._cfg

    def __init__(self, control_id, max_tasks: int, number_timers: int, memory_size: int):
        self._cfg = {}
        self.cntrl_type = "ACTN"
        self._cfg['controlID'] = control_id
        self.control_id = control_id
        self.max_tasks = max_tasks
        self.number_timers = number_timers
        if memory_size > 0:
            self.memory_storage_size = memory_size

    @property
    def max_tasks(self) -> int:
        """max number of tasks

        Returns
        -------
        int
            The max number of tasks
        """
        return int(self._cfg["maxTasks"])

    @max_tasks.setter
    def max_tasks(self, val: int):
        self._cfg["maxTasks"] = val

    @property
    def number_timers(self) -> int:
        """number of Timers

        Returns
        -------
        int
            The number of timers
        """
        return int(self._cfg["numTimers"])

    @number_timers.setter
    def number_timers(self, val: int):
        self._cfg["numTimers"] = val

    @property
    def memory_storage_size(self) -> int:
        """Size of memory storage

        Returns
        -------
        int
            The number of timers
        """
        return int(self._cfg["memSize"])

    @memory_storage_size.setter
    def memory_storage_size(self, val: int):
        self._cfg["memSize"] = val
    
    
class ActionStation(threading.Thread):
    """_summary_

    Parameters
    ----------
    threading : _type_
        _description_
    """
    def _on_message(self, payload):
        data = str(payload, "utf-8").strip()
        command_array = data.split("\n")
        reply = ""
        for command in command_array:
            try:
                reply += self._on_command(command.strip())
            except TypeError:
                pass
        return reply

    def _on_command(self, data):
        data_array = data.split("\t")
        try:
            rx_device_id = data_array[0]
            cntrl_type = data_array[1]
            control_id = data_array[2]
        except (KeyError, IndexError):
            return ""
        if rx_device_id == self.device_id and cntrl_type == 'ACTN':
            command = data_array[2]
            if command in self._action_station_commands:
                return self._action_station_commands[command](data_array)
        task_dict_key = f"{rx_device_id}\t{control_id}\t"
        if task_dict_key in self._device_control_filter_dict:
            uuid = self._device_control_filter_dict[task_dict_key]
            threading.Thread(target=task_runner, args=( self.action_station_dict['jsonStore'][uuid], data_array, self.task_pull_url, self.context)).start()
        return ""

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

    def add_connection(self, connection):
        """Add a connection to listen too

        Parameters
        ----------
        connection : _type_
            _description_
        """
        self.connection_zmq_sub.connect(CONNECTION_PUB_URL.format(id=connection.connection_id))
        self.connection_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, connection.connection_id)
        connection.rx_zmq_sub.connect(DEVICE_PUB_URL.format(id=self.action_station_id))

    def close(self):
        """Close the action_station json filename
        """
        self.save_action(self._json_filename, self.action_station_dict)
        self.running = False

    def _add_input_filter(self, j_object: dict):
        if j_object['objectType'] == 'TASK':
            try:
                rx_device_id = j_object['tasks'][0]["deviceID"]
            except KeyError:
                rx_device_id = self.device_id
            control_id = j_object['tasks'][0]["controlID"]
            task_dict_key = f"{rx_device_id}\t{control_id}\t"
            self._device_control_filter_dict[task_dict_key] = j_object['uuid']

    def _delete_input_filter(self, uuid: str):
        store_object = self.action_station_dict['jsonStore'][uuid]
        if store_object['objectType'] in ['TASK']:
            rx_device_id = store_object['tasks'][0]["deviceID"]
            control_id = store_object['tasks'][0]["controlID"]
            task_dict_key = f"{rx_device_id}\t{control_id}\t"
            del self._device_control_filter_dict[task_dict_key]

    def _list_command(self, data):
        j_object_list = []
        for j_object in self.action_station_dict['jsonStore'].values():
            action_pair = {
                "name": j_object['name'],
                "uuid": j_object['uuid'],
                "objectType": j_object['objectType']
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
        for j_object in self.action_station_dict['jsonStore'].values():
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
        for j_object in self.action_station_dict['jsonStore'].values():
            if j_object['objectType'] == "TASK":
                action_pair = {
                    "name": j_object['name'],
                    "uuid": j_object['uuid'],
                    "objectType": j_object['objectType']
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
        try:
            j_object = self.action_station_dict['jsonStore'][payload["uuid"]]
        except KeyError:
            j_object = {}
        reply = f"\t{self.device_id}\tACTN\tGET\t{json.dumps(j_object)}\n"
        return reply

    def _delete_command(self, data):
        payload = json.loads(data[3])
        result = {
            'objectType': "DELETE_RESULT",
            'uuid': payload['uuid'],
            'result': False
        }
        try:
            self._delete_input_filter(payload["uuid"])
            store_obj = self.action_station_dict['jsonStore'][payload["uuid"]]
            if store_obj['objectType'] not in ["CONFIG"]:
                del self.action_station_dict['jsonStore'][payload["uuid"]]
                result['result'] = True
        except KeyError:
            result['result'] = False
            result['error'] = "Cannot delete CFG"
        reply = f"\t{self.device_id}\tACTN\tDELETE\t{json.dumps(result)}\n"
        self.save_action(self._json_filename,  self.action_station_dict)
        return reply

    def _update_command(self, data):
        payload = json.loads(data[3])
        result = {
            'objectType': "UPDATE_RESULT",
            'uuid': payload['uuid']
        }
        if payload['objectType'] in ['TASK', 'TMR', 'MRY']:
            if 'jsonStore' not in self.action_station_dict:
                self.action_station_dict['jsonStore'] = {}
            self.action_station_dict['jsonStore'][payload['uuid']] = payload
            reply = f"\t{self.device_id}\tACTN\tUPDATE\t{json.dumps(result)}\n"
            self._add_input_filter(payload)
        self.save_action(self._json_filename,  self.action_station_dict)
        return reply

    def _run_command(self, data):
        payload = json.loads(data[3])
        reply = ""
        return reply
    
    def __init__(self, device_id: str, max_actions=100, number_timers=10, memory_storage_size=0, context: zmq.Context=None):
        """Action Station"""
        threading.Thread.__init__(self, daemon=True)
        self.context = context or zmq.Context.instance()
        self._json_filename = f"{device_id}_Actions.json"
        self.action_station_dict = self.load_action(self._json_filename)
        self.max_actions = max_actions
        self._device_control_filter_dict = {}
        self.device_id = device_id
        self.timers = []
        self._action_station_commands = {
            "LIST": self._list_command,
            "LIST_TASKS": self._list_tasks_command,
            "LIST_CONFIGS": self._list_configs_command,
            "GET": self._get_command,
            "DELETE": self._delete_command,
            "UPDATE": self._update_command,
            "RUN": self._run_command
        }

        if not self.action_station_dict:
            self.action_station_id = shortuuid.uuid()
            self.action_station_dict['actionStationID'] = self.action_station_id
            self.action_station_dict['jsonStore'] = {}
            timer_cfg = make_timer_config(number_timers)
            self.action_station_dict['jsonStore'][timer_cfg['uuid']] = timer_cfg
        else:
            self.action_station_id = self.action_station_dict['actionStationID']
            for j_object in self.action_station_dict['jsonStore'].values():
                self._add_input_filter(j_object)

        self.task_pull_url = f"inproc://TASK_PULL_{self.action_station_id}"
        self.running = True
        self.start()
        time.sleep(1)

    def run(self):
        tx_zmq_pub = self.context.socket(zmq.PUB)
        tx_zmq_pub.bind(DEVICE_PUB_URL.format(id=self.action_station_id))

        self.device_zmq_sub = self.context.socket(zmq.SUB)
        # Subscribe on ALL, and my connection
        self.device_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALL")
        self.device_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ALARM")
        self.device_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, self.action_station_id)

        # rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "ANNOUNCE")
        self.connection_zmq_sub = self.context.socket(zmq.SUB)

        # Socket to receive messages on
        task_receiver = self.context.socket(zmq.PULL)
        task_receiver.bind( self.task_pull_url)

        poller = zmq.Poller()
        poller.register(self.device_zmq_sub, zmq.POLLIN)
        poller.register(self.connection_zmq_sub, zmq.POLLIN)
        poller.register(task_receiver, zmq.POLLIN)
        while self.running:
            try:
                socks = dict(poller.poll(50))
            except zmq.error.ContextTerminated:
                break
            if self.device_zmq_sub in socks:
                try:
                    [_, _, data] = self.device_zmq_sub.recv_multipart()
                except ValueError:
                    # If there aren't three parts continue.
                    pass
                if data:
                    logging.debug("ActionStation Device RX:\n%s", data.decode().rstrip())
                    reply = self._on_message(data)
                    if reply:
                        tx_zmq_pub.send_multipart([b'ALL', b'', reply.encode('utf-8')])
            if self.connection_zmq_sub in socks:
                msg = self.connection_zmq_sub.recv_multipart()
                if len(msg) == 3:
                    if msg[0] == b"COMMAND":
                        continue
                    logging.debug("ActionStation Connection RX:\n%s", msg[2].decode().rstrip())
                    reply = self._on_message(msg[2])
                    if reply:
                        tx_zmq_pub.send_multipart([msg[0], msg[1], reply.encode('utf-8')])
            if task_receiver in socks:
                message = task_receiver.recv()
                if message:
                    logging.debug("ActionStation TASK RX:\n%s", message.decode())
                    tx_zmq_pub.send_multipart([b'ALL', b'', message])
        tx_zmq_pub.close()
        self.device_zmq_sub.close()
