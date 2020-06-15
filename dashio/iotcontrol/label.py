from .enums import Colour
from .control import Control


class Label(Control):
    """A Config only control"""

    def __init__(self,
                 control_id,
                 control_title='A label',
                 text='',
                 max_font_size=20,
                 text_colour=Colour.WHITE):
        super().__init__('LBL', control_id)
        self.title = control_title
        self.text = text
        self.max_font_size = max_font_size
        self.text_colour = text_colour
        self._state_str = ''

    @property
    def text(self) -> str:
        return self._cfg['text']

    @text.setter
    def text(self, val: str):
        self._cfg['text'] = val

    @property
    def max_font_size(self) -> int:
        return self._cfg['maxFontSize']

    @max_font_size.setter
    def max_font_size(self, val: int):
        self._cfg['maxFontSize'] = val

    @property
    def sent_text_colour(self) -> Colour:
        return self._sent_text_colour

    @sent_text_colour.setter
    def sent_text_colour(self, val: Colour):
        self._sent_text_colour = val
        self._cfg['textColour'] = str(val.value)
