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
from ..constants import BAD_CHARS
from .control import Control, ControlPosition, ControlConfig, _get_title_position, _get_text_align, _get_text_format, _get_precision, _get_keyboard_type, _get_color_str, _get_caption_mode
from .enums import (
    Keyboard,
    Precision,
    TextAlignment,
    TextFormat,
    Color,
    TitlePosition,
    CaptionMode
)


class TextBoxConfig(ControlConfig):
    """TextBoxConfig"""

    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        text: str,
        text_align: TextAlignment,
        text_format: TextFormat,
        units: str,
        precision: Precision,
        keyboard_type: Keyboard,
        close_keyboard_on_send: bool,
        caption_mode: CaptionMode,
        replace: dict[str: str] | None,
        control_position: ControlPosition | None
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["text"] = text.translate(BAD_CHARS)
        self.cfg["textAlign"] = text_align.value
        self.cfg["format"] = text_format.value
        self.cfg["units"] = units.translate(BAD_CHARS)
        self.cfg["precision"] = precision.value
        self.cfg["kbdType"] = keyboard_type.value
        self.cfg["closeKbdOnSend"] = close_keyboard_on_send
        self.cfg["captionMode"] = caption_mode.value
        if replace is not None:
            for key, val in replace.items():
                for c in '\t\n':
                    if (c in key) or (c in val):
                        raise ValueError("Bad characters '\t\n' in replace dictionary.")
            self.cfg["replace"] = replace

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates TextBoxConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        TextBoxConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            "",
            _get_text_align(cfg_dict["textAlign"]),
            _get_text_format(cfg_dict["format"]),
            cfg_dict["units"],
            _get_precision(cfg_dict["precision"]),
            _get_keyboard_type(cfg_dict["kbdType"]),
            cfg_dict["closeKbdOnSend"],
            _get_caption_mode(cfg_dict["captionMode"]),
            cfg_dict["replace"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls


class TextBox(Control):
    """A TextBox control
    """

    def __init__(
        self,
        control_id: str,
        title="A Text Box",
        title_position=TitlePosition.BOTTOM,
        text="",
        text_align=TextAlignment.LEFT,
        text_format=TextFormat.NONE,
        units="",
        precision=Precision.OFF,
        keyboard_type=Keyboard.ALL,
        close_keyboard_on_send=True,
        caption_mode=CaptionMode.MSG,
        replace=None,
        control_position=None,
        column_no=1
    ):
        """A TextBox control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default None
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the **Dash** app, by default None
        text : str, optional
            Text for the textbox, by default ""
        text_align : TextAlignment, optional
            Text alignment, by default TextAlignment.LEFT
        text_format : TextFormat, optional
            Format of the text, by default TextFormat.NONE
        units : str, optional
            Units, by default ""
        precision : Precision, optional
            precision, by default Precision.OFF
        keyboard_type : Keyboard, optional
            Keyboard type for the textbox, by default Keyboard.ALL
        close_keyboard_on_send : bool, optional
            Set to True to close keyboard on close, by default True
        caption_mode: CaptionMode, optional default MSG
            CaptionMode.MSG is for when the caption receives messages to be displayed.
            CaptionMode.SENT is when the caption shows the last message the user has entered.
        replace: { str: str }
            Dictionary of replacement text key value replacements to be performed by the Text box in the App.
        column_no : int, optional default is 1. Must be 1..3
            The Dash App reports its screen size in columns. column_no allows you to specify which column no to load into.
            Each control can store three configs that define how the device looks for Dash apps installed on single column
            phones or 2 column fold out phones or 3 column tablets.
        """
        super().__init__("TEXT", control_id)
        self._app_columns_cfg[str(column_no)].append(
            TextBoxConfig(
                control_id,
                title,
                title_position,
                text,
                text_align,
                text_format,
                units,
                precision,
                keyboard_type,
                close_keyboard_on_send,
                caption_mode,
                replace,
                control_position
            )
        )
        self._color = Color.WHITE
        self._caption_color = Color.WHITE
        self.text = text.translate(BAD_CHARS)
        self.caption = ""

    def get_state(self):
        return self._control_hdr_str + f"{self.text}\n"

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict, column_no=1):
        """Instantiates TextBox from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        TextBox
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            "",
            _get_text_align(cfg_dict["textAlign"]),
            _get_text_format(cfg_dict["format"]),
            cfg_dict["units"],
            _get_precision(cfg_dict["precision"]),
            _get_keyboard_type(cfg_dict["kbdType"]),
            cfg_dict["closeKbdOnSend"],
            _get_caption_mode(cfg_dict["captionMode"]),
            cfg_dict.get("replace"),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            column_no
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    @property
    def text(self) -> str:
        """TextBox text

        Returns
        -------
        str
            Textbox text
        """
        return self._text

    @text.setter
    def text(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._text = _val
        color = _get_color_str(self._color)
        self.state_str = self._control_hdr_str + f"{_val}\t{color}\n"

    @property
    def caption(self) -> str:
        """Caption text

        Returns
        -------
        str
            Caption text
        """
        return self._caption

    @caption.setter
    def caption(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._caption = _val
        color = _get_color_str(self._caption_color)
        self.state_str = f"\t{{device_id}}\tTXTC\t{self.control_id}\t{_val}\t{color}\n"

    @property
    def color(self):
        """TextBox Color

        Returns
        -------
        Color
            Text Color
        """
        return self._color

    @color.setter
    def color(self, val):
        self._color = val

    @property
    def caption_color(self):
        """TextBox Caption Color

        Returns
        -------
        Color
            Caption Color
        """
        return self._caption_color

    @caption_color.setter
    def caption_color(self, val):
        self._caption_color = val
