"""menu.py

Returns
-------
Class
    Menu
"""
from .button import Button
from .control import Control
from .enums import Icon, TitlePosition
from .selector import Selector
from .slider_single_bar import SliderSingleBar
from .textbox import TextBox


class Menu(Control):
    """A Menu Control
    """

    def __init__(self,
                 control_id: str,
                 title="A Menu",
                 text="A Menu with Text",
                 icon=Icon.MENU,
                 control_position=None,
                 title_position=TitlePosition.BOTTOM):
        """A Menu control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Menu"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        text : str, optional
            Menu text, by default "A Menu with Text"
        icon : Icon, optional
            Menu icon, by default Icon.MENU
        """
        super().__init__("MENU", control_id, title=title, control_position=control_position, title_position=title_position)
        self.icon_name = icon
        self.text = text

    def add_control(self, control):
        """Add a control to the menu

        Parameters
        ----------
        control : Control
            A control to add to the menu

        Raises
        ------
        TypeError
            Must be either TextBox, Button, SliderSingleBar, Selector controls
        """
        if isinstance(control, TextBox, Button, SliderSingleBar, Selector):
            control.parent_id = self.control_id
        else:
            raise TypeError("Only TextBox, Button, or SliderSingleBar are allowed")

    @property
    def icon_name(self) -> Icon:
        """The icon for the menu

        Returns
        -------
        Icon
            The Icon
        """
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value

    @property
    def text(self) -> str:
        """Text displayed in iotdashboard app

        Returns
        -------
        str
            The text
        """
        return self._cfg["text"]

    @text.setter
    def text(self, val: str):
        self._cfg["text"] = val
