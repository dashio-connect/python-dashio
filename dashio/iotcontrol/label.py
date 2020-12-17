from .enums import Color, LabelStyle
from .control import Control


class Label(Control):
    """A Config only control"""

    def __init__(
        self,
        control_id,
        control_title="A label",
        text="",
        color=Color.WHITE,
        style=LabelStyle.BASIC,
        control_position=None,
    ):
        super().__init__("LBL", control_id, control_position=control_position)
        self.title = control_title
        self.text = text
        self.color = color
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
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, val: Color):
        self._cfg["Color"] = str(val.value)

    @property
    def text(self):
        return self._cfg["text"]

    @text.setter
    def text(self, val):
        self._cfg["text"] = val
