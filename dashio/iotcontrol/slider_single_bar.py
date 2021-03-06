from .enums import Color, SliderBarType, TitlePosition
from .control import Control


class SliderSingleBar(Control):
    def __init__(
        self,
        control_id,
        title="A Single Slider",
        title_position=TitlePosition.BOTTOM,
        min=0.0,
        max=1000.0,
        red_value=750,
        show_min_max=False,
        slider_enabled=True,
        send_only_on_release=True,
        bar_follows_slider=False,
        bar_color=Color.BLUE,
        knob_color=Color.RED,
        bar_style=SliderBarType.SEGMENTED,
        control_position=None,
    ):
        super().__init__("SLDR", control_id, control_position=control_position, title_position=title_position)
        self.title = title
        self._control_id_bar = "BAR"

        self._bar1_value = 0.0
        self._slider_value = 0.0

        self.min = min
        self.max = max
        self.red_value = red_value
        self.show_min_max = show_min_max
        self.slider_enabled = slider_enabled
        self.send_only_on_release = send_only_on_release
        self.bar_follows_slider = bar_follows_slider
        self.bar_color = bar_color
        self.bar_style = bar_style
        self.knob_color = knob_color
        self._slider_state_str = self._state_str + "{}\n".format(self._slider_value)
        self._bar1_state_str = self._state_str + "{}\n".format(self._bar1_value)
        self._bar1_slider_state_str = self._slider_state_str + self._bar1_state_str

    def get_state(self):
        return self._bar1_slider_state_str

    @property
    def bar1_value(self) -> float:
        return self._bar1_value

    @bar1_value.setter
    def bar1_value(self, val: float):
        self._bar1_value = val
        self._bar1_state_str = self._state_str + "{}\n".format(self._bar1_value)
        self.message_tx_event(self._bar1_state_str)
        self._bar1_slider_state_str = self._slider_state_str + self._bar1_state_str

    @property
    def slider_value(self) -> float:
        return self._slider_value

    @slider_value.setter
    def slider_value(self, val: float):
        self._slider_value = val
        self._slider_state_str = self._state_str + "{}\n".format(self._slider_value)
        self.message_tx_event(self._slider_state_str)
        self._bar1_slider_state_str = self._slider_state_str + self._bar1_state_str

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
    def slider_enabled(self) -> bool:
        return self._cfg["sliderEnabled"]

    @slider_enabled.setter
    def slider_enabled(self, val: bool):
        self._cfg["sliderEnabled"] = val

    @property
    def send_only_on_release(self) -> bool:
        return self._cfg["sendOnlyOnRelease"]

    @send_only_on_release.setter
    def send_only_on_release(self, val: bool):
        self._cfg["sendOnlyOnRelease"] = val

    @property
    def bar_follows_slider(self) -> bool:
        return self._cfg["barFollowsSlider"]

    @bar_follows_slider.setter
    def bar_follows_slider(self, val: bool):
        self._cfg["barFollowsSlider"] = val

    @property
    def bar_color(self) -> Color:
        return self._bar_color

    @bar_color.setter
    def bar_color(self, val: Color):
        self._bar_color = val
        self._cfg["barColor"] = str(val.value)

    @property
    def bar_style(self) -> SliderBarType:
        return self._bar_style

    @bar_style.setter
    def bar_style(self, val: SliderBarType):
        self._bar_style = val
        self._cfg["barStyle"] = val.value

    @property
    def knob_color(self) -> Color:
        return self._knob_color

    @knob_color.setter
    def knob_color(self, val: Color):
        self._knob_color = val
        self._cfg["knobColor"] = str(val.value)
