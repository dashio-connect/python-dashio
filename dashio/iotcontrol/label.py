from .enums import Colour, LabelStyle
from .control import Control


class Label(Control):
    """A Config only control"""

    def __init__(self, control_id, control_title="A label", text="", text_colour=Colour.WHITE, control_position=None):
        super().__init__("LBL", control_id, control_position=control_position)
        self.title = control_title
        self.text = text
        self.text_colour = text_colour
        self._state_str = ""

    @property
    def style(self) -> LabelStyle:
        return self._style

    @style.setter
    def style(self, val: LabelStyle):
        self._style = val
        self._cfg["style"] = val.value

    @property
    def colour(self) -> Colour:
        return self._colour

    @colour.setter
    def sent_text_colour(self, val: Colour):
        self._colour = val
        self._cfg["colour"] = str(val.value)
