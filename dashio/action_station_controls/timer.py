"""Timer Class"""
import threading
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

class Timer(threading.Thread):
    """Timer Class"""

    def timeout(self):
        pass

    def __init__(self, timer_type: str, timeout: int) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.timer_type = None
        if timer_type == 'REPEAT':
            self.timer_type = RepeatTimer(1, self.timeout, args=("bar",))