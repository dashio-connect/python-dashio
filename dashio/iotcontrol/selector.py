from .control import Control
from .enums import Colour, TextAlignment


class Selector(Control):

    def __init__(self,
                 control_id,
                 control_title='A Selector',
                 max_font_size=20,
                 text_align=TextAlignment.LEFT,
                 background_colour=Colour.BLUE,
                 text_colour=Colour.WHITE_SMOKE,
                 title_bar_colour=Colour.RED,
                 control_position=None):
        super().__init__('SLCTR', control_id, control_position=control_position)
        self.title = control_title
        self.text_align = text_align
        self.selection_list = []
        self._position = 0
        self.background_colour = background_colour
        self.text_colour = text_colour
        self.title_bar_colour = title_bar_colour
        self._cfg['selection'] = self.selection_list

    def get_state(self):
        _state_str = '\t{}\t{}\t{}\t'.format(self.msg_type, self.control_id, self.position)
        _state_str += '\t'.join(map(str, self.selection_list))
        _state_str += '\n'
        return _state_str

    def add_selection(self, text):
        self.selection_list.append(text)

    def set_selected(self, selected_text):
        if selected_text in self.selection_list:
            self._position = self.selection_list.index(selected_text)
            slctr_str = '\t{}\t{}\t{}\t'.format(self.msg_type, self.control_id, self._position)
            slctr_str += '\t'.join(map(str, self.selection_list))
            slctr_str += '\n'
            self.state_str = slctr_str

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, val):
        try:
            _ = self.selection_list[val]
            self._position = val
            self.state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._position)
        except IndexError:
            pass

    @property
    def text_align(self) -> TextAlignment:
        return self._text_align

    @text_align.setter
    def text_align(self, val: TextAlignment):
        self._text_align = val
        self._cfg['textAlign'] = val.value

    @property
    def background_colour(self) -> Colour:
        return self._background_colour

    @background_colour.setter
    def background_colour(self, val: Colour):
        self._background_colour = val
        self._cfg['backgroundColour'] = str(val.value)

    @property
    def text_colour(self) -> Colour:
        return self.text_colour

    @text_colour.setter
    def text_colour(self, val: Colour):
        self._text_colour = val
        self._cfg['textColour'] = str(val.value)

    @property
    def title_bar_colour(self) -> Colour:
        return self._title_bar_colour

    @title_bar_colour.setter
    def title_bar_colour(self, val: Colour):
        self._title_bar_colour = val
        self._cfg['titleBarColour'] = str(val.value)
