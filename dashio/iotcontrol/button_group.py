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
from .control import Control, ControlPosition, ControlConfig, _get_icon, _get_title_position
from .enums import Icon, TitlePosition


class ButtonGroupConfig(ControlConfig):
    """ButtonGroupConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        text: str,
        icon: Icon,
        grid_view: bool,
        control_position: ControlPosition,
        title_position: TitlePosition
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["text"] = text.translate(BAD_CHARS)
        self.cfg["iconName"] = icon.value
        self.cfg["gridView"] = grid_view

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates ButtonGroupConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        ButtonGroupConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            cfg_dict["text"],
            _get_icon(cfg_dict["iconName"]),
            cfg_dict["gridView"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            _get_title_position(cfg_dict["titlePosition"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

class ButtonGroup(Control):
    """ButtonGroup control that shows a popup of buttons.

    Attributes
    ----------
    control_id : str
        a unique identity string. The identity string must be a unique string for each ButtonGroup per device
    title: str
        A short title for the button group
    text : str
        The text that appears on the ButtonGroup

    Methods
    -------
    add_button(Button)
        Add a button to the ButtonGroup
    """

    def __init__(
        self,
        control_id,
        title="A Button Group",
        text="A Button group with Text",
        title_position=TitlePosition.BOTTOM,
        icon=Icon.MENU,
        grid_view=True,
        control_position=None,
    ):
        """ButtonGroup control that shows a popup of buttons.

        Parameters
        ----------
            control_id : str
                An unique control identity string. The control identity string must be a unique string for each control per device
            title : str, optional:
                [description]. Defaults to "A Button Group".
            text (str, optional):
                [description]. Defaults to "A Button group with Text".
            title_position ([type], optional):
                [description]. Defaults to TitlePosition.BOTTOM.
            icon ([type], optional):
                [description]. Defaults to Icon.MENU.
            grid_view (bool, optional):
                [description]. Defaults to True.
            control_position ([type], optional):
                [description]. Defaults to None.
        """
        super().__init__("BTGP", control_id)
        self._cfg_columnar.append(ButtonGroupConfig(control_id, title, text, icon, grid_view, control_position, title_position))
        
    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates ButtonGroup from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        ButtonGroup
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            cfg_dict["text"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_icon(cfg_dict["iconName"]),
            cfg_dict["gridView"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def add_button(self, control):
        """[summary]

        Parameters
        ----------
        control : [type]
            [description]

        Raises
        ------
        TypeError
            [description]
        """
        if isinstance(control, Button):
            control.parent_id = self.control_id
        else:
            raise TypeError("Only buttons are allowed")
