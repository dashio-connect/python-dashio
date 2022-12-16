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
from .control import Control, ControlPosition, ControlConfig, _get_title_position, _get_color_picker_style
from .enums import (ColorPickerStyle, TitlePosition)



class ColorPickerConfig(ControlConfig):
    """ColorPickerConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        style: ColorPickerStyle,
        send_only_on_release: bool,
        control_position: ControlPosition
        ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["style"] = style.value
        self.cfg["sendOnlyOnRelease"] = send_only_on_release

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates ColorPickerConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        ColorPickerConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_color_picker_style(cfg_dict["pickerStyle"]),
            cfg_dict["sendOnlyOnRelease"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

class ColorPicker(Control):
    """Color Picker Control
    """

    def __init__(
        self,
        control_id: str,
        title="A Color Picker",
        title_position=TitlePosition.BOTTOM,
        style=ColorPickerStyle.WHEEL,
        send_only_on_release=True,
        control_position=None,
    ):
        """ColorPicker

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
        picker_style: ColorPickerStyle, optional
            The style of color picker to use.
        send_only_on_release: Boolean
            send only on release, by default True

        """
        super().__init__("CLR", control_id)
        self._cfg_columnar.append(
            ColorPickerConfig(
                control_id,
                title,
                title_position,
                style,
                send_only_on_release,
                control_position
            )
        )
        self._color_value = "#4F5GA2"


    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates ColorPicker from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Button
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_color_picker_style(cfg_dict["pickerStyle"]),
            cfg_dict["sendOnlyOnRelease"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls


    def get_state(self):
        return self._control_hdr_str + f"{self._color_value}\n"


    def send_color_rgb(self, red: int, green: int, blue: int):
        """Send color as #rrggbb for the given color values."""
        self._color_value = f"#{red:02x}{green:02x}{blue:02x}"
        self.state_str = self._control_hdr_str + f"{self._color_value}\n"


    def color_to_rgb(self, color_value:str) -> tuple:
        """Return (red, green, blue) for the color_value."""
        clr = color_value.lstrip('#')
        len_v = len(clr)
        return tuple(int(clr[i:i + len_v // 3], 16) for i in range(0, len_v, len_v // 3))


    @property
    def color_value(self) -> str:
        """Color value

        Returns
        -------
        str
            The color value as #rrggbb
        """
        return self._color_value

    @color_value.setter
    def color_value(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._color_value = _val
        self.state_str = self._control_hdr_str + f"{_val}\n"
