from .enums import Color, DialNumberPosition, DialStyle, Precision, TitlePosition
from .control import Control


class Dial(Control):
    def __init__(
        self,
        control_id,
        title="A Dial",
        title_position=TitlePosition.BOTTOM,
        min=0.0,
        max=100.0,
        red_value=75.0,
        dial_fill_color=Color.RED,
        pointer_color=Color.BLUE,
        number_position=DialNumberPosition.LEFT,
        show_min_max=False,
        style=DialStyle.STD,
        precision=Precision.OFF,
        units="",
        control_position=None,
    ):
        super().__init__("DIAL", control_id, control_position=control_position, title_position=title_position)
        self._dial_value = 0
        self.title = title
        self.min = min
        self.max = max
        self.red_value = red_value
        self.dial_fill_color = dial_fill_color
        self.pointer_color = pointer_color
        self.number_position = number_position
        self.show_min_max = show_min_max
        self.style = style
        self.precision = precision
        self.units = units
        self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._dial_value)

    @property
    def dial_value(self) -> float:
        return self._dial_value

    @dial_value.setter
    def dial_value(self, val: float):
        self._dial_value = val
        self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._dial_value)

    @property
    def min(self) -> float:
        return self._cfg["min"]

    @min.setter
    def min(self, val: float):
        self._cfg["min"] = val

    @property
    def max(self) -> float:
        return self._cfg["max"]

    @max.setter
    def max(self, val: float):
        self._cfg["max"] = val

    @property
    def red_value(self) -> float:
        return self._cfg["redValue"]

    @red_value.setter
    def red_value(self, val: float):
        self._cfg["redValue"] = val

    @property
    def show_min_max(self) -> bool:
        return self._cfg["showMinMax"]

    @show_min_max.setter
    def show_min_max(self, val: bool):
        self._cfg["showMinMax"] = val

    @property
    def dial_fill_color(self) -> Color:
        return self._dial_fill_color

    @dial_fill_color.setter
    def dial_fill_color(self, val: Color):
        self._dial_fill_color = val
        self._cfg["dialFillColor"] = str(val.value)

    @property
    def pointer_color(self) -> Color:
        return self._pointer_color

    @pointer_color.setter
    def pointer_color(self, val: Color):
        self._pointer_color = val
        self._cfg["pointerColor"] = str(val.value)

    @property
    def number_positions(self) -> DialNumberPosition:
        return self._number_position

    @number_positions.setter
    def number_positions(self, val: DialNumberPosition):
        self._number_position = val
        self._cfg["numberPosition"] = val.value

    @property
    def style(self) -> DialStyle:
        return self._style

    @style.setter
    def style(self, val: DialStyle):
        self._style = val
        self._cfg["style"] = val.value

    @property
    def precision(self) -> Precision:
        return self._cfg["precision"]

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg["precision"] = val.value

    @property
    def units(self) -> str:
        return self._cfg["units"]

    @units.setter
    def units(self, val: str):
        self._cfg["units"] = val
