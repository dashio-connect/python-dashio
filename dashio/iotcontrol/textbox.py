from .enums import TextAlignment, Precision, Keyboard, TitlePosition, TextFormat
from .control import Control


class TextBox(Control):
    def __init__(
        self,
        control_id,
        title="A Text Box",
        title_position=TitlePosition.BOTTOM,
        text="",
        text_align=TextAlignment.LEFT,
        text_format=TextFormat.NONE,
        units="",
        precision=Precision.OFF,
        keyboard_type=Keyboard.ALL_CHARS,
        close_keyboard_on_send=True,
        control_position=None,
    ):
        super().__init__("TEXT", control_id, title=title, control_position=control_position, title_position=title_position)
        self.text = text
        self.text_align = text_align
        self.units = units
        self.precision = precision
        self.text_format = text_format
        self.keyboard_type = keyboard_type
        self.close_keyboard_on_send = close_keyboard_on_send

    def get_state(self):
        return self._state_str + f"{self.text}\n"

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, val):
        self._text = val
        self.state_str = self._state_str + f"{self.text}\n"

    @property
    def text_align(self) -> TextAlignment:
        return self._text_align

    @text_align.setter
    def text_align(self, val: TextAlignment):
        self._text_align = val
        self._cfg["textAlign"] = val.value

    @property
    def text_format(self) -> TextFormat:
        return self._text_format

    @text_format.setter
    def text_format(self, val: TextFormat):
        self._text_format = val
        self._cfg["format"] = val.value

    @property
    def units(self) -> str:
        return self._cfg["units"]

    @units.setter
    def units(self, val: str):
        self._cfg["units"] = val

    @property
    def precision(self) -> Precision:
        return self._precision

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg["precision"] = val.value

    @property
    def keyboard_type(self) -> Keyboard:
        return self._cfg["kbdType"]

    @keyboard_type.setter
    def keyboard_type(self, val: Keyboard):
        self._keyboard_type = val
        self._cfg["kbdType"] = val.value

    @property
    def close_keyboard_on_send(self) -> bool:
        return self._cfg["closeKbdOnSend"]

    @close_keyboard_on_send.setter
    def close_keyboard_on_send(self, val: bool):
        self._cfg["closeKbdOnSend"] = val
