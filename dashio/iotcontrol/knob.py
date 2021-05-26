from .control import Control
from .enums import Color, KnobStyle, TitlePosition


class Knob(Control):
    def __init__(
        self,
        control_id,
        title="A Knob",
        title_position=TitlePosition.BOTTOM,
        knob_style=KnobStyle.NORMAL,
        dial_min=0.0,
        dial_max=100.0,
        red_value=75.0,
        show_min_max=False,
        send_only_on_release=True,
        dial_follows_knob=False,
        dial_color=Color.BLUE,
        knob_color=Color.RED,
        control_position=None,
    ):
        super().__init__("KNOB", control_id, title=title, control_position=control_position, title_position=title_position)
        self._control_id_dial = f"\t{{device_id}}\tKBDL\t{control_id}\t"
        self._knob_value = 0
        self._knob_dial_value = 0
        self.knob_style = knob_style
        self.dial_min = dial_min
        self.dial_max = dial_max
        self.red_value = red_value
        self.show_min_max = show_min_max
        self.send_only_on_release = send_only_on_release
        self.dial_follows_knob = dial_follows_knob
        self.dial_color = dial_color
        self.knob_color = knob_color
        self._state_str_knob = self._control_hdr_str + f"{self._knob_value}\n"
        self._state_str_dial = self._control_id_dial + f"{self._knob_dial_value}\n"
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    def get_state(self):
        return self._knob_dial_state_str

    @property
    def knob_value(self) -> float:
        return self._knob_value

    @knob_value.setter
    def knob_value(self, val: float):
        self._knob_value = val
        self._state_str_knob = self._control_hdr_str + f"{val}\n"
        self.message_tx_event(self._state_str_knob)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_dial_value(self) -> float:
        return self._knob_dial_value

    @knob_dial_value.setter
    def knob_dial_value(self, val: float):
        self._knob_dial_value = val
        self._state_str_dial = self._control_id_dial + f"{val}\n"
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
    def dial_min(self) -> float:
        return self._cfg["min"]

    @dial_min.setter
    def dial_min(self, val: float):
        self._cfg["min"] = val

    @property
    def dial_max(self) -> float:
        return self._cfg["max"]

    @dial_max.setter
    def dial_max(self, val: float):
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
