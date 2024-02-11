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
import json

from ..constants import BAD_CHARS
from .enums import ColorPickerStyle, DeviceViewStyle, DialNumberPosition, DirectionStyle, ChartXAxisLabelsStyle, \
    Keyboard, KnobStyle, Precision, TextAlignment, TitlePosition, Icon, Color, TextFormat, LabelStyle, SliderBarStyle, \
    DialStyle, TimeGraphPositionOfKey, ButtonStyle, ButtonGroupStyle, MenuStyle
from .event import Event


def _get_icon(icon_str: str) -> Icon:
    icon_name = icon_str.upper().replace(" ", "_")
    return Icon[icon_name]


def _get_color_str(color) -> str:
    if isinstance(color, str):
        if color[0] == '#':
            return color
    return str(color.value)


def _get_color(color_str: str) -> Color:
    if color_str[0] == '#':
        return color_str
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


def _get_button_style(button_style: str) -> ButtonStyle:
    btn_style = button_style.upper()
    return ButtonStyle[btn_style]


def _get_menu_style(button_style: str) -> MenuStyle:
    menu_style = button_style.upper()
    return MenuStyle[menu_style]


def _get_button_group_style(button_group_style: str) -> ButtonGroupStyle:
    btn_grp_style = button_group_style.upper()
    return ButtonGroupStyle[btn_grp_style]


def _get_device_view_style(device_view_style: str) -> DeviceViewStyle:
    dvs_name = device_view_style.upper().replace(" ", "")
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


def _get_chart_x_axis_labels_style(gxal_style_str: str) -> ChartXAxisLabelsStyle:
    ds_name = gxal_style_str.upper().replace(" ", "")
    return ChartXAxisLabelsStyle[ds_name]


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


class ControlConfig:
    """Base ControlConfig"""
    def get_cfg_json(self) -> str:
        """Returns the CFG str for the control called when the iotdashboard app asks for a CFG

        Parameters
        ----------
        data : list from IoTDashboard
            The command from IoTDashboard split on \t into a list

        Returns
        -------
        str
            The CFG for this control
        """
        cfg_str = json.dumps(self.cfg) + "\n"

        return cfg_str

    def get_cfg64(self) -> dict:
        """Returns the CFG dict for the control called when the iotdashboard app asks for a CFG

        Parameters
        ----------
        data : list from IoTDashboard
            The command from IoTDashboard split on \t into a list

        Returns
        -------
        dict
            The CFG dict for this control
        """
        return self.cfg

    def update_position(self, control_position: ControlPosition):
        """Updates the controls position from control_position

        Parameters
        ----------
        control_position : ControlPosition
            The position to use to update the control
        """
        self.cfg["xPositionRatio"] = control_position.x_position_ratio
        self.cfg["yPositionRatio"] = control_position.y_position_ratio
        self.cfg["widthRatio"] = control_position.width_ratio
        self.cfg["heightRatio"] = control_position.height_ratio

    def __init__(
        self,
        control_id: str,
        title: str,
        control_position: ControlPosition,
        title_position: TitlePosition

    ) -> None:
        self.cfg = {}
        if title is not None:
            self.cfg["title"] = title.translate(BAD_CHARS)
        self._title_position = None
        if title_position is not None:
            self.cfg["titlePosition"] = title_position.value
        if control_position is not None:
            self.cfg["xPositionRatio"] = control_position.x_position_ratio
            self.cfg["yPositionRatio"] = control_position.y_position_ratio
            self.cfg["widthRatio"] = control_position.width_ratio
            self.cfg["heightRatio"] = control_position.height_ratio
        self.cfg["controlID"] = control_id.translate(BAD_CHARS)
        self.cfg["parentID"] = ""

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instatiates Dial from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        ControlConfig
        """

        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            _get_title_position(cfg_dict["titlePosition"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    @property
    def parent_id(self) -> str:
        """The parent control or deviceview this control belongs to

        Returns
        -------
        str
            The parent_id
        """
        return self.cfg["parentID"]

    @parent_id.setter
    def parent_id(self, val: str):
        _val = val.translate(BAD_CHARS)
        self.cfg["parentID"] = _val


class Control():
    """Base class for controls. """

    def get_state(self) -> str:
        """This is called by iotdashboard app. Controls need to implement their own version."""
        return ""

    def get_cfg(self, data) -> list:
        """Returns the CFG str for the control called when the iotdashboard app asks for a CFG

        Parameters
        ----------
        data : list from IoTDashboard
            The command from IoTDashboard split on \t into a list

        Returns
        -------
        str
            The CFG for this control
        """
        cfg_list = []
        try:
            num_columns = int(data[3])
            dashboard_id = data[2]
        except (IndexError, ValueError):
            return cfg_list
        if 1 <= num_columns <= self._cfg_max_no_columns:
            while num_columns >= 1:
                cfgs = self._app_columns_cfg[str(num_columns)]
                if cfgs:
                    for cfg in cfgs:
                        cfg_list.append(f"\tCFG\t{dashboard_id}\t{self.cntrl_type}\t{cfg.get_cfg_json()}")
                    break
                num_columns = num_columns - 1
        return cfg_list

    def get_cfg64(self, data) -> list:
        """Returns the CFG dict for the control called when the iotdashboard app asks for a CFG

        Parameters
        ----------
        data : list from IoTDashboard
            The command from IoTDashboard split on \t into a list

        Returns
        -------
        dict
            The CFG dict for this control
        """
        cfg_list = []
        try:
            num_columns = int(data[3])
        except (IndexError, ValueError):
            return []
        if 1 <= num_columns <= self._cfg_max_no_columns:
            cfgs = self._app_columns_cfg[str(num_columns)]
            if cfgs:
                for cfg in cfgs:
                    cfg_list.append(cfg.get_cfg64())
                return cfg_list
            num_columns = 1
            while num_columns <= 3:
                cfgs = self._app_columns_cfg[str(num_columns)]
                if cfgs:
                    for cfg in cfgs:
                        cfg_list.append(cfg.get_cfg64())
                    break
                num_columns = num_columns + 1
        return cfg_list

    def add_config(self, config, column_no=1):
        """Add a duplicate Config for dashio Apps with wider screens"""
        config.cfg["controlID"] = self.control_id
        if 1 <= column_no <= self._cfg_max_no_columns:
            self._app_columns_cfg[str(column_no)].append(config)

    def add_receive_message_callback(self, callback):
        """Add a callback to receive incoming messages to the control."""
        self._message_rx_event += callback

    def remove_receive_message_callback(self, callback):
        """Remaove a callback from receive incoming messages to the control."""
        self._message_rx_event -= callback

    def add_transmit_message_callback(self, callback):
        """Add a callback for transmitted messages from the control."""
        self._message_tx_event += callback

    def remove_transmit_message_callback(self, callback):
        """Remove a callback for transmitted messages from the control."""
        self._message_tx_event -= callback

    def __init__(self, cntrl_type: str, control_id: str):
        """Control base type - all controls have these charactoristics and methods.

        Parameters
        ----------
        cntrl_type : str
            The type of control to implement
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        """
        # List to store control CFG json
        self._app_columns_cfg = {
            '1': [],
            '2': [],
            '3': []
        }

        self._is_active = False

        self._cfg_max_no_columns = 3
        self.cntrl_type = cntrl_type.translate(BAD_CHARS)
        self.control_id = control_id.translate(BAD_CHARS)
        if not self.control_id:
            raise ValueError('control_id cannot be an empty string')
        self._message_rx_event = Event()
        self._message_tx_event = Event()
        # This may break things but makes all controls able to be setup from tasks.
        self._message_rx_event += self._message_tx_event
        self._control_hdr_str = f"\t{{device_id}}\t{self.cntrl_type}\t{self.control_id}\t"

    def del_config(self, column_no=1):
        """Deletes all the columnar config layout entries"""
        self._app_columns_cfg[str(column_no)] = []

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
        self._message_tx_event(val)

    #  Use getter, setter properties to store the settings in the config dictionary
    @property
    def parent_id(self, index=0, column_no=1) -> str:
        """The parent control or deviceview this control belongs to

        Returns
        -------
        str
            The parent_id
        """
        if not 1 <= column_no <= self._cfg_max_no_columns:
            column_no = 1
        return self._app_columns_cfg[str(column_no)][index]["parentID"]

    @parent_id.setter
    def parent_id(self, val: str, index=0, column_no=1):
        _val = val.translate(BAD_CHARS)
        if not 1 <= column_no <= self._cfg_max_no_columns:
            column_no = 1
        self._app_columns_cfg[str(column_no)][index].parent_id = _val
