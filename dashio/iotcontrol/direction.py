
"""Direction control

Returns
-------
Class
    Direction
"""

from .control import Control
from .enums import Color, DirectionStyle, Precision, TitlePosition


class Direction(Control):
    """Direction control
    """
    def __init__(
        self,
        control_id: str,
        title="A Control",
        style=DirectionStyle.DEG,
        title_position=TitlePosition.BOTTOM,
        pointer_color=Color.GREEN,
        units="",
        precision=Precision.OFF,
        calibration_angle=0,
        control_position=None
    ):
        """Direction Control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Control"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        style : DirectionStyle, optional
            The Direction style to display, by default DirectionStyle.DEG
        pointer_color : Color, optional
            Color of the pointer, by default Color.GREEN
        units : str, optional
            Units to be displayed with the value, by default ""
        precision : [type], optional
            Precision of the value displayed, by default Precision.OFF
        calibration_angle : int, optional
            Calibration angle offset, by default 0
        """
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
            s_str = self._control_hdr_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._control_hdr_str + f"{self._direction_value}\n"
        return s_str

    @property
    def direction_value(self) -> float:
        """Direction value

        Returns
        -------
        float
            The direction
        """
        return self._direction_value

    @direction_value.setter
    def direction_value(self, val: float):
        self._direction_value = val
        if self._direction_text:
            s_str = self._control_hdr_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._control_hdr_str + f"{self._direction_value}\n"
        self.state_str = s_str

    @property
    def direction_text(self) -> str:
        """Direction text

        Returns
        -------
        str
            Text to be displayed on the direction control
        """
        return self._direction_text

    @direction_text.setter
    def direction_text(self, val: str):
        self._direction_text = val
        if self._direction_text:
            s_str = self._control_hdr_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._control_hdr_str + f"{self._direction_value}\n"
        self.state_str = s_str

    @property
    def pointer_color(self) -> Color:
        """Color of the pointer

        Returns
        -------
        Color
            Pointer color
        """
        return self._pointer_color

    @pointer_color.setter
    def pointer_color(self, val: Color):
        self._pointer_color = val
        self._cfg["pointerColor"] = str(val.value)

    @property
    def calibration_angle(self) -> float:
        """Calibration

        Returns
        -------
        float
            Calibration offset
        """
        return self._cfg["calAngle"]

    @calibration_angle.setter
    def calibration_angle(self, val: float):
        self._cfg["calAngle"] = val

    @property
    def style(self) -> DirectionStyle:
        """Direction style

        Returns
        -------
        DirectionStyle
            Style of the direction control
        """
        return self._style

    @style.setter
    def style(self, val: DirectionStyle):
        self._style = val
        self._cfg["style"] = val.value

    @property
    def units(self) -> str:
        """Units displayed on the control

        Returns
        -------
        str
            Units string displayed with the value
        """
        return self._cfg["units"]

    @units.setter
    def units(self, val: str):
        self._cfg["units"] = val

    @property
    def precision(self) -> Precision:
        """Precision

        Returns
        -------
        Precision
            The precision of the value displayed on the control
        """
        return self._precision

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg["precision"] = val.value
