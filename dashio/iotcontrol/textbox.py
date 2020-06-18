from .enums import TextAlignment, Precision, Keyboard, Colour
from .control import Control


class TextBox(Control):

    def __init__(self,
                 control_id,
                 control_title='A Text Box',
                 text='',
                 max_font_size=20,
                 text_align=TextAlignment.LEFT,
                 number_of_rows=1,
                 units='',
                 precision=Precision.OFF,
                 keyboard_type=Keyboard.ALL_CHARS,
                 sent_text_colour=Colour.WHITE,
                 close_keyboard_on_send=True):
        super().__init__('TEXT', control_id)
        self.title = control_title
        self.text = text
        self.max_font_size = max_font_size
        self.text_align = text_align
        self.number_of_rows = number_of_rows
        self.units = units
        self.precision = precision
        self.keyboard_type = keyboard_type
        self.sent_text_colour = sent_text_colour
        self.close_keyboard_on_send = close_keyboard_on_send
        self._state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self.text)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, val):
        self._text = val
        self.state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self.text)

    @property
    def max_font_size(self):
        return self._cfg['maxFontSize']

    @max_font_size.setter
    def max_font_size(self, val):
        self._cfg['maxFontSize'] = val

    @property
    def text_align(self) -> TextAlignment:
        return self._text_align

    @text_align.setter
    def text_align(self, val: TextAlignment):
        self._text_align = val
        self._cfg['textAlign'] = val.value

    @property
    def number_of_rows(self):
        return self._cfg['numberOfRows']

    @number_of_rows.setter
    def number_of_rows(self, val):
        self._cfg['numberOfRows'] = val

    @property
    def units(self):
        return self._cfg['units']

    @units.setter
    def units(self, val):
        self._cfg['units'] = val

    @property
    def precision(self):
        return self._precision

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg['precision'] = val.value

    @property
    def keyboard_type(self) -> Keyboard:
        return self._cfg['kbdType']

    @keyboard_type.setter
    def keyboard_type(self, val: Keyboard):
        self._keyboard_type = val
        self._cfg['kbdType'] = val.value

    @property
    def sent_text_colour(self) -> Colour:
        return self._sent_text_colour

    @sent_text_colour.setter
    def sent_text_colour(self, val: Colour):
        self._sent_text_colour = val
        self._cfg['sentTextColour'] = str(val.value)

    @property
    def close_keyboard_on_send(self) -> bool:
        return self._cfg['closeKbdOnSend']

    @close_keyboard_on_send.setter
    def close_keyboard_on_send(self, val: bool):
        self._cfg['closeKbdOnSend'] = val