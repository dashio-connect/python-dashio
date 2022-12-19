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
from .control import Control, ControlPosition, ControlConfig, _get_color, _get_title_position, _get_dial_number_position, _get_dial_style, _get_precision
from .enums import (Color, DialNumberPosition, DialStyle, Precision,
                    TitlePosition)


class DialConfig(ControlConfig):
    """DialConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        dial_min: float,
        dial_max: float,
        red_value: float,
        dial_fill_color: Color,
        pointer_color: Color,
        number_position: DialNumberPosition,
        show_min_max: bool,
        style: DialStyle,
        precision: Precision,
        units: str,
        control_position: ControlPosition
        ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["min"] = dial_min
        self.cfg["max"] = dial_max
        self.cfg["redValue"] = red_value
        self.cfg["dialFillColor"] = str(dial_fill_color.value)
        self.cfg["pointerColor"] = str(pointer_color.value)
        self.cfg["numberPosition"] = number_position.value
        self.cfg["showMinMax"] = show_min_max
        self.cfg["style"] = style.value
        self.cfg["precision"] = precision.value
        self.cfg["units"] = units

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates DialConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        DialConfig
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


class Dial(Control):
    """Dial Control"""

    def add_config_columnar(self, config: DialConfig):
        if isinstance(config, DialConfig):
            config.cfg["min"] = self.dial_min
            config.cfg["max"] = self.dial_max
            config.cfg["redValue"] = self.red_value
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

    def add_config_full_page(self, config: DialConfig):
        if isinstance(config, DialConfig):
            config.cfg["min"] = self.dial_min
            config.cfg["max"] = self.dial_max
            config.cfg["redValue"] = self.red_value
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

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
        control_position=None
    ):
        """Dial

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
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
        super().__init__("DIAL", control_id)
        self._cfg_columnar.append(
            DialConfig(
                control_id,
                title,
                title_position,
                dial_min,
                dial_max,
                red_value,
                dial_fill_color,
                pointer_color,
                number_position,
                show_min_max,
                style,
                precision,
                units,
                control_position
            )
        )
        self._dial_value = 0
        self._dial_min = dial_min
        self._dial_max = dial_max
        self._red_value = red_value

    @property
    def dial_min(self):
        """Return the minimum dial value"""
        return self._dial_min

    @property
    def dial_max(self):
        """Return the maximum dial value"""
        return self._dial_max

    @property
    def red_value(self):
        """Return the red value for the dial"""
        return self._red_value

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
