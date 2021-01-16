from .control import Control
from .enums import Icon, TitlePosition
from .button import Button


class ButtonGroup(Control):
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
        super().__init__("BTGP", control_id, control_position=control_position, title_position=title_position)
        self.title = title
        self.icon_name = icon
        self.text = text
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
