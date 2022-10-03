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
from ..constants import BAD_CHARS
from .control import Control, ControlPosition, _get_color, _get_title_position, _get_dial_number_position, _get_dial_style, _get_precision
from .enums import (Color, DialNumberPosition, DialStyle, Precision,
                    TitlePosition)


class Dial(Control):
    """Dial Control
    """
    def __init__(
        self,
        control_id: str,
        title="A Dial",
        title_position=TitlePosition.BOTTOM,
        dial_min=0.0,
        dial_max=100.0,
        red_value=75.0,
        dial_fill_color=Color.RED,
        pointer_color=Color.BLUE,
        number_position=DialNumberPosition.LEFT,
        show_min_max=False,
        style=DialStyle.PIE,
        precision=Precision.OFF,
        units="",
        control_position=None,
    ):
        """Dial

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : [type], optional
            Title of the control, by default None
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        dial_min : float, optional
            Minimum dial position, by default 0.0
        dial_max : float, optional
            Maximum dial position, by default 100.0
        red_value : float, optional
            Position for red part of dial, by default 75.0
        dial_fill_color : Color, optional
            Dial fill color, by default Color.RED
        pointer_color : Color, optional
            Pointer color, by default Color.BLUE
        number_position : DialNumberPosition, optional
            Position of the number on the dial, by default DialNumberPosition.LEFT
        show_min_max : bool, optional
            True to show min max, by default False
        style : DialStyle, optional
            Dial style, by default DialStyle.PIE
        precision : Precision, optional
            Precision of the displayed number, by default Precision.OFF
        units : str, optional
            Units of the dial position, by default ""
        """
        super().__init__("DIAL", control_id, title=title, control_position=control_position, title_position=title_position)
        self._dial_value = 0
        self.dial_min = dial_min
        self.dial_max = dial_max
        self.red_value = red_value
        self.dial_fill_color = dial_fill_color
        self.pointer_color = pointer_color
        self.number_position = number_position
        self.show_min_max = show_min_max
        self.style = style
        self.precision = precision
        self.units = units

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Dial from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Dial
        """
        
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["min"],
            cfg_dict["max"],
            cfg_dict["redValue"],
            _get_color(cfg_dict["dialFillColor"]),
            _get_color(cfg_dict["pointerColor"]),
            _get_dial_number_position(cfg_dict["numberPosition"]),
            cfg_dict["showMinMax"],
            _get_dial_style(cfg_dict["style"]),
            _get_precision(cfg_dict["precision"]),
            cfg_dict["units"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def get_state(self):
        return self._control_hdr_str + f"{self._dial_value}\n"

    @property
    def dial_value(self) -> float:
        """Dial value

        Returns
        -------
        float
            The position of the dial
        """
        return self._dial_value

    @dial_value.setter
    def dial_value(self, val: float):
        self._dial_value = val
        self.state_str = self._control_hdr_str + f"{val}\n"

    @property
    def dial_min(self) -> float:
        """Dial min

        Returns
        -------
        float
            Minimum dial position
        """
        return self._cfg["min"]

    @dial_min.setter
    def dial_min(self, val: float):
        self._cfg["min"] = val

    @property
    def dial_max(self) -> float:
        """Dial Max

        Returns
        -------
        float
            Maximum position of the dial
        """
        return self._cfg["max"]

    @dial_max.setter
    def dial_max(self, val: float):
        self._cfg["max"] = val

    @property
    def red_value(self) -> float:
        """Red value

        Returns
        -------
        float
            The start of the red part of the dial
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
            True to show min max values
        """
        return self._cfg["showMinMax"]

    @show_min_max.setter
    def show_min_max(self, val: bool):
        self._cfg["showMinMax"] = val

    @property
    def dial_fill_color(self) -> Color:
        """Dial fill color

        Returns
        -------
        Color
            The color of the dial
        """
        return self._dial_fill_color

    @dial_fill_color.setter
    def dial_fill_color(self, val: Color):
        self._dial_fill_color = val
        self._cfg["dialFillColor"] = str(val.value)

    @property
    def pointer_color(self) -> Color:
        """Pointer color

        Returns
        -------
        Color
            The color of the pointer
        """
        return self._pointer_color

    @pointer_color.setter
    def pointer_color(self, val: Color):
        self._pointer_color = val
        self._cfg["pointerColor"] = str(val.value)

    @property
    def number_position(self) -> DialNumberPosition:
        """Number position

        Returns
        -------
        DialNumberPosition
            Position to display the number on the dial
        """
        return self._number_position

    @number_position.setter
    def number_position(self, val: DialNumberPosition):
        self._number_position = val
        self._cfg["numberPosition"] = val.value

    @property
    def style(self) -> DialStyle:
        """The style of the dial

        Returns
        -------
        DialStyle
            Which style of Dial to display
        """
        return self._style

    @style.setter
    def style(self, val: DialStyle):
        self._style = val
        self._cfg["style"] = val.value

    @property
    def precision(self) -> Precision:
        """Precision

        Returns
        -------
        Precision
            The precision of the value that is displayed
        """
        return self._cfg["precision"]

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg["precision"] = val.value

    @property
    def units(self) -> str:
        """units

        Returns
        -------
        str
            Include these units to be displayed with the value
        """
        return self._cfg["units"]

    @units.setter
    def units(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["units"] = _val
