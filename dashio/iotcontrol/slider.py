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
from .control import Control, ControlPosition, ControlConfig, _get_title_position, _get_color, _get_bar_style
from .enums import Color, SliderBarStyle, TitlePosition

class SliderConfig(ControlConfig):
    """SliderConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        bar_min: float,
        bar_max: float,
        red_value: float,
        show_min_max: bool,
        slider_enabled: bool,
        send_only_on_release: bool,
        bar_follows_slider: bool,
        bar_color: Color,
        knob_color: Color,
        bar_style: SliderBarStyle,
        control_position: ControlPosition,
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["redValue"] = red_value
        self.cfg["min"] = bar_min
        self.cfg["max"] = bar_max
        self.cfg["showMinMax"] = show_min_max
        self.cfg["sliderEnabled"] = slider_enabled
        self.cfg["sendOnlyOnRelease"] = send_only_on_release
        self.cfg["barFollowsSlider"] = bar_follows_slider
        self.cfg["barColor"] = str(bar_color.value)
        self.cfg["knobColor"] = str(knob_color.value)
        self.cfg["barStyle"] = bar_style.value

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates SliderConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        SliderConfig
        """
        tmp_cls = cls(
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
            _get_bar_style(cfg_dict["barStyle"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

class Slider(Control):
    """Single slider bar control
    """

    def add_config_columnar(self, config: SliderConfig):
        if isinstance(config, SliderConfig):
            config.cfg["min"] = self.bar_min
            config.cfg["max"] = self.bar_max
            config.cfg["redValue"] = self.red_value
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

    def add_config_full_page(self, config: SliderConfig):
        if isinstance(config, SliderConfig):
            config.cfg["min"] = self.bar_min
            config.cfg["max"] = self.bar_max
            config.cfg["redValue"] = self.red_value
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

    def __init__(
        self,
        control_id: str,
        title="A Single Slider",
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
        bar_style=SliderBarStyle.SEG,
        control_position=None,
    ):
        """[summary]

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Single SLider"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        bar_min : float, optional
            min bar value, by default 0.0
        bar_max : float, optional
            max bar vale, by default 1000.0
        red_value : int, optional
            red value, by default 750
        show_min_max : bool, optional
            show min max, by default False
        slider_enabled : bool, optional
            enable slider, by default True
        send_only_on_release : bool, optional
            send only on release, by default True
        bar_follows_slider : bool, optional
            bar follows slider, by default False
        bar_color : Color, optional
            bar color, by default Color.BLUE
        knob_color : Color, optional
            knob color, by default Color.RED
        bar_style : SliderBarStyle, optional
            bar style, by default SliderBarStyle.SEGMENTED
        """
        super().__init__("SLDR", control_id)
        self._cfg_columnar.append(
            SliderConfig(
                control_id,
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
                control_position
            )
        )


        self._control_id_bar = f"\t{{device_id}}\tBAR\t{control_id}\t"

        self._bar1_value = 0.0
        self._bar2_value = None
        self._slider_value = 0.0

        self._slider_state_str = self._control_hdr_str + f"{self._slider_value}\n"
        self._bar_state_str = self._control_id_bar + f"{self._bar1_value}\n"
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str

        self._bar_min=bar_min
        self._bar_max=bar_max
        self._red_value=red_value

    @property
    def bar_min(self):
        """Returns the minimum bar value"""
        return self._bar_min

    @property
    def bar_max(self):
        """Returns the maximum bar value"""
        return self._bar_max

    @property
    def red_value(self):
        """Returns the red value"""
        return self._red_value

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Slider from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Slider
        """
        tmp_cls = cls(
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
            _get_bar_style(cfg_dict["barStyle"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def get_state(self):
        return self._bar_slider_state_str

    @property
    def bar1_value(self) -> float:
        """bar 1 value

        Returns
        -------
        float
            the bar value
        """
        return self._bar1_value

    @bar1_value.setter
    def bar1_value(self, val: float):
        self._bar1_value = val

        if self._bar2_value is None:
            self._bar_state_str = self._control_id_bar + f"{self._bar1_value}\n"
        else:
            self._bar_state_str = self._control_id_bar + "{:.2f}\t{:.2f}\n".format(self._bar1_value, self._bar2_value)
        self._message_tx_event(self._bar_state_str)
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
        if self._bar2_value is None:
            self._bar_state_str = self._control_id_bar + f"{self._bar1_value}\n"
        else:
            self._bar_state_str = self._control_id_bar + "{:.2f}\t{:.2f}\n".format(self._bar1_value, self._bar2_value)
        self._message_tx_event(self._bar_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str

    @property
    def slider_value(self) -> float:
        """the slider value

        Returns
        -------
        float
            Slider value
        """
        return self._slider_value

    @slider_value.setter
    def slider_value(self, val: float):
        self._slider_value = val
        self._slider_state_str = self._control_hdr_str + f"{self._slider_value}\n"
        self._message_tx_event(self._slider_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar_state_str
