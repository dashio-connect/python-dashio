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
import copy
import json
import logging

from ..constants import BAD_CHARS
from .enums import ColorPickerStyle, DeviceViewStyle, DialNumberPosition, DirectionStyle, GraphXAxisLabelsStyle, Keyboard, KnobStyle, Precision,\
    TextAlignment, TitlePosition, Icon, Color, TextFormat, LabelStyle, SliderBarStyle, DialStyle, TimeGraphPositionOfKey
from .event import Event


def _get_icon(icon_str: str) -> Icon:
    icon_name = icon_str.upper().replace(" ", "")
    return Icon[icon_name]

def _get_color(color_str: str) -> Color:
    color_name = color_str.upper().replace(" ", "_")
    return Color[color_name]

def _get_title_position(position_str: str) -> TitlePosition:
    t_pos_name = position_str.upper().replace(" ", "")
    return TitlePosition[t_pos_name]

def _get_text_align(text_align_str: str) -> TextAlignment:
    t_align_name = text_align_str.upper().replace(" ", "")
    return TextAlignment[t_align_name]

def _get_text_format(text_format_str: str) -> TextFormat:
    t_format_name = text_format_str.upper().replace(" ", "")
    return TextFormat[t_format_name]

def _get_precision(precision_int: int) -> Precision:
    return Precision(precision_int)

def _get_keyboard_type(keyboard_str: str) -> Keyboard:
    t_keyboard = keyboard_str.upper().replace(" ", "")
    return Keyboard[t_keyboard]

def _get_device_view_style(device_vuew_style: str) -> DeviceViewStyle:
    dvs_name = device_vuew_style.upper().replace(" ", "")
    return DeviceViewStyle[dvs_name]

def _get_color_picker_style(color_picker_style: str) -> ColorPickerStyle:
    cps_name = color_picker_style.upper().replace(" ", "")
    return ColorPickerStyle[cps_name]

def _get_dial_number_position(dn_position_str: str) -> DialNumberPosition:
    dnp_name = dn_position_str.upper().replace(" ", "")
    return DialNumberPosition[dnp_name]

def _get_direction_style(dir_style_str: str) -> DirectionStyle:
    ds_name = dir_style_str.upper().replace(" ", "")
    return DirectionStyle[ds_name]

def _get_graph_x_axis_labels_style(gxal_style_str: str) -> GraphXAxisLabelsStyle:
    ds_name = gxal_style_str.upper().replace(" ", "")
    return GraphXAxisLabelsStyle[ds_name]

def _get_knob_style(knob_style_str: str) -> KnobStyle:
    ks_name = knob_style_str.upper().replace(" ", "")
    return KnobStyle[ks_name]

def _get_label_style(label_style_str: str) -> LabelStyle:
    ks_name = label_style_str.upper().replace(" ", "")
    return LabelStyle[ks_name]

def _get_bar_style(bar_style_str: str) -> SliderBarStyle:
    bs_name = bar_style_str.upper().replace(" ", "")
    return SliderBarStyle[bs_name]

def _get_dial_style(dial_style_str: str) -> DialStyle:
    bs_name = dial_style_str.upper().replace(" ", "")
    return DialStyle[bs_name]

def _get_time_graph_position_of_key(tgp_of_key: str) -> TimeGraphPositionOfKey:
    tgp_of_key = tgp_of_key.upper().replace(" ", "")
    return TimeGraphPositionOfKey[tgp_of_key]


class ControlPosition:
    """
    ControlPosition
        Used to describe a controls position.
    """
    def __init__(self, x_position_ratio: float, y_position_ratio: float, width_ratio: float, height_ratio: float):
        """The ControlPosition class describes the location and size of a control on a DeviceView. The
        x_postion and y_position ratio place the top left hand corner of the control. The width and height ratio
        describe the controls size. The ratio is a number betwwen 0 and 1 representing the width and height of the
        DeviceView.

        Parameters
        ----------
        x_position_ratio : float
            Left side position expressed as a ration between 0 and 1
        y_position_ratio : float
            Upper side position expressed as a ration between 0 and 1
        width_ratio : float
            Control width expressed as a ration between 0 and 1
        height_ratio : float
            Control height expressed as a ration between 0 and 1
        """
        self.x_position_ratio = x_position_ratio
        self.y_position_ratio = y_position_ratio
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio

class Control:
    """Base class for controls.
    """

    def get_state(self) -> str:
        """This is called by iotdashboard app. Controls need to implement their own version."""
        return ""

    def get_cfg(self, data):
        """Returns the CFG for the control called when the iotdashboard app asks for a CFG

        Parameters
        ----------
        data : list from IoTDashboard
            The command from IoTDashboard split on \t into a list

        Returns
        -------
        str
            The CFG for this control
        """
        try:
            num_columns = int(data[3])
            dashboard_id = data[2]
        except (IndexError, ValueError):
            return
        if self._control_position_column_3 and num_columns == 3:
            self._cfg["xPositionRatio"] = self._control_position_column_3.x_position_ratio
            self._cfg["yPositionRatio"] = self._control_position_column_3.y_position_ratio
            self._cfg["widthRatio"] = self._control_position_column_3.width_ratio
            self._cfg["heightRatio"] = self._control_position_column_3.height_ratio
        elif self._control_position_column_2 and num_columns == 2 or num_columns == 3:
            self._cfg["xPositionRatio"] = self._control_position_column_2.x_position_ratio
            self._cfg["yPositionRatio"] = self._control_position_column_2.y_position_ratio
            self._cfg["widthRatio"] = self._control_position_column_2.width_ratio
            self._cfg["heightRatio"] = self._control_position_column_2.height_ratio
        elif self._control_position_column_1:
            self._cfg["xPositionRatio"] = self._control_position_column_1.x_position_ratio
            self._cfg["yPositionRatio"] = self._control_position_column_1.y_position_ratio
            self._cfg["widthRatio"] = self._control_position_column_1.width_ratio
            self._cfg["heightRatio"] = self._control_position_column_1.height_ratio

        cfg_str = f"\tCFG\t{dashboard_id}\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str


    def __init__(self, cntrl_type: str, control_id: str, title=None, control_position=None, title_position=None):
        """Control base type - all controls have these charactoristics and methods.

        Parameters
        ----------
        cntrl_type : str
            The type of control to implement
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : [type], optional
            Title of the control, by default None
        control_position : ControlPosition, optional
            The position of the control on a DeviceView this sets for number of columns = 1, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        """
        # Dictionary to store CFG json
        self._cfg = {}
        self._title = None
        # Remove incompatible characters
        if title is not None:
            self.title = title.translate(BAD_CHARS)
        self._title_position = None
        if title_position is not None:
            self.title_position = title_position
        self.cntrl_type = cntrl_type.translate(BAD_CHARS)
        self.control_id = control_id.translate(BAD_CHARS)
        self.message_rx_event = Event()
        self.message_tx_event = Event()
        self._control_hdr_str = f"\t{{device_id}}\t{self.cntrl_type}\t{self.control_id}\t"
        self._control_position_column_1 = None
        self._control_position_column_2 = None
        self._control_position_column_3 = None
        if control_position is not None:
            self.control_position_column_1 = control_position

    @property
    def state_str(self) -> str:
        """The current state of the control

        Returns
        -------
        str
            The current state of the control
        """
        return self._control_hdr_str

    @state_str.setter
    def state_str(self, val):
        self.message_tx_event(val)

    # Use getter, setter properties to store the settings in the config dictionary
    @property
    def parent_id(self) -> str:
        """The parent control or deviceview this control belongs to

        Returns
        -------
        str
            The parent_id
        """
        return self._cfg["parentID"]

    @parent_id.setter
    def parent_id(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["parentID"] = _val

    @property
    def control_id(self) -> str:
        """The control id of the control

        Returns
        -------
        str
            The control id should be a unique string for all controls on a device
        """
        return self._cfg["controlID"]

    @control_id.setter
    def control_id(self, val: str):
        self._cfg["controlID"] = val

    @property
    def title(self) -> str:
        """The title of the control

        Returns
        -------
        str
            The title of the control thats is displayed on the iotdashboard app
        """
        return self._cfg["title"]

    @title.setter
    def title(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["title"] = _val

    @property
    def control_position_column_1(self) -> ControlPosition:
        """Control Position for 1 column device

        Returns:
            ControlPosition: The position of the control on the DeviceView
        """
        return self._control_position_column_1

    @control_position_column_1.setter
    def control_position_column_1(self, val: ControlPosition):
        self._control_position_column_1 = copy.copy(val)

    @property
    def control_position_column_2(self) -> ControlPosition:
        """Control Position for 2 column device

        Returns:
            ControlPosition: The position of the control on the DeviceView
        """
        return self._control_position_column_2

    @control_position_column_2.setter
    def control_position_column_2(self, val: ControlPosition):
        self._control_position_column_2 = copy.copy(val)

    @property
    def control_position_column_3(self) -> ControlPosition:
        """Control Position

        Returns:
            ControlPosition: The position of the control on the DeviceView
        """
        return self._control_position_column_3

    @control_position_column_3.setter
    def control_position_column_3(self, val: ControlPosition):
        self._control_position_column_3 = copy.copy(val)

    @property
    def title_position(self) -> TitlePosition:
        """Title position for 3 column device

        Returns:
            TitlePosition: The position of the title
        """
        return self._title_position

    @title_position.setter
    def title_position(self, val: TitlePosition):
        self._title_position = val
        self._cfg["titlePosition"] = val.value
