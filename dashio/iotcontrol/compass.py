from .enums import Colour
from .control import Control


class Compass(Control):
    def __init__(self,
                 control_id,
                 control_title='A Control',
                 pointer_colour=Colour.GREEN,
                 calibration_angle=0,
                 control_position=None):
        super().__init__('DIR', control_id, control_position=control_position)
        self.title = control_title
        self.pointer_colour = pointer_colour
        self.calibration_angle = calibration_angle

        self._direction_value = 0
        self._state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._direction_value)

    @property
    def direction_value(self):
        return self._direction_value

    @direction_value.setter
    def direction_value(self, val):
        self._direction_value = val
        self.state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, val)

    @property
    def pointer_colour(self) -> Colour:
        return self._pointer_colour

    @pointer_colour.setter
    def pointer_colour(self, val: Colour):
        self._pointer_colour = val
        self._cfg['pointerColour'] = str(val.value)

    @property
    def calibration_angle(self):
        return self._cfg['calAngle']

    @calibration_angle.setter
    def calibration_angle(self, val):
        self._cfg['calAngle'] = val
