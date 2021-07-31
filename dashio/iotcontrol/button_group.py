from .button import Button
from .control import Control
from .enums import Icon, TitlePosition


class ButtonGroup(Control):
    """ButtonGroup control that shows a popup of buttons.

    Attributes
    ----------
    control_id : str
        a unique identity string. The identity string must be a unique string for each ButtonGroup per device
    title: str
        A short title for the button group
    text : str
        The text that appears on the ButtonGroup

    Methods
    -------
    add_button(Button)
        Add a button to the ButtonGroup
    """
    def get_state(self):
        return ""

    def __init__(
        self,
        control_id,
        title="A Button Group",
        text="A Button group with Text",
        title_position=TitlePosition.BOTTOM,
        icon=Icon.MENU,
        grid_view=True,
        control_position=None,
    ):
        """ButtonGroup control that shows a popup of buttons.

        Parameters
        ----------
            control_id : str
                [description]
            title : str, optional:
                [description]. Defaults to "A Button Group".
            text (str, optional):
                [description]. Defaults to "A Button group with Text".
            title_position ([type], optional):
                [description]. Defaults to TitlePosition.BOTTOM.
            icon ([type], optional):
                [description]. Defaults to Icon.MENU.
            grid_view (bool, optional):
                [description]. Defaults to True.
            control_position ([type], optional):
                [description]. Defaults to None.
        """
        super().__init__("BTGP", control_id, title=title, control_position=control_position, title_position=title_position)
        self.icon_name = icon
        self.text = text.translate({ord(i): None for i in '\t\n'})
        self.grid_view = grid_view

    def add_button(self, control):
        if isinstance(control, Button):
            control.parent_id = self.control_id
        else:
            raise TypeError("Only buttons are allowed")

    @property
    def grid_view(self) -> bool:
        return self._cfg["gridView"]

    @grid_view.setter
    def grid_view(self, val: bool):
        self._cfg["gridView"] = val

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value

    @property
    def text(self) -> str:
        return self._cfg["text"]

    @text.setter
    def text(self, val: str):
        self._cfg["text"] = val
