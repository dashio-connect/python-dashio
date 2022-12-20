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
from .control import Control, ControlPosition, ControlConfig, _get_color, _get_title_position, _get_knob_style
from .enums import Color, KnobStyle, TitlePosition

class KnobConfig(ControlConfig):
    """KnobConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        knob_style: KnobStyle,
        dial_min: float,
        dial_max: float,
        red_value: float,
        show_min_max: bool,
        send_only_on_release: bool,
        dial_follows_knob: bool,
        dial_color: Color,
        knob_color: Color,
        control_position=None,
        ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["style"] = str(knob_style.value)
        self.cfg["min"] = dial_min
        self.cfg["max"] = dial_max
        self.cfg["redValue"] = red_value
        self.cfg["showMinMax"] = show_min_max
        self.cfg["sendOnlyOnRelease"] = send_only_on_release
        self.cfg["dialFollowsKnob"] = dial_follows_knob
        self.cfg["dialColor"] = str(dial_color.value)
        self.cfg["knobColor"] = str(knob_color.value)

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates KnobConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        KnobConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_knob_style(cfg_dict["style"]),
            cfg_dict["min"],
            cfg_dict["max"],
            cfg_dict["redValue"],
            cfg_dict["showMinMax"],
            cfg_dict["sendOnlyOnRelease"],
            cfg_dict["dialFollowsKnob"],
            _get_color(cfg_dict["dialColor"]),
            _get_color(cfg_dict["knobColor"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

class Knob(Control):
    """A Knob control
    """

    def add_config_columnar(self, config: KnobConfig):
        if isinstance(config, KnobConfig):
            config.cfg["min"] = self.dial_min
            config.cfg["max"] = self.dial_max
            config.cfg["redValue"] = self.red_value
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

    def add_config_full_page(self, config: KnobConfig):
        if isinstance(config, KnobConfig):
            config.cfg["min"] = self.dial_min
            config.cfg["max"] = self.dial_max
            config.cfg["redValue"] = self.red_value
            config.cfg["ControlID"] = self.control_id
            self._cfg_columnar.append(config)

    def __init__(
        self,
        control_id,
        title="A Knob",
        title_position=TitlePosition.BOTTOM,
        knob_style=KnobStyle.NORMAL,
        dial_min=0.0,
        dial_max=100.0,
        red_value=75.0,
        show_min_max=False,
        send_only_on_release=True,
        dial_follows_knob=False,
        dial_color=Color.BLUE,
        knob_color=Color.RED,
        control_position=None
    ):
        """A Knob control is a control with a dial and knob.

        Parameters
        ----------
        control_id : str
            A unique identifier for this control
        title : str, optional
            The title for this control will be displayed on the iotdashboard app, by default "A Knob"
        title_position : TitlePosition, optional
            The position of the title, by default TitlePosition.BOTTOM
        knob_style : KnobStyle, optional
            The Knob style, by default KnobStyle.NORMAL
        dial_min : float, optional
            Minimum dial value, by default 0.0
        dial_max : float, optional
            Maximum dial value, by default 100.0
        red_value : float, optional
            The value where the red starts, by default 75.0
        show_min_max : bool, optional
            Whether to show the min amd max values, by default False
        send_only_on_release : bool, optional
            Have the DashIO app send values either on release or during movement, by default True
        dial_follows_knob : bool, optional
            Have the DashIO app adjust the dial to match the knob value, by default False
        dial_color : Color, optional
            Color of the Dial, by default Color.BLUE
        knob_color : Color, optional
            Color of the Knob, by default Color.RED
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        """
        super().__init__("KNOB", control_id)
        self._cfg_columnar.append(
            KnobConfig(
                control_id,
                title,
                title_position,
                knob_style,
                dial_min,
                dial_max,
                red_value,
                show_min_max,
                send_only_on_release,
                dial_follows_knob,
                dial_color,
                knob_color,
                control_position
            )
        )

        self._control_id_dial = f"\t{{device_id}}\tKBDL\t{control_id}\t"
        self._knob_value = 0
        self._knob_dial_value = 0
        self._state_str_knob = self._control_hdr_str + f"{self._knob_value}\n"
        self._state_str_dial = self._control_id_dial + f"{self._knob_dial_value}\n"
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

        self._dial_min = dial_min
        self._dial_max = dial_max
        self._red_value = red_value

    @property
    def dial_min(self):
        """Return the minimum dial value"""
        return self._dial_min

    @property
    def dial_max(self):
        """Return the maximum dial value"""
        return self._dial_max

    @property
    def red_value(self):
        """Return the red value for the dial"""
        return self._red_value

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Knob from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Knob
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            _get_knob_style(cfg_dict["style"]),
            cfg_dict["min"],
            cfg_dict["max"],
            cfg_dict["redValue"],
            cfg_dict["showMinMax"],
            cfg_dict["sendOnlyOnRelease"],
            cfg_dict["dialFollowsKnob"],
            _get_color(cfg_dict["dialColor"]),
            _get_color(cfg_dict["knobColor"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def get_state(self):
        return self._knob_dial_state_str

    @property
    def knob_value(self) -> float:
        """knob value

        Returns
        -------
        float
            The value of the knob
        """
        return self._knob_value

    @knob_value.setter
    def knob_value(self, val: float):
        self._knob_value = val
        self._state_str_knob = self._control_hdr_str + f"{val}\n"
        self._message_tx_event(self._state_str_knob)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_dial_value(self) -> float:
        """Knob dial value

        Returns
        -------
        float
            The knob dial value
        """
        return self._knob_dial_value

    @knob_dial_value.setter
    def knob_dial_value(self, val: float):
        self._knob_dial_value = val
        self._state_str_dial = self._control_id_dial + f"{val}\n"
        self._message_tx_event(self._state_str_dial)
        self._knob_dial_state_str = self._state_str_knob + self._state_str_dial
