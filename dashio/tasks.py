import zmq
import logging

from .constants import TASK_PULL_URL


def _read_control(data):
    logging.debug("TASK: ")
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
    "READ_CONTROL": _read_control
}


def task_runner(task_dict: dict, data: list, push_id: str, context: zmq.Context):
    """Run a task

    Parameters
    ----------
    task_dict : dict
        The dask to perfom
    data : list
        The data for the task.
    push_id : str
        Who to send the result too.
    context : zmq.Context
        Use this context to be Thread safe
    """
    result = "TASK TEST"

    for task in task_dict['tasks']:
        try:
            result = TASK_FUNC_DICT[task['objectType']](data)
        except KeyError:
            logging.debug("TASK NOT YET IMPLEMENTED: %s", task['objectType'])
    if result:
    # Set up socket to send messages to
        task_sender = context.socket(zmq.PUSH)
        task_sender.connect(TASK_PULL_URL.format(id=push_id))
        # send the result
        task_sender.send(result.encode())
