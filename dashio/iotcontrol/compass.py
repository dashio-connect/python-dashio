from .enums import Color
from .control import Control


class Compass(Control):
    def __init__(
        self,
        control_id,
        control_title="A Control",
        pointer_color=Color.GREEN,
        calibration_angle=0,
        control_position=None,
    ):
        super().__init__("DIR", control_id, control_position=control_position)
        self.title = control_title
        self.pointer_color = pointer_color
        self.calibration_angle = calibration_angle

        self._direction_value = 0
        self._state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._direction_value)

    @property
    def direction_value(self):
        return self._direction_value

    @direction_value.setter
    def direction_value(self, val):
        self._direction_value = val
        self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, val)

    @property
    def pointer_color(self) -> Color:
        return self._pointer_color

    @pointer_color.setter
    def pointer_color(self, val: Color):
        self._pointer_color = val
        self._cfg["pointerColor"] = str(val.value)

    @property
    def calibration_angle(self):
        return self._cfg["calAngle"]

    @calibration_angle.setter
    def calibration_angle(self, val):
        self._cfg["calAngle"] = val
