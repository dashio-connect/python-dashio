from .enums import Color, DirectionStyle, TitlePosition, Precision
from .control import Control


class Direction(Control):
    def __init__(
        self,
        control_id,
        title="A Control",
        style=DirectionStyle.DEG,
        title_position=TitlePosition.BOTTOM,
        pointer_color=Color.GREEN,
        units="",
        precision=Precision.OFF,
        calibration_angle=0,
        control_position=None
    ):
        super().__init__("DIR", control_id, title=title, title_position=title_position, control_position=control_position)
        self.pointer_color = pointer_color
        self.calibration_angle = calibration_angle
        self._direction_value = 0
        self._direction_text = ""
        self.style = style
        self.units = units
        self.precision = precision

    def get_state(self):
        if self._direction_text:
            s_str = self._state_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._state_str + f"{self._direction_value}\n"
        return s_str

    @property
    def direction_value(self) -> float:
        return self._direction_value

    @direction_value.setter
    def direction_value(self, val: float):
        self._direction_value = val
        if self._direction_text:
            s_str = self._state_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._state_str + f"{self._direction_value}\n"
        self.state_str = s_str

    @property
    def direction_text(self) -> str:
        return self._direction_text

    @direction_text.setter
    def direction_text(self, val: str):
        self._direction_text = val
        if self._direction_text:
            s_str = self._state_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._state_str + f"{self._direction_value}\n"
        self.state_str = s_str

    @property
    def pointer_color(self) -> Color:
        return self._pointer_color

    @pointer_color.setter
    def pointer_color(self, val: Color):
        self._pointer_color = val
        self._cfg["pointerColor"] = str(val.value)

    @property
    def calibration_angle(self) -> float:
        return self._cfg["calAngle"]

    @calibration_angle.setter
    def calibration_angle(self, val: float):
        self._cfg["calAngle"] = val

    @property
    def style(self) -> DirectionStyle:
        return self._style

    @style.setter
    def style(self, val: DirectionStyle):
        self._style = val
        self._cfg["style"] = val.value

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
