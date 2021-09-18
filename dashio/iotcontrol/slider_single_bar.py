"""slider_single_bar.py"""
from .control import Control
from .enums import Color, SliderBarType, TitlePosition


class SliderSingleBar(Control):
    """Single slider bar control
    """
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
        bar_style=SliderBarType.SEGMENTED,
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
        bar_style : SliderBarType, optional
            bar style, by default SliderBarType.SEGMENTED
        """
        super().__init__("SLDR", control_id, title=title, control_position=control_position, title_position=title_position)
        self._control_id_bar = f"\t{{device_id}}\tBAR\t{control_id}\t"

        self._bar1_value = 0.0
        self._slider_value = 0.0

        self.bar_min = bar_min
        self.bar_max = bar_max
        self.red_value = red_value
        self.show_min_max = show_min_max
        self.slider_enabled = slider_enabled
        self.send_only_on_release = send_only_on_release
        self.bar_follows_slider = bar_follows_slider
        self.bar_color = bar_color
        self.bar_style = bar_style
        self.knob_color = knob_color
        self._slider_state_str = self._control_hdr_str + f"{self._slider_value}\n"
        self._bar1_state_str = self._control_id_bar + f"{self._bar1_value}\n"
        self._bar_slider_state_str = self._slider_state_str + self._bar1_state_str

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
        self._bar1_state_str = self._control_id_bar + f"{self._bar1_value}\n"
        self.message_tx_event(self._bar1_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar1_state_str

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
        self.message_tx_event(self._slider_state_str)
        self._bar_slider_state_str = self._slider_state_str + self._bar1_state_str

    @property
    def bar_min(self) -> float:
        """min bar value

        Returns
        -------
        float
            min bar value
        """
        return self._cfg["min"]

    @bar_min.setter
    def bar_min(self, val: float):
        self._cfg["min"] = val

    @property
    def bar_max(self) -> float:
        """max bar value

        Returns
        -------
        float
            max bar value
        """
        return self._cfg["max"]

    @bar_max.setter
    def bar_max(self, val: float):
        self._cfg["max"] = val

    @property
    def red_value(self) -> float:
        """Red value

        Returns
        -------
        float
            position of the red value
        """
        return self._cfg["redValue"]

    @red_value.setter
    def red_value(self, val: float):
        self._cfg["redValue"] = val

    @property
    def show_min_max(self) -> bool:
        """[summary]

        Returns
        -------
        bool
            [description]
        """
        return self._cfg["showMinMax"]

    @show_min_max.setter
    def show_min_max(self, val: bool):
        self._cfg["showMinMax"] = val

    @property
    def slider_enabled(self) -> bool:
        """Slider enabled

        Returns
        -------
        bool
            slider enabled
        """
        return self._cfg["sliderEnabled"]

    @slider_enabled.setter
    def slider_enabled(self, val: bool):
        self._cfg["sliderEnabled"] = val

    @property
    def send_only_on_release(self) -> bool:
        """Send slider position on release

        Returns
        -------
        bool
            Set to false for data firehose
        """
        return self._cfg["sendOnlyOnRelease"]

    @send_only_on_release.setter
    def send_only_on_release(self, val: bool):
        self._cfg["sendOnlyOnRelease"] = val

    @property
    def bar_follows_slider(self) -> bool:
        """Set bar follows slider

        Returns
        -------
        bool
            Set to True for bar follows slider
        """
        return self._cfg["barFollowsSlider"]

    @bar_follows_slider.setter
    def bar_follows_slider(self, val: bool):
        self._cfg["barFollowsSlider"] = val

    @property
    def bar_color(self) -> Color:
        """bar color

        Returns
        -------
        Color
            The color of the bar
        """
        return self._bar_color

    @bar_color.setter
    def bar_color(self, val: Color):
        self._bar_color = val
        self._cfg["barColor"] = str(val.value)

    @property
    def bar_style(self) -> SliderBarType:
        """Slider bar style

        Returns
        -------
        SliderBarType
            Type of slider to display
        """
        return self._bar_style

    @bar_style.setter
    def bar_style(self, val: SliderBarType):
        self._bar_style = val
        self._cfg["barStyle"] = val.value

    @property
    def knob_color(self) -> Color:
        """Color of the slider Knob

        Returns
        -------
        Color
            slider knob color
        """
        return self._knob_color

    @knob_color.setter
    def knob_color(self, val: Color):
        self._knob_color = val
        self._cfg["knobColor"] = str(val.value)
