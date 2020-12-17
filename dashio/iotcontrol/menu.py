from .control import Control
from .enums import Icon
from .slider_single_bar import SliderSingleBar
from .button import Button
from .textbox import TextBox
from .selector import Selector


class Menu(Control):
    def get_state(self):
        return ""

    def __get_menu_controls_state(self, msg):
        menu_status = ""
        for key in self.control_dict.keys():
            menu_status += self.control_dict[key].get_state()
        self.state_str = menu_status

    def __init__(self, control_id, title="A Menu", text="A Menu with Text", icon=Icon.MENU, control_position=None):
        super().__init__("MENU", control_id, control_position=control_position)
        self.title = title
        self.control_list = []
        self.control_dict = {}
        self._state_str = "\t{}\t{}\t".format(self.msg_type, self.control_id)
        self.icon_name = icon
        self.text = text

    def add_control(self, control):
        if (
            isinstance(control, TextBox)
            or isinstance(control, Button)
            or isinstance(control, SliderSingleBar)
            or isinstance(control, Selector)
        ):
            control.parent_id = self.control_id
        else:
            raise TypeError("Only TextBox, Button, or SliderSingleBar are allowed")

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value

    @property
    def text(self):
        return self._cfg["text"]

    @text.setter
    def text(self, val):
        self._cfg["text"] = val
