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
import json
import logging
import threading

import zmq

from ..constants import CONNECTION_PUB_URL, MEMORY_REQ_URL, TASK_PULL


def num(s_num: str):
    try:
        return int(s_num)
    except ValueError:
        return float(s_num)

def _read_control_task(data, task):
    logging.debug("READ_CONTROL: %s", data)
    return data[+3]

def _if_task(data, task):
    logging.debug("IF: %s", data)
    return ""

def _endif_task(data, task):
    logging.debug("ENDIF: %s", data)
    return  ''

def _send_alarm_task(data, task):
    logging.debug("SEND_ALARM: %s", data)
    return  ''

def _write_control_task(data, task):
    logging.debug("WRITE_CONTROL: %s", data)
    return ""

MESSAGE_FORMAT_INPUTS = {
    "AVD": ["url"],
    "BTTN": ["button_state", "icon_name", "text"],
    "TEXT": ["text"],
    "GRPH": ["line_id", "line_data"],
    "DIAL": ["data"],
    "CLR": ["rgb"],
    "TGRPH": ["time_stamp", "data"],
    "KNOB": ["data"],
    "KBDL": ["data"],
    "SLCTR": ["url"],
    "SLDR": ["url"],
    "DIR": ["url"],
    "LOG": ["url"],
    "LBL": ["url"],
}

MESSAGE_FORMAT_OUTPUTS = {
    "AVD": "\t{device_id}\tAVD\t{control_id}\t{url}",
    "BTTN": "\t{device_id}\tBTTN\t{control_id}\t{url}",
    "TEXT": "\t{device_id}\tTEXT\t{control_id}\t{url}",
    "GRPH": "\t{device_id}\tGRPH\t{control_id}\t{url}",
    "DIAL": "\t{device_id}\tDIAL\t{control_id}\t{url}",
    "CLR": "\t{device_id}\tCLR\t{control_id}\t{url}",
    "TGRPH": "\t{device_id}\tTGRPH\t{control_id}\t{url}",
    "KNOB": "\t{device_id}\tKNOB\t{control_id}\t{url}",
    "KBDL": "\t{device_id}\tKBDL\t{control_id}\t{url}",
    "SLCTR":"\t{device_id}\tSLCTR\t{control_id}\t{url}",
    "SLDR": "\t{device_id}\tSLDR\t{control_id}\t{url}",
    "DIR": "\t{device_id}\tDIR\t{control_id}\t{url}",
    "LOG": "\t{device_id}\tLOG\t{control_id}\t{url}",
    "LBL": "\t{device_id}\tLBL\t{control_id}\t{url}",
}

class TaskService(threading.Thread):
    """Task Class"""

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send_multipart([b"ALL", out_message.encode()])

    def close(self):
        """Close the thread"""
        self.running = False

    def _task_store_mem(self, mem_loc, data):
        self.task_memory[mem_loc] = data

    def _task_get_mem(self, mem_loc):
        return self.task_memory.get(mem_loc, "")

    def _send_alarm(self, alarm_id: str, header: str, body: str):
        msg = f"\t{self.device_id}\tALM\t{alarm_id}\t{header}\t{body}\n"
        self.send_message(msg)

    def _read_control_action(self, action, msg: bytearray):
        logging.debug("READ_CONTROL: %s", msg.decode())

    def _send_alarm_action(self, action, msg):
        logging.debug("SEND_ALARM: %s", msg)
        self._send_alarm(action['alarmID'], action['title'], action['body'])

    def _write_control_action(self, action, msg):
        logging.debug("WRITE_CONTROL: %s", msg.decode())

    def _read_mem_action(self, action, msg):
        logging.debug("READ_MEM memType: %s", action["memType"])
        if action["memType"] == "Local":
            pass
        elif action["memType"] == "Task":
            reply = self._task_get_mem(action['memoryID'])
            logging.debug("Task read mem: %s", reply)
        elif action["memType"] == "Global":
            self.device_mem_socket.send_multipart([b'GET', action['memoryID'].encode(), b'0'])
            reply = self.device_mem_socket.recv_multipart()
        else:
            logging.debug("READ_MEM unknown memType: %s", action["memType"])

    def _write_mem_action(self, action, msg):
        logging.debug("WRITE_MEM memType: %s", action["memType"])
        if action["memType"] == "Local":
            pass
        elif action["memType"] == "Task":
            self._task_store_mem(action['memoryID'], action['thing'])
        elif action["memType"] == "Global":
            self.device_mem_socket.send_multipart([b'SET', action['memoryID'].encode(), action['thing'].encode()])
            reply = self.device_mem_socket.recv_multipart()
            logging.debug("Task write mem: %s", reply)
        else:
            logging.debug("WRITE_MEM unknown memType: %s", action["memType"])

    def _connect_device_id(self, device_id):
        msg_dict = {
            'msgType': 'connect',
            'deviceID': device_id
        }
        logging.debug("AS CONNECT: %s", device_id)
        self.task_sender.send_multipart([b"COMMAND", json.dumps(msg_dict).encode()])

    def __init__(self, device_id: str, action_station_id: str, task_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.device_id = device_id
        self.control_type = "TASK"
        self.task_memory = {}

        self.action_function_dict = {
            "READ_CONTROL": self._read_control_action,
            "SEND_ALARM": self._send_alarm_action,
            "WRITE_CONTROL": self._write_control_action,
            "READ_MEM": self._read_mem_action,
            "WRITE_MEM": self._write_mem_action,
        }

        self.task_id = task_config_dict['uuid']
        self.actions = task_config_dict['actions']
        self.name = task_config_dict['name']
        self.sub_msg = None
        rx_device_id = ""
        if len(self.actions) == 0:
            return
        try:
            rx_device_id = self.actions[0]["deviceID"]
            rx_control_type = self.actions[0]["controlType"]
            rx_control_id = self.actions[0]["controlID"]
        except KeyError:
            return
        self.sub_msg = f"\t{rx_device_id}\t{rx_control_type}\t{rx_control_id}"
        self.push_url = TASK_PULL.format(id=action_station_id)
        self.sub_url = CONNECTION_PUB_URL.format(id=action_station_id)

        self.device_mem_socket = self.context.socket(zmq.REQ)
        self.device_mem_socket.connect(MEMORY_REQ_URL.format(id=self.device_id))

        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)

        if rx_device_id != device_id:
            self._connect_device_id(rx_device_id)
        self.start()

    # Do a simple test case to check messaging.
    def _do_actions(self, msg):
        for action in self.actions:
            self.action_function_dict[action['objectType']](action, msg)


    def run(self):
        task_receiver = self.context.socket(zmq.SUB)
        task_receiver.connect(self.sub_url)
        task_receiver.setsockopt_string(zmq.SUBSCRIBE, self.sub_msg)

        poller = zmq.Poller()
        poller.register(task_receiver, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(15))
            except zmq.error.ContextTerminated:
                break
            if task_receiver in socks:
                message, _ = task_receiver.recv_multipart()
                if message:
                    logging.debug("TASK: %s\t%s RX:%s", self.name, self.task_id, message.decode())
                    self._do_actions(message)
        self.task_sender.close()
        task_receiver.close()
        self.device_mem_socket.close()
