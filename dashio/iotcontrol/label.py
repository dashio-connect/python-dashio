from .enums import Colour, LabelStyle
from .control import Control


class Label(Control):
    """A Config only control"""

    def __init__(
        self,
        control_id,
        control_title="A label",
        text="",
        colour=Colour.WHITE,
        style=LabelStyle.BASIC,
        control_position=None,
    ):
        super().__init__("LBL", control_id, control_position=control_position)
        self.title = control_title
        self.text = text
        self.colour = text_colour
        self.style = style
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
    def colour(self, val: Colour):
        self._cfg["colour"] = str(val.value)
