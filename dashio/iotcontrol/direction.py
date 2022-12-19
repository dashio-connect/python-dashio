"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from ..constants import BAD_CHARS
from .control import Control, ControlPosition, ControlConfig, _get_color, _get_title_position, _get_direction_style, _get_precision
from .enums import Color, DirectionStyle, Precision, TitlePosition


class DirectionConfig(ControlConfig):
    """DirectionConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        style: DirectionStyle,
        title_position: TitlePosition,
        pointer_color: Color,
        units: str,
        precision: Precision,
        calibration_angle: float,
        control_position: ControlPosition
        ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["style"] = str(style.value)
        self.cfg["pointerColor"] = str(pointer_color.value)
        self.cfg["units"] = units
        self.cfg["precision"] = precision.value
        self.cfg["calAngle"] = calibration_angle

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates DirectionConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        DirectionConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_direction_style(cfg_dict["style"]),
            _get_title_position(cfg_dict["titlePosition"]),
            _get_color(cfg_dict["pointerColor"]),
            cfg_dict["units"],
            _get_precision(cfg_dict["precision"]),
            cfg_dict["calAngle"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls


class Direction(Control):
    """Direction control"""


    def add_config_columnar(self, config: DirectionConfig):
        if isinstance(config, DirectionConfig):
            config.cfg["calAngle"] = self.cal_angle
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

    def add_config_full_page(self, config: DirectionConfig):
        if isinstance(config, DirectionConfig):
            config.cfg["calAngle"] = self.cal_angle
            config.cfg["ControlID"] = self.control_id
            self._cfg_full_page.append(config)


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
        precision : Precision, optional
            Precision of the value displayed, by default Precision.OFF
        calibration_angle : int, optional
            Calibration angle offset, by default 0
        """
        super().__init__("DIR", control_id)
        self._cfg_columnar.append(
            DirectionConfig(
                control_id,
                title,
                style,
                title_position,
                pointer_color,
                units,
                precision,
                calibration_angle,
                control_position
            )
        )
        self._cal_angle = calibration_angle
        self._direction_value = 0
        self._direction_text = ""

    @property
    def cal_angle(self):
        """Retturns the calibration angle"""
        return self._cal_angle


    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Direction from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Direction
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_direction_style(cfg_dict["style"]),
            _get_title_position(cfg_dict["titlePosition"]),
            _get_color(cfg_dict["pointerColor"]),
            cfg_dict["units"],
            _get_precision(cfg_dict["precision"]),
            cfg_dict["calAngle"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls



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
        self._direction_text = val.translate(BAD_CHARS)
        if self._direction_text:
            s_str = self._control_hdr_str + f"{self._direction_value}\t{self._direction_text}\n"
        else:
            s_str = self._control_hdr_str + f"{self._direction_value}\n"
        self.state_str = s_str
