import zmq
import logging

from .constants import TASK_PULL_URL


def _read_control(data):
    logging.debug("TASK: ")
    return ""

TASK_FUNC_DICT = {
    "READ_CONTROL": _read_control
}


def task_runner(task_dict: dict, data: list, push_id: str, context):
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
    # Socket to send messages to
    task_sender = context.socket(zmq.PUSH)
    task_sender.connect(TASK_PULL_URL.format(push_id))


    for task in task_dict['tasks']:
        result = TASK_FUNC_DICT[task['objectType']](data)

    
    task_sender.send(result)
    


