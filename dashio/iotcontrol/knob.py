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
from .control import Control, ControlPosition, _get_color, _get_title_position, _get_knob_style
from .enums import Color, KnobStyle, TitlePosition


class Knob(Control):
    """A Knob control
    """
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
        """A Knob control is a control with a dial and knob.

        Parameters
        ----------
        control_id : [type]
            [description]
        title : str, optional
            [description], by default "A Knob"
        title_position : [type], optional
            [description], by default TitlePosition.BOTTOM
        knob_style : [type], optional
            [description], by default KnobStyle.NORMAL
        dial_min : float, optional
            [description], by default 0.0
        dial_max : float, optional
            [description], by default 100.0
        red_value : float, optional
            [description], by default 75.0
        show_min_max : bool, optional
            [description], by default False
        send_only_on_release : bool, optional
            [description], by default True
        dial_follows_knob : bool, optional
            [description], by default False
        dial_color : [type], optional
            [description], by default Color.BLUE
        knob_color : [type], optional
            [description], by default Color.RED
        control_position : [type], optional
            [description], by default None
        """
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

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Knob from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Knob
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_knob_style(cfg_dict["style"]),
            cfg_dict["min"],
            cfg_dict["max"],
            cfg_dict["redValue"],
            cfg_dict["showMinMax"],
            cfg_dict["sendOnlyOnRelease"],
            cfg_dict["dialFollowsKnob"],
            _get_color(cfg_dict["dialColor"]),
            _get_color(cfg_dict["knobColor"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def get_state(self):
        return self._knob_dial_state_str

    @property
    def knob_value(self) -> float:
        """knob value

        Returns
        -------
        float
            The value of the knob
        """
        return self._knob_value

    @knob_value.setter
    def knob_value(self, val: float):
        self._knob_value = val
        self._state_str_knob = self._control_hdr_str + f"{val}\n"
        self.message_tx_event(self._state_str_knob)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_dial_value(self) -> float:
        """Knob dial value

        Returns
        -------
        float
            The knob dial value
        """
        return self._knob_dial_value

    @knob_dial_value.setter
    def knob_dial_value(self, val: float):
        self._knob_dial_value = val
        self._state_str_dial = self._control_id_dial + f"{val}\n"
        self.message_tx_event(self._state_str_dial)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_style(self) -> KnobStyle:
        """Knob style

        Returns
        -------
        KnobStyle
            The style of the knob
        """
        return self._knob_style

    @knob_style.setter
    def knob_style(self, val: KnobStyle):
        self._knob_style = val
        self._cfg["style"] = str(val.value)

    @property
    def dial_min(self) -> float:
        """Dial min

        Returns
        -------
        float
            The min value for the dial
        """
        return self._cfg["min"]

    @dial_min.setter
    def dial_min(self, val: float):
        self._cfg["min"] = val

    @property
    def dial_max(self) -> float:
        """Dial max

        Returns
        -------
        float
            The max value of the dial
        """
        return self._cfg["max"]

    @dial_max.setter
    def dial_max(self, val: float):
        self._cfg["max"] = val

    @property
    def red_value(self) -> float:
        """Knob red value

        Returns
        -------
        float
            The red value start from this value
        """
        return self._cfg["redValue"]

    @red_value.setter
    def red_value(self, val: float):
        self._cfg["redValue"] = val

    @property
    def show_min_max(self) -> bool:
        """Show min max

        Returns
        -------
        bool
            True to show min/max
        """
        return self._cfg["showMinMax"]

    @show_min_max.setter
    def show_min_max(self, val: bool):
        self._cfg["showMinMax"] = val

    @property
    def send_only_on_release(self) -> bool:
        """Send only on release

        Returns
        -------
        bool
            True for iotdashboard to send updates only when control released
        """
        return self._cfg["sendOnlyOnRelease"]

    @send_only_on_release.setter
    def send_only_on_release(self, val: bool):
        self._cfg["sendOnlyOnRelease"] = val

    @property
    def dial_follows_knob(self) -> bool:
        """Dial follows knob

        Returns
        -------
        bool
            Set to true if the Dial follows the Knob
        """
        return self._cfg["dialFollowsKnob"]

    @dial_follows_knob.setter
    def dial_follows_knob(self, val: bool):
        self._cfg["dialFollowsKnob"] = val

    @property
    def dial_color(self) -> Color:
        """The dial color

        Returns
        -------
        Color
            Color of the dial
        """
        return self._dial_color

    @dial_color.setter
    def dial_color(self, val: Color):
        self._dial_color = val
        self._cfg["dialColor"] = str(val.value)

    @property
    def knob_color(self) -> Color:
        """Knob color

        Returns
        -------
        Color
            The color of the Knob
        """
        return self._knob_color

    @knob_color.setter
    def knob_color(self, val: Color):
        self._knob_color = val
        self._cfg["knobColor"] = str(val.value)
