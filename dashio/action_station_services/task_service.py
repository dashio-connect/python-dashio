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
import math
import zmq

from ..constants import TASK_CONN_PORT_OFFSET, TASK_MEMORY_PORT_OFFSET, TASK_PULL_PORT_OFFSET, TCP_URL
from . import action_station_service_config as assc


def str_to_num(s_num: str):
    try:
        return int(s_num)
    except ValueError:
        return float(s_num)


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

    def _read_control_action(self, action: assc.ActionReadControl, msg: list):
        logging.debug("READ_CONTROL: %s", msg)
        if msg[0] != action.deviceID or msg[1] != action.controlType or msg[2] != action.controlID:
            return False, []
        return True, msg[3:]

    def _write_control_action(self, action: assc.ActionWriteControl, msg: list):
        logging.debug("WRITE_CONTROL: %s", msg)
        data = "\t".join(msg) + "\n"
        self.send_message(f"\t{action.deviceID}\t{action.controlType}\t{action.controlID}\t{data}")
        return True, msg

    def _send_alarm_action(self, action: assc.ActionSendAlarm, msg: list):
        logging.debug("SEND_ALARM: %s", msg)
        self._send_alarm(action.alarmID, action.title, action.body)
        return True, msg

    def _write_mem_action(self, action: assc.ActionWriteMem, msg: list):
        logging.debug("WRITE_MEM memType: %s", action.memType)
        if action.memType == "Local":
            pass
        elif action.memType == "Task":
            self._task_store_mem(action.memType, msg)
        elif action.memType == "Global":
            thing = "\t".join(msg)
            self.device_mem_socket.send_multipart([b'SET', action.memoryID.encode(), thing.encode()])
            reply = self.device_mem_socket.recv_multipart()
            logging.debug("Task write mem: %s", reply)
        else:
            logging.debug("WRITE_MEM unknown memType: %s", action.memType)
        return True, msg

    def _read_mem_action(self, action: assc.ActionReadMem, msg: list):
        logging.debug("READ_MEM memType: %s", action.memType)
        if action.memType == "Local":
            pass
        elif action.memType == "Task":
            reply = self._task_get_mem(action.memType)
            logging.debug("Task read mem: %s", reply)
            return True, reply.split('\t')
        elif action.memType == "Global":
            self.device_mem_socket.send_multipart([b'GET', action.memType.encode(), b'0'])
            reply = self.device_mem_socket.recv_multipart()
            logging.debug("Task read mem reply: %s", reply)
            # TODO test and return reply
            return True, msg
        else:
            logging.debug("READ_MEM unknown memType: %s", action.memType)
        return True, msg

    def _bitwise_action(self, action: assc.ActionBitwise, msg: list):
        logging.debug("BITWISE BEFORE: %s", msg)
        for msg_item in msg:
            if action.bw_or is not None:
                msg_item = msg_item | action.bw_or
            if action.bw_and is not None:
                msg_item = msg_item & action.bw_and
            if action.shiftRight is not None:
                msg_item = msg_item >> action.shiftRight
        logging.debug("BITWISE AFTER: %s", msg)
        return True, msg

    def _scale_action(self, action: assc.ActionScale, msg: list):
        logging.debug("SCALE: %s", msg)
        new_msg = []
        for msg_item in msg:
            new_item = float(msg_item) * action.scale + action.offset
            new_msg.append(new_item)
        return True, new_msg

    def _if_action(self, action: assc.ActionIf, msg: list):
        logging.debug("IF: %s", msg)
        if action.ifOperator == '>':
            return (float(msg[action.fieldNo]) > float(action.value)), msg
        elif action.ifOperator == '<':
            return (float(msg[action.fieldNo]) < float(action.value)), msg
        elif action.ifOperator == '=':
            return math.isclose(float(msg[action.fieldNo]), float(action.value)), msg
        else:
            return False, msg

    def _connect_device_id(self, device_id):
        msg_dict = {
            'msgType': 'connect',
            'deviceID': device_id
        }
        logging.debug("AS CONNECT: %s", device_id)
        self.task_sender.send_multipart([b"COMMAND", json.dumps(msg_dict).encode()])

    def action_chain(self, start_msg, task_actions: list):
        res = start_msg
        for task_action in task_actions:
            res_if, res = self.actions_map[task_action.objectType](task_action, res)
            if task_action.objectType == 'IF':
                if res_if:
                    res = self.action_chain(res, task_action.ifTrue)
                else:
                    res = self.action_chain(res, task_action.ifFalse)
        return res

    def __init__(self, device_id: str, local_port: int, task_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.device_id = device_id
        self.control_type = "TASK"
        self.task_memory = {}

        self.sub_msg = None
        rx_device_id = ""

        if len(task_config_dict['actions']) == 0:
            return

        self.task = assc.task_parse(task_config_dict)

        try:
            rx_device_id = self.task.actions[0].deviceID
            self.sub_msg = f"\t{rx_device_id}\t{self.task.actions[0].controlType}\t{self.task.actions[0].controlID}"
        except KeyError:
            return

        self.actions_map = {
            'READ_CONTROL': self._read_control_action,
            'WRITE_CONTROL': self._write_control_action,
            'SEND_ALARM': self._send_alarm_action,
            'WRITE_MEM': self._write_mem_action,
            'READ_MEM': self._read_mem_action,
            'BITWISE': self._bitwise_action,
            'SCALE': self._scale_action,
            'IF': self._if_action
        }

        self.sub_url = TCP_URL.format(port=local_port + TASK_CONN_PORT_OFFSET)
        self.push_url = TCP_URL.format(port=local_port + TASK_PULL_PORT_OFFSET)

        self.device_mem_socket = self.context.socket(zmq.REQ)
        self.device_mem_socket.connect(TCP_URL.format(port=local_port + TASK_MEMORY_PORT_OFFSET))

        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)

        if rx_device_id != device_id:
            self._connect_device_id(rx_device_id)
        self.start()

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
                    msg_list = message.decode().strip().split('\t')
                    logging.debug("TASK: %s\t%s RX:%s", self.task.name, self.task.uuid, msg_list)
                    self.action_chain(msg_list, self.task.actions)
        self.task_sender.close()
        task_receiver.close()
        self.device_mem_socket.close()
