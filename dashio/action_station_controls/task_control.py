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
import zmq
import logging
import threading
from ..constants import TASK_PULL

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

class TaskControl(threading.Thread):
    """Task Class"""

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send_multipart([b"ALL", b"0", out_message.encode('utf-8')])

    def close(self):
        """Close the thread"""
        self.running = False

    def _task_store_mem(self, mem_loc, data):
        self.task_memory[mem_loc] = data

    def _task_get_mem(self, mem_loc):
        return self.task_memory.get(mem_loc, "")

    def _send_alarm(self, alarm_id: str, header: str, body: str):
        msg = f"\t{self.device_id}\t{alarm_id}\t{header}\t{body}\n"
        self.task_sender.send_multipart([b"ALARM", b"0", msg.encode('utf-8')])

    def _read_control_action(self, action, msg):
        logging.debug("READ_CONTROL: %s", msg)

    def _send_alarm_action(self, action, msg):
        logging.debug("SEND_ALARM: %s", msg)
        self._send_alarm(action['alarmID'], action['title'], action['body'])

    def _write_control_action(self, action, msg):
        logging.debug("WRITE_CONTROL: %s", msg)


    def __init__(self, device_id: str, action_station_id: str, task_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.device_id = device_id
        self.control_type = "TASK"
        self.task_memory = {}

        action_function_dict = {
            "READ_CONTROL": self._read_control_action,
            "SEND_ALARM": self._send_alarm_action,
            "WRITE_CONTROL": self._write_control_action
        }

        self.task_id = task_config_dict['uuid']
        self.actions = task_config_dict['actions']
        self.name = task_config_dict['name']
        self.push_url = TASK_PULL.format(id=action_station_id)
        self.pull_url = TASK_PULL.format(id=self.task_id)

        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)
        self.start()

    # Do a simple test case to check messaging.
    def _do_actions(self, msg):
        if len(self.actions) == 2:
            if self.actions[0]['objectType'] == "READ_CONTROL":
                self._read_control_action(self.actions[0], msg)
            else:
                return
            if self.actions[1]['objectType'] == "SEND_ALARM":
                self._send_alarm_action(self.actions[1], msg)
            elif self.actions[1]['objectType'] == "WRITE_CONTROL":
                self._write_control_action(self.actions[1], msg)

    def run(self):
        task_receiver = self.context.socket(zmq.PULL)
        task_receiver.bind(self.pull_url)
        poller = zmq.Poller()
        poller.register(task_receiver, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(15))
            except zmq.error.ContextTerminated:
                break
            if task_receiver in socks:
                message = task_receiver.recv()
                if message:
                    logging.debug("TASK: %s\t%s RX:%s", self.name, self.task_id, message.decode())
                    self._do_actions(message)
        self.task_sender.close()
        task_receiver.close()
