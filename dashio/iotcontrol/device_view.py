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
from .control import Control
from .enums import Color, Icon


class DeviceView(Control):
    """A DeviceView provides a control that descibes appearance and style of the group of controls
        that are displayed on this DeviceView by the iotdashboard app.

    Attributes
    ----------
    control_id : str
       An unique control identity string. The control identity string must be a unique string for each control per device
       Each control inherits the DeviceViews Control settings
    title : str
        The controls title
    icon : Icon
        The Icon representing the DeviceView
    color : Color
        The color of the DeviceView
    share_column : Booloan
        Something something
    num_columns : int
        Number of columns for DeviceView
    control_title_box_color : Color
        Title box color for controls
    control_title_box_transparency : int
        Title box transparency for controls


    Methods
    -------
    add_control(Control) :
        Add a control to the device view
    """

    def __init__(
        self,
        control_id,
        title="A DeviceView",
        icon=Icon.SQUARE,
        color=Color.BLACK,
        share_column = True,
        num_columns = 1,
        control_title_box_color=Color.BLACK,
        control_title_box_transparency=0,
        control_color=Color.WHITE_SMOKE,
        control_border_color=Color.WHITE_SMOKE,
        control_border_on=False,
        control_background_color=Color.BLACK,
        control_title_font_size=16,
        control_max_font_size=20,
        control_background_transparency=0,
    ):
        super().__init__("DVVW", control_id, title=title)
        self.icon_name = icon
        self.color = color
        self.share_column = share_column
        self.num_columns = num_columns
        self.control_title_box_color = control_title_box_color
        self.control_title_box_transparency = control_title_box_transparency
        self.control_color = control_color
        self.control_border_color = control_border_color
        self.control_border_on = control_border_on
        self.control_background_color = control_background_color
        self.control_title_font_size = control_title_font_size
        self.control_max_font_size = control_max_font_size
        self.control_background_transparency = control_background_transparency
        self._state_str = ""

    def add_control(self, control):
        """Add a control to the DeviceView

        Parameters
        ----------
        control : Control
            The control to add
        """
        control.parent_id = self.control_id

    @property
    def icon_name(self) -> Icon:
        """Icon name

        Returns
        -------
        Icon
            Icon for the DeviceView
        """
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value

    @property
    def share_column(self) -> bool:
        """[summary]

        Returns
        -------
        bool
            [description]
        """
        return self._cfg["shareColumn"]

    @share_column.setter
    def share_column(self, val: bool):
        self._cfg["shareColumn"] = val

    @property
    def num_columns(self) -> int:
        """[summary]

        Returns
        -------
        int
            Number of columns

        Raises
        ------
        ValueError
            The value must be 1 to 3
        """
        return self._cfg["numColumns"]

    @num_columns.setter
    def num_columns(self, val: int):
        if 1 <= val <= 3:
            self._cfg["numColumns"] = val
        else:
            raise ValueError("Value must be in the range 1 to 3")

    @property
    def color(self) -> Color:
        """Color

        Returns
        -------
        Color
            The device view color
        """
        return self._color

    @color.setter
    def color(self, val: Color):
        self._color = val
        self._cfg["color"] = str(val.value)

    @property
    def control_title_box_color(self) -> Color:
        """Control title box color

        Returns
        -------
        Color
            The control title box color
        """
        return self._control_title_box_color

    @control_title_box_color.setter
    def control_title_box_color(self, val: Color):
        self._control_title_box_color = val
        self._cfg["ctrlTitleBoxColor"] = str(val.value)

    @property
    def control_title_box_transparency(self) -> int:
        """Control Box title transparency

        Returns
        -------
        int
            The percent transparency of the control box title
        """
        return self._cfg["ctrlTitleBoxTransparency"]

    @control_title_box_transparency.setter
    def control_title_box_transparency(self, val: int):
        if 0 <= val <= 100:
            self._cfg["ctrlTitleBoxTransparency"] = val
        else:
            raise ValueError("Value must be in the range 0 to 100")

    @property
    def control_color(self) -> Color:
        """Controls color

        Returns
        -------
        Color
            The color of the control
        """
        return self._control_color

    @control_color.setter
    def control_color(self, val: Color):
        self._control_color = val
        self._cfg["ctrlColor"] = str(val.value)

    @property
    def control_border_color(self) -> Color:
        """Control border color

        Returns
        -------
        Color
            The control border color
        """
        return self._control_border_color

    @control_border_color.setter
    def control_border_color(self, val: Color):
        self._control_border_color = val
        self._cfg["ctrlBorderColor"] = str(val.value)

    @property
    def control_border_on(self) -> bool:
        """Control border display

        Returns
        -------
        bool
            Set to true to display the contol borders
        """
        return self._cfg["ctrlBorderOn"]

    @control_border_on.setter
    def control_border_on(self, val: bool):
        self._cfg["ctrlBorderOn"] = val

    @property
    def control_background_color(self) -> Color:
        """Control background color

        Returns
        -------
        Color
            The control background color
        """
        return self._control_background_color

    @control_background_color.setter
    def control_background_color(self, val: Color):
        self._control_background_color = val
        self._cfg["ctrlBkgndColor"] = str(val.value)

    @property
    def control_title_font_size(self) -> int:
        """Control title font size

        Returns
        -------
        int
            Control title font size
        """
        return self._cfg["ctrlTitleFontSize"]

    @control_title_font_size.setter
    def control_title_font_size(self, val: int):
        self._cfg["ctrlTitleFontSize"] = val

    @property
    def control_max_font_size(self) -> int:
        """Control max font size

        Returns
        -------
        int
            Max font size for a control
        """
        return self._cfg["ctrlMaxFontSize"]

    @control_max_font_size.setter
    def control_max_font_size(self, val: int):
        self._cfg["ctrlMaxFontSize"] = val

    @property
    def control_background_transparency(self) -> int:
        """Control background transparency

        Returns
        -------
        int
            the control background tranparency
        """
        return self._cfg["ctrlBkgndTransparency"]

    @control_background_transparency.setter
    def control_background_transparency(self, val: int):
        if 0 <= val <= 100:
            self._cfg["ctrlBkgndTransparency"] = val
        else:
            raise ValueError("Value must be in the range 0 to 100")
