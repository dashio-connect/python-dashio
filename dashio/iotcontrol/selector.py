from .control import Control
from .enums import Colour, TextAlignment

class Selector(Control):

# sentSelectionColour
# selection
    def __init__(self,
                 control_id,
                 control_title='A Selector',
                 max_font_size=20,
                 text_align=TextAlignment.LEFT,
                 sent_selection_colour=Colour.WHITE):
        super().__init__('SLCTR', control_id)
        self.title = control_title
        self.max_font_size = max_font_size
        self.text_align = text_align
        self.sent_selection_colour = sent_selection_colour
        self.selection_list = []

    def add_selection(self, text):
        self.selection_list.append(text)

    def send_selected(self, selected_text):
        if selected_text in self.selection_list:
            position = self.selection_list.index(selected_text)
            self.state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, position)

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
    def sent_selection_colour(self) -> Colour:
        return self._sent_selection_colour

    @sent_selection_colour.setter
    def sent_selection_colour(self, val: Colour):
        self._sent_selection_colour = val
        self._cfg['sentSelectionColour'] = str(val.value)
