from .enums import Color, TitlePosition
from .control import Control


class Compass(Control):
    def __init__(
        self,
        control_id,
        title="A Control",
        title_position=TitlePosition.BOTTOM,
        pointer_color=Color.GREEN,
        calibration_angle=0,
        control_position=None
    ):
        super().__init__("DIR", control_id, title=title, title_position=title_position, control_position=control_position)
        self.pointer_color = pointer_color
        self.calibration_angle = calibration_angle
        self._direction_value = 0

    def get_state(self):
        return self._state_str + "{}\n".format(self._direction_value)

    @property
    def direction_value(self) -> float:
        return self._direction_value

    @direction_value.setter
    def direction_value(self, val: float):
        self._direction_value = val
        self.state_str = self._state_str + "\t{}\n".format(val)

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
