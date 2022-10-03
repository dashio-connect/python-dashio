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
from .button import Button
from .control import Control, ControlPosition, _get_icon, _get_title_position
from .enums import Icon, TitlePosition
from .selector import Selector
from .slider import Slider
from .textbox import TextBox


class Menu(Control):
    """A Menu Control
    """

    def __init__(self,
                 control_id: str,
                 title="A Menu",
                 text="A Menu with Text",
                 icon=Icon.MENU,
                 control_position=None,
                 title_position=TitlePosition.BOTTOM):
        """A Menu control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Menu"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        text : str, optional
            Menu text, by default "A Menu with Text"
        icon : Icon, optional
            Menu icon, by default Icon.MENU
        """
        super().__init__("MENU", control_id, title=title, control_position=control_position, title_position=title_position)
        self.icon_name = icon
        self.text = text

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Menu from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Menu
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            cfg_dict["text"],
            _get_icon(cfg_dict["iconName"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            _get_title_position(cfg_dict["titlePosition"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def add_control(self, control):
        """Add a control to the menu

        Parameters
        ----------
        control : Control
            A control to add to the menu

        Raises
        ------
        TypeError
            Must be either TextBox, Button, Slider, Selector controls
        """
        if isinstance(control, (TextBox, Button, Slider, Selector)):
            control.parent_id = self.control_id
        else:
            raise TypeError("Only TextBox, Button, Slider, or Selector are allowed")

    @property
    def icon_name(self) -> Icon:
        """The icon for the menu

        Returns
        -------
        Icon
            The Icon
        """
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value

    @property
    def text(self) -> str:
        """Text displayed in iotdashboard app

        Returns
        -------
        str
            The text
        """
        return self._cfg["text"]

    @text.setter
    def text(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["text"] = _val
