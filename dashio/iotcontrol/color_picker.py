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
from .control import Control
from .enums import (ColorPickerStyle, TitlePosition)


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
        title : [type], optional
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
        super().__init__("CLR", control_id, title=title, control_position=control_position, title_position=title_position)
        self.picker_style = style
        self.send_only_on_release = send_only_on_release
        self._color_value = "#4F5GA2"


    def get_state(self):
        return self._control_hdr_str + f"{self._color_value}\n"


    def send_color_rgb(self, red, green, blue):
        """Send color as #rrggbb for the given color values."""
        self._color_value = '#%02x%02x%02x' % (red, green, blue)
        self.state_str = self._control_hdr_str + f"{self._color_value}\n"


    def color_to_rgb(self, color_value:str) -> tuple:
        """Return (red, green, blue) for the color_value."""
        clr = color_value.lstrip('#')
        len_v = len(clr)
        return tuple(int(clr[i:i + len_v // 3], 16) for i in range(0, len_v, len_v // 3))


    @property
    def color_value(self) -> str:
        """Dial value

        Returns
        -------
        float
            The position of the dial
        """
        return self._dial_value

    @color_value.setter
    def color_value(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._color_value = _val
        self.state_str = self._control_hdr_str + f"{_val}\n"


    @property
    def style(self) -> ColorPickerStyle:
        """Color Picker style

        Returns
        -------
        ColorPickerStyle
            Style to use for the color picker control
        """
        return self._style

    @style.setter
    def style(self, val: ColorPickerStyle):
        self._style = val
        self._cfg["style"] = val.value


    @property
    def send_only_on_release(self) -> bool:
        """Send color on release

        Returns
        -------
        bool
            Set to false for data firehose
        """
        return self._cfg["sendOnlyOnRelease"]

    @send_only_on_release.setter
    def send_only_on_release(self, val: bool):
        self._cfg["sendOnlyOnRelease"] = val
