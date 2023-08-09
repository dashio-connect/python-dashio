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
from .control import Control, ControlPosition, ControlConfig, _get_color, _get_icon, _get_title_position, _get_button_style, _get_color_str
from .enums import ButtonState, Color, Icon, TitlePosition, ButtonStyle


class ButtonConfig(ControlConfig):
    """ButtonGroupConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        button_enabled: bool,
        style: ButtonStyle,
        icon_name: Icon,
        on_color: Color,
        off_color: Color,
        text: str,
        control_position: ControlPosition
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["text"] = text.translate(BAD_CHARS)
        self.cfg["iconName"] = icon_name.value
        self.cfg["buttonEnabled"] = button_enabled
        self.cfg["style"] = str(style.value)
        self.cfg["onColor"] = _get_color_str(on_color)
        self.cfg["offColor"] = _get_color_str(off_color)

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
            cfg_dict.get("title", ''),
            _get_title_position(cfg_dict.get("titlePosition", 'bottom')),
            cfg_dict.get("buttonEnabled", True),
            _get_button_style(cfg_dict.get("style", 'basic')),
            _get_icon(cfg_dict.get("iconName", 'none')),
            _get_color(cfg_dict.get("onColor", 'blue')),
            _get_color(cfg_dict.get("offColor", 'red')),
            cfg_dict.get("text", ""),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls


class Button(Control):
    """A Button control.

    Attributes
    ----------
    control_id : str
        An unique control identity string. The control identity string must be a unique string for each control per device
    title: str
        A short title for the button group
    text : str
        The text that appears on the ButtonGroup
    title_position : TitlePosition
        Can be TitlePosition.BOTTOM, TitlePosition.TOP, TitlePosition.OFF
    button_enabled : boolean
        True allows the app to send button events. False disables button pushes
    stype : ButtonStyle
        The style of the button. Options are ButtonStyle.BASIC, ButtonStyle.HIGHLIGHT
    icon_name : Icon
        Set the icon for the button
    off_color : Color
        Set the off color
    on_color : Color
        Set the on color
    control_position : ControlPosition
        Set the size and position of the button on a DeviceView.
    column_no : int, optional default is 1. Must be 1..3
        The Dash App reports its screen size in columns. column_no allows you to specify which column no to load into.
        Each control can store three configs that define how the device looks for Dash apps installed on single column
        phones or 2 column fold out phones or 3 column tablets.

    Methods
    -------
    send_button(btn_state, btn_icon, text) :
        Updates the button state, button icon and text.

    from_cfg_dict(cfg_dict: dict) :
        Instatiates Button from cfg dictionary
    """

    def toggle_btn(self):
        """
        Toggles the current ButtonState
        """
        if self.btn_state == ButtonState.FLASH:
            return
        if self.btn_state == ButtonState.OFF:
            self.btn_state = ButtonState.ON
        else:
            self.btn_state = ButtonState.OFF

    def __init__(
        self,
        control_id,
        title="A Button",
        title_position=TitlePosition.BOTTOM,
        button_enabled=True,
        style=ButtonStyle.BASIC,
        icon_name=Icon.NONE,
        on_color=Color.BLUE,
        off_color=Color.RED,
        text="",
        control_position: ControlPosition = None,
        column_no=1
    ):
        super().__init__("BTTN", control_id)
        self._app_columns_cfg[str(column_no)].append(
            ButtonConfig(
                control_id,
                title,
                title_position,
                button_enabled,
                style,
                icon_name,
                on_color,
                off_color,
                text,
                control_position
            )
        )
        self._btn_state = ButtonState.OFF
        self._text = text.translate(BAD_CHARS)
        self._icon_name = icon_name

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict, column_no=1):
        """Instatiates Button from cfg dictionary

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
            cfg_dict["buttonEnabled"],
            _get_button_style(cfg_dict.get("style", 'basic')),
            _get_icon(cfg_dict["iconName"]),
            _get_color(cfg_dict["onColor"]),
            _get_color(cfg_dict["offColor"]),
            cfg_dict["text"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            column_no
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def get_state(self):
        """get_state is called by iotdashboard

        Returns
        -------
        str
            The controls state
        """
        text = self._text
        if (not text) and (self.icon_name == Icon.NONE):
            return self._control_hdr_str + f"{self._btn_state.value}\n"
        if (not text) and self.icon_name != Icon.NONE:
            return self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\n"
        return self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\t{text}\n"

    @property
    def icon_name(self) -> Icon:
        """Returns the Icon the Button is set too

        Returns
        -------
        Icon
            The Icon the button is currently set to
        """
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self.state_str = self._control_hdr_str + f"{self._btn_state.value}\t{val.value}\n"

    @property
    def text(self) -> str:
        """Return the Buttons current text string

        Returns
        -------
        str
            The buttons text.
        """

        return self._text

    @text.setter
    def text(self, val: str):
        self._text = val.translate(BAD_CHARS)
        self.state_str = self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\t{self._text}\n"

    @property
    def btn_state(self) -> ButtonState:
        """
        Returns the state of the button.
        """
        return self._btn_state

    @btn_state.setter
    def btn_state(self, val: ButtonState):
        self._btn_state = val
        self.state_str = self._control_hdr_str + f"{val.value}\n"

    def send_button(self, btn_state: ButtonState, btn_icon: Icon, text: str):
        """Sends the button state to **DashIO** app.

        Parameters
        ----------
        btn_state : ButtonState
            State of the button
        btn_icon : Icon
            Icon to send
        text : str
            Text to send.
        """
        self._btn_state = btn_state
        self._icon_name = btn_icon
        self._text = text.translate(BAD_CHARS)
        self.state_str = self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\t{self._text}\n"
