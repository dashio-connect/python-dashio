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

TASK_FUNC_DICT = {
    "READ_CONTROL": _read_control_task,
    "IF": _if_task,
    "ENDIF": _endif_task,
    "SEND_ALARM": _send_alarm_task,
    "WRITE_CONTROL": _write_control_task
}

class TaskControl(threading.Thread):
    """Task Class"""

    def send_message(self, out_message=""):
        """Send the message"""
        self.task_sender.send(out_message.encode())

    def close(self):
        """Close the thread"""
        self.running = False

    def _task_store_mem(self, mem_loc, data):
        self.task_memory[mem_loc] = data

    def _task_get_mem(self, mem_loc):
        return self.task_memory.get(mem_loc, "")
    
    def __init__(self, device_id: str, action_station_id: str, task_config_dict: dict, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.device_id = device_id
        self.control_type = "TASK"
        self.task_memory = {}
        self.task_id = task_config_dict['uuid']
        self.actions = task_config_dict['actions']
        self.name = task_config_dict['name']
        self.push_url = TASK_PULL.format(id=action_station_id)
        self.pull_url = TASK_PULL.format(id=self.task_id)

        self.task_sender = self.context.socket(zmq.PUSH)
        self.task_sender.connect(self.push_url)
        self.start()

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
