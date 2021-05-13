from .slider_single_bar import SliderSingleBar
from .enums import Color, SliderBarType, TitlePosition

class SliderDoubleBar(SliderSingleBar):
    def __init__(self,
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
                 control_position=None,):
        super().__init__(control_id,
                         title,
                         title_position,
                         min,
                         max,
                         red_value,
                         show_min_max,
                         slider_enabled,
                         send_only_on_release,
                         bar_follows_slider,
                         bar_color,
                         knob_color,
                         bar_style,
                         control_position)

        self._bar2_value = 0.0
        self._bar_state_str = self._control_id_bar + "{:.2f}\t{:.2f}\n".format(self._bar1_value, self._bar2_value)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str

    @property
    def bar1_value(self) -> float:
        return self._bar1_value

    @bar1_value.setter
    def bar1_value(self, val: float):
        self._bar1_value = val
        self._bar_state_str = self._control_id_bar + "{:.2f}\t{:.2f}\n".format(val, self._bar2_value)
        self.message_tx_event(self._bar_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str

    @property
    def bar2_value(self) -> float:
        return self._bar2_value

    @bar2_value.setter
    def bar2_value(self, val: float):
        self._bar2_value = val
        self._bar_state_str = self._control_id_bar + "{:.2f}\t{:.2f}\n".format(self._bar1_value, val)
        self.message_tx_event(self._bar_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str

    @property
    def slider_value(self) -> float:
        return self._slider_value

    @slider_value.setter
    def slider_value(self, val: float):
        self._slider_value = val
        self._slider_state_str = self._state_str + f"{self._slider_value}\n"
        self.message_tx_event(self._slider_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str
