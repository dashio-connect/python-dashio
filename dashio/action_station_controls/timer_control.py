"""Timer Class"""
import threading
import zmq
from .action_control_config import ActionControlCFG, SelectorParameterSpec, IntParameterSpec



def make_timer_config(num_timers):
    """Make a timer config"""
    provisioning_list = [
        SelectorParameterSpec("SLCTR1", "Timer Type",["Repeat", "OneShot"], "Repeat"),
        IntParameterSpec("INT1", "Timeout", 100, 600000, "ms", 1000)
    ]
    parameter_list = []
    timer_cfg = ActionControlCFG(
        "TIMER",
        "Timer Provisioning",
        "A useful timer can be used as a recurring or oneshot.",
        "TMR",
        num_timers,
        True,
        True,
        True,
        provisioning_list,
        parameter_list
    )
    return timer_cfg.__json__()


class RepeatTimer(threading.Timer):
    """The timer"""
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class TimerControl(threading.Thread):
    """Timer Class"""

    def timeout(self):
        pass

    def __init__(self, timer_type: str, timeout: int, context) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.timer_type = None
        timer_time = timeout/1000.0
        if timer_type == 'REPEAT':
            self.timer_type = RepeatTimer(timer_time, self.timeout)