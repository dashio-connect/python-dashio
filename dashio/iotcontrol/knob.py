from .enums import Color, KnobStyle, TitlePosition
from .control import Control


class Knob(Control):
    def __init__(
        self,
        control_id,
        title="A Knob",
        title_position=TitlePosition.BOTTOM,
        knob_style=KnobStyle.NORMAL,
        min=0.0,
        max=100.0,
        red_value=75.0,
        show_min_max=False,
        send_only_on_release=True,
        dial_follows_knob=False,
        dial_color=Color.BLUE,
        knob_color=Color.RED,
        control_position=None,
    ):
        super().__init__("KNOB", control_id, control_position=control_position, title_position=title_position)
        self.title = title
        self._control_id_dial = "KBDL"
        self._knob_value = 0
        self._knob_dial_value = 0
        self.knob_style = knob_style
        self.min = min
        self.max = max
        self.red_value = red_value
        self.show_min_max = show_min_max
        self.send_only_on_release = send_only_on_release
        self.dial_follows_knob = dial_follows_knob
        self.dial_color = dial_color
        self.knob_color = knob_color
        self._state_str_knob = self._state_str + "{}\n".format(self._knob_value)
        self._state_str_dial = self._state_str + "{}\n".format(self._knob_dial_value)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    def get_state(self):
        return self._knob_dial_state_str

    @property
    def knob_value(self) -> float:
        return self._knob_value

    @knob_value.setter
    def knob_value(self, val: float):
        self._knob_value = val
        self._state_str_knob = self._state_str + "{}\n".format(val)
        self.message_tx_event(self._state_str_knob)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_dial_value(self) -> float:
        return self._knob_dial_value

    @knob_dial_value.setter
    def knob_dial_value(self, val: float):
        self._knob_dial_value = val
        self._state_str_dial = self._state_str + "{}\n".format(val)
        self.message_tx_event(self._state_str_dial)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_style(self) -> KnobStyle:
        return self._knob_style

    @knob_style.setter
    def knob_style(self, val: KnobStyle):
        self._knob_style = val
        self._cfg["style"] = str(val.value)

    @property
    def min(self) -> float:
        return self._cfg["min"]

    @min.setter
    def min(self, val: float):
        self._cfg["min"] = val

    @property
    def max(self) -> float:
        return self._cfg["max"]

    @max.setter
    def max(self, val: float):
        self._cfg["max"] = val

    @property
    def red_value(self) -> float:
        return self._cfg["redValue"]

    @red_value.setter
    def red_value(self, val: float):
        self._cfg["redValue"] = val

    @property
    def show_min_max(self) -> bool:
        return self._cfg["showMinMax"]

    @show_min_max.setter
    def show_min_max(self, val: bool):
        self._cfg["showMinMax"] = val

    @property
    def send_only_on_release(self) -> bool:
        return self._cfg["sendOnlyOnRelease"]

    @send_only_on_release.setter
    def send_only_on_release(self, val: bool):
        self._cfg["sendOnlyOnRelease"] = val

    @property
    def dial_follows_knob(self) -> bool:
        return self._cfg["dialFollowsKnob"]

    @dial_follows_knob.setter
    def dial_follows_knob(self, val: bool):
        self._cfg["dialFollowsKnob"] = val

    @property
    def dial_color(self) -> Color:
        return self._dial_color

    @dial_color.setter
    def dial_color(self, val: Color):
        self._dial_color = val
        self._cfg["dialColor"] = str(val.value)

    @property
    def knob_color(self) -> Color:
        return self._knob_color

    @knob_color.setter
    def knob_color(self, val: Color):
        self._knob_color = val
        self._cfg["knobColor"] = str(val.value)
