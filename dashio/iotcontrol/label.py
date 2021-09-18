"""label.py

Returns
-------
Class
    Label
"""
from .control import Control
from .enums import Color, LabelStyle, TitlePosition


class Label(Control):
    """A Config only control"""

    def __init__(
        self,
        control_id: str,
        title="A label",
        title_position=TitlePosition.BOTTOM,
        color=Color.WHITE,
        style=LabelStyle.BASIC,
        control_position=None,
    ):
        """Label

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Label"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        color : Color, optional
            Color of the label, by default Color.WHITE
        style : LabelStyle, optional
            Style of label to be displayed, by default LabelStyle.BASIC
        """
        super().__init__("LBL", control_id, title=title, control_position=control_position, title_position=title_position)
        self.color = color
        self.style = style
        self._state_str = ""

    @property
    def style(self) -> LabelStyle:
        """Label style

        Returns
        -------
        LabelStyle
            Style of label to display
        """
        return self._style

    @style.setter
    def style(self, val: LabelStyle):
        self._style = val
        self._cfg["style"] = val.value

    @property
    def color(self) -> Color:
        """Color

        Returns
        -------
        Color
            Clor of the label
        """
        return self._color

    @color.setter
    def color(self, val: Color):
        self._color = val
        self._cfg["color"] = str(val.value)
