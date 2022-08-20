"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from .enums import Color, SliderBarStyle, TitlePosition
from .control import ControlPosition, _get_title_position, _get_color, _get_bar_style
from .slider_single_bar import SliderSingleBar


class SliderDoubleBar(SliderSingleBar):
    """A double bar slyder control
    """
    def __init__(self,
                 control_id: str,
                 title="A Double Slider",
                 title_position=TitlePosition.BOTTOM,
                 bar_min=0.0,
                 bar_max=1000.0,
                 red_value=750,
                 show_min_max=False,
                 slider_enabled=True,
                 send_only_on_release=True,
                 bar_follows_slider=False,
                 bar_color=Color.BLUE,
                 knob_color=Color.RED,
                 bar_style=SliderBarStyle.SEGMENTED,
                 control_position=None,):
        super().__init__(control_id,
                         title,
                         title_position,
                         bar_min,
                         bar_max,
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

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates SliderDoubleBar from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        SliderDoubleBar
        """
        return cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["min"],
            cfg_dict["max"],
            cfg_dict["redValue"],
            cfg_dict["showMinMax"],
            cfg_dict["sliderEnabled"],
            cfg_dict["sendOnlyOnRelease"],
            cfg_dict["barFollowsSlider"],
            _get_color(cfg_dict["barColor"]),
            _get_color(cfg_dict["knobColor"]),
            _get_bar_style(["title"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )

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
        """bar2 value

        Returns
        -------
        float
            The value of bar2
        """
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
        self._slider_state_str = self._control_hdr_str + f"{self._slider_value}\n"
        self.message_tx_event(self._slider_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str
