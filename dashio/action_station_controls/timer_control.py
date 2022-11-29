"""Timer Class"""
import threading
import zmq
import time
from .action_control_config import ActionControlCFG, SelectorParameterSpec, IntParameterSpec


def make_timer_config(num_timers):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec("SLCTR1", "Timer Type",["Repeat", "OneShot"], "Repeat"),
        IntParameterSpec("INT1", "Timeout", 100, 600000, "ms", 1000)
    ]
    parameter_in_list = []
    parameter_out_list = []

    timer_cfg = ActionControlCFG(
        "TMR",
        "Timer",
        "Timer Provisioning",
        "TMR",
        num_timers,
        True,
        True,
        provisioning_list,
        parameter_in_list
        #parameter_out_list
    )
    return timer_cfg.__json__()


class RepeatTimer(threading.Timer):
    """The timer"""
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class TimerControl(threading.Thread):
    """Timer Class"""

    def send_message(self):
        """Send the message"""
        task_sender = self.context.socket(zmq.PUSH)
        task_sender.connect(self.push_url)
        task_sender.send(self.control_msg.encode())

    def close(self):
        """Close the thread"""
        self.running = False

    def __init__(self, device_id: str, control_id: str, timer_type: str, timeout: int, push_url: str, context: zmq.Context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.context = context
        self.running = True
        self.timer_type = None
        self.push_url = push_url
        timer_time = timeout/1000.0
        self.control_msg = f"\t{device_id}\tTMR\t{control_id}\n"
        if timer_type == 'REPEAT':
            self.timer_type = RepeatTimer(timer_time, self.send_message)
        elif timer_type == 'REPEAT':
            self.timer_type = threading.Timer(timer_time, self.send_message)
        if self.timer_type:
            self.timer_type.start()
        self.start()

    def run(self):
        """Sleep for time"""
        while self.running:
            time.sleep(1)
