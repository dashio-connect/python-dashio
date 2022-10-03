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
from .control import Control, ControlPosition, _get_color, _get_title_position, _get_label_style
from .enums import Color, LabelStyle, TitlePosition


class Label(Control):
    """A Config only control"""

    def __init__(
        self,
        control_id: str,
        title="A label",
        title_position=TitlePosition.BOTTOM,
        color=Color.WHITE,
        style=LabelStyle.BASIC,
        control_position=None,
    ):
        """Label

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Label"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        color : Color, optional
            Color of the label, by default Color.WHITE
        style : LabelStyle, optional
            Style of label to be displayed, by default LabelStyle.BASIC
        """
        super().__init__("LBL", control_id, title=title, control_position=control_position, title_position=title_position)
        self.color = color
        self.style = style
        self._state_str = ""

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates a label from cfg dictionary

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
            _get_color(cfg_dict["color"]),
            _get_label_style(cfg_dict["style"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    @property
    def style(self) -> LabelStyle:
        """Label style

        Returns
        -------
        LabelStyle
            Style of label to display
        """
        return self._style

    @style.setter
    def style(self, val: LabelStyle):
        self._style = val
        self._cfg["style"] = val.value

    @property
    def color(self) -> Color:
        """Color

        Returns
        -------
        Color
            Clor of the label
        """
        return self._color

    @color.setter
    def color(self, val: Color):
        self._color = val
        self._cfg["color"] = str(val.value)
