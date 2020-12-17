from .enums import TextAlignment, Precision, Keyboard
from .control import Control


class TextBox(Control):
    def __init__(
        self,
        control_id,
        control_title="A Text Box",
        text="",
        text_align=TextAlignment.LEFT,
        number_of_rows=1,
        units="",
        precision=Precision.OFF,
        keyboard_type=Keyboard.ALL_CHARS,
        close_keyboard_on_send=True,
        control_position=None,
    ):
        super().__init__("TEXT", control_id, control_position=control_position)
        self.title = control_title
        self.text = text
        self.text_align = text_align
        self.number_of_rows = number_of_rows
        self.units = units
        self.precision = precision
        self.keyboard_type = keyboard_type
        self.close_keyboard_on_send = close_keyboard_on_send
        self._state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self.text)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, val):
        self._text = val
        self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self.text)

    @property
    def text_align(self) -> TextAlignment:
        return self._text_align

    @text_align.setter
    def text_align(self, val: TextAlignment):
        self._text_align = val
        self._cfg["textAlign"] = val.value

    @property
    def number_of_rows(self):
        return self._cfg["numberOfRows"]

    @number_of_rows.setter
    def number_of_rows(self, val):
        self._cfg["numberOfRows"] = val

    @property
    def units(self):
        return self._cfg["units"]

    @units.setter
    def units(self, val):
        self._cfg["units"] = val

    @property
    def precision(self):
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
