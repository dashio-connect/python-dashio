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
from .control import Control, ControlPosition, _get_title_position, _get_text_align, _get_text_format, _get_precision, _get_keyboard_type
from .enums import (Keyboard, Precision, TextAlignment, TextFormat,
                    TitlePosition)


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
        control_position=None,
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
            Position of the title when displayed on the iotdashboard app, by default None
        text : str, optional
            Text for the textbox, by default ""
        text_align : TextAlignment, optional
            Text alaignment, by default TextAlignment.LEFT
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
        """
        super().__init__("TEXT", control_id, title=title, control_position=control_position, title_position=title_position)
        self.text = text.translate(BAD_CHARS)
        self.text_align = text_align
        self.units = units
        self.precision = precision
        self.text_format = text_format
        self.keyboard_type = keyboard_type
        self.close_keyboard_on_send = close_keyboard_on_send

    def get_state(self):
        return self._control_hdr_str + f"{self.text}\n"


    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates TextBox from cfg dictionary

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
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
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
        self.state_str = self._control_hdr_str + f"{_val}\n"

    @property
    def text_align(self) -> TextAlignment:
        """How to align the text

        Returns
        -------
        TextAlignment
            Text alignment
        """
        return self._text_align

    @text_align.setter
    def text_align(self, val: TextAlignment):
        self._text_align = val
        self._cfg["textAlign"] = val.value

    @property
    def text_format(self) -> TextFormat:
        """[summary]

        Returns
        -------
        TextFormat
            [description]
        """
        return self._text_format

    @text_format.setter
    def text_format(self, val: TextFormat):
        self._text_format = val
        self._cfg["format"] = val.value

    @property
    def units(self) -> str:
        """Add units to the text string

        Returns
        -------
        str
            the units
        """
        return self._cfg["units"]

    @units.setter
    def units(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["units"] = _val

    @property
    def precision(self) -> Precision:
        """Apply a prescion to the text string if it is a number

        Returns
        -------
        Precision
            The prescion to use
        """
        return self._precision

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg["precision"] = val.value

    @property
    def keyboard_type(self) -> Keyboard:
        """Keyboard type to use when entering text"""
        return self._cfg["kbdType"]

    @keyboard_type.setter
    def keyboard_type(self, val: Keyboard):
        self._keyboard_type = val
        self._cfg["kbdType"] = val.value

    @property
    def close_keyboard_on_send(self) -> bool:
        """Close the keyboard on send

        Returns
        -------
        bool
            Set to True for the keyboard to close on send
        """
        return self._cfg["closeKbdOnSend"]

    @close_keyboard_on_send.setter
    def close_keyboard_on_send(self, val: bool):
        self._cfg["closeKbdOnSend"] = val
