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
from __future__ import annotations
from .control import Control, ControlConfig, _get_color, _get_icon, _get_device_view_style, _get_color_str
from .enums import Color, Icon, DeviceViewStyle


class DeviceViewConfig(ControlConfig):
    """DeviceViewConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        style: DeviceViewStyle,
        icon_name: Icon,
        color: Color | str,
        share_column: bool,
        num_columns: int,
        control_title_box_color: Color | str,
        control_title_box_transparency: int,
        control_color: Color | str,
        control_border_color: Color | str,
        control_background_color: Color | str,
        control_title_font_size: int,
        control_max_font_size: int,
        control_background_transparency: int,
        num_grid_columns: int,
        num_grid_rows: int,
        user_tappable_color: Color | str = ''
    ) -> None:
        super().__init__(control_id, title, control_position=None, title_position=None)
        self.cfg["iconName"] = icon_name.value
        self.cfg["style"] = str(style.value)
        self.cfg["color"] = _get_color_str(color)
        self.cfg["shareColumn"] = share_column
        if 1 <= num_columns <= 10:
            self.cfg["numColumns"] = num_columns
        else:
            raise ValueError("num_columns must be in the range 1 to 10")
        self.cfg["ctrlTitleBoxColor"] = _get_color_str(control_title_box_color)
        if 0 <= control_title_box_transparency <= 100:
            self.cfg["ctrlTitleBoxTransparency"] = control_title_box_transparency
        else:
            raise ValueError("Value must be in the range 0 to 100")
        self.cfg["ctrlColor"] = _get_color_str(control_color)
        self.cfg["ctrlBorderColor"] = _get_color_str(control_border_color)
        self.cfg["ctrlBkgndColor"] = _get_color_str(control_background_color)
        self.cfg["ctrlTitleFontSize"] = control_title_font_size
        self.cfg["ctrlMaxFontSize"] = control_max_font_size
        if 0 <= control_background_transparency <= 100:
            self.cfg["ctrlBkgndTransparency"] = control_background_transparency
        else:
            raise ValueError("Value must be in the range 0 to 100")
        self.cfg["gridColumns"] = num_grid_columns
        self.cfg["gridRows"] = num_grid_rows
        self.cfg["ctrlUItapColor"] = _get_color_str(user_tappable_color)

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates DeviceViewConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        DeviceViewConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_device_view_style(cfg_dict["style"]),
            _get_icon(cfg_dict["iconName"]),
            _get_color(cfg_dict["color"]),
            cfg_dict["shareColumn"],
            cfg_dict["numColumns"],
            _get_color(cfg_dict["ctrlTitleBoxColor"]),
            cfg_dict["ctrlTitleBoxTransparency"],
            _get_color(cfg_dict["ctrlColor"]),
            _get_color(cfg_dict["ctrlBorderColor"]),
            _get_color(cfg_dict["ctrlBkgndColor"]),
            cfg_dict["ctrlTitleFontSize"],
            cfg_dict["ctrlMaxFontSize"],
            cfg_dict["ctrlBkgndTransparency"],
            cfg_dict["gridColumns"],
            cfg_dict["gridRows"],
            _get_color(cfg_dict.get("ctrlUItapColor", ''))
        )
        return tmp_cls


class DeviceView(Control):
    """A DeviceView provides a control that describes appearance and style of the group of controls
        that are displayed on this DeviceView by the **Dash** app.

    Attributes
    ----------
    control_id : str
       An unique control identity string. The control identity string must be a unique string for each control per device
       Each control inherits the DeviceViews Control settings
    title : str
        The controls title
    style : DeviceViewStyle
        The style of the DeviceView
    icon : Icon
        The Icon representing the DeviceView
    color : Color
        The color of the DeviceView
    share_column : Boolean
        Something something
    num_columns : int
        Number of columns for DeviceView
    control_title_box_color : Color
        Title box color for controls
    control_title_box_transparency : int
        Title box transparency for controls
    control_color : Color, default is Color.WHITE_SMOKE
        set the control color.
    control_border_color : Color, default is Color.WHITE_SMOKE
        Set the border color.
    control_background_color: Color, default is Color.BLACK,
        Set the background color.
    control_title_font_size : int, default is 16
        Size of the title font.
    control_max_font_size : int, default is 20
        Set the maximum font size.
    control_background_transparency : int, default is 0
        Background transparency of controls.
    num_grid_columns : int
        The num of grid columns on the edit view
    num_grid_rows : int
        The num of grid rows on the edit view
    user_tappable_color : Color
        The color of user table buttons on screen in controls
    column_no : int, optional default is 1. Must be 1..3
        The Dash App reports its screen size in columns. column_no allows you to specify which column no to load into.
        Each control can store three configs that define how the device looks for Dash apps installed on single column
        phones or 2 column fold out phones or 3 column tablets.


    Methods
    -------
    add_control(Control) :
        Add a control to the device view

    from_cfg_dict(dict) :
        A class method to instantiate a DeviceView object from a dictionary
    """

    def __init__(
        self,
        control_id,
        title="A DeviceView",
        style=DeviceViewStyle.BASIC,
        icon=Icon.SQUARE,
        color: Color | str = Color.BLACK,
        share_column=True,
        num_columns=1,
        control_title_box_color: Color | str = Color.BLACK,
        control_title_box_transparency=0,
        control_color: Color | str = Color.WHITE_SMOKE,
        control_border_color: Color | str = Color.WHITE_SMOKE,
        control_background_color: Color | str = Color.BLACK,
        control_title_font_size=16,
        control_max_font_size=20,
        control_background_transparency=0,
        num_grid_columns=22,
        num_grid_rows=32,
        user_tappable_color='',
        column_no=1
    ):
        super().__init__("DVVW", control_id)
        self._app_columns_cfg[str(column_no)].append(
            DeviceViewConfig(
                control_id,
                title,
                style,
                icon,
                color,
                share_column,
                num_columns,
                control_title_box_color,
                control_title_box_transparency,
                control_color,
                control_border_color,
                control_background_color,
                control_title_font_size,
                control_max_font_size,
                control_background_transparency,
                num_grid_columns,
                num_grid_rows,
                user_tappable_color
            )
        )
        self._state_str = ""

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict, column_no=1):
        """Instantiates DeviceView from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        DeviceView
        """
        return cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_device_view_style(cfg_dict["style"]),
            _get_icon(cfg_dict["iconName"]),
            _get_color(cfg_dict["color"]),
            cfg_dict["shareColumn"],
            cfg_dict["numColumns"],
            _get_color(cfg_dict["ctrlTitleBoxColor"]),
            cfg_dict["ctrlTitleBoxTransparency"],
            _get_color(cfg_dict["ctrlColor"]),
            _get_color(cfg_dict["ctrlBorderColor"]),
            _get_color(cfg_dict["ctrlBkgndColor"]),
            cfg_dict["ctrlTitleFontSize"],
            cfg_dict["ctrlMaxFontSize"],
            cfg_dict["ctrlBkgndTransparency"],
            cfg_dict["gridColumns"],
            cfg_dict["gridRows"],
            _get_color(cfg_dict.get("ctrlUItapColor", '')),
            column_no
        )

    def add_control(self, control):
        """Add a control to the DeviceView

        Parameters
        ----------
        control : Control
            The control to add
        """
        control.parent_id = self.control_id
