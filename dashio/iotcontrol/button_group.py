from .control import Control
from .enums import Icon, Colour
from .button import Button


class ButtonGroup(Control):
    def get_state(self):
        return ''

    def __get_button_group_state(self, msg):
        button_group_status = ''
        for key in self.control_dict.keys():
            button_group_status += self.control_dict[key].get_state()
        self.state_str = button_group_status

    def __init__(self,
                 control_id,
                 title='A Button Group',
                 text='A Button group with Text',
                 icon=Icon.MENU,
                 background_colour=Colour.BLACK,
                 title_bar_colour=Colour.BLACK,
                 grid_view=True,
                 control_position=None):
        super().__init__('BTGP', control_id, control_position=control_position)
        self.title = title
        self.control_list = []
        self.control_dict = {}
        self._state_str = '\t{}\t{}\t'.format(self.msg_type, self.control_id)
        self.icon_name = icon
        self.text = text
        self.background_colour = background_colour
        self.title_bar_colour = title_bar_colour
        self.grid_view = gtid_view

    def add_button(self, control):
        if isinstance(control, Button):
            control.parent_id = self.control_id
        else:
            raise TypeError("Only buttons are allowed")

    @property
    def background_colour(self) -> Colour:
        return self._background_colour

    @background_colour.setter
    def background_colour(self, val: Colour):
        self._background_colour = val
        self._cfg['backgroundColour'] = str(val.value)

    @property
    def title_bar_colour(self) -> Colour:
        return self._title_bar_colour

    @title_bar_colour.setter
    def title_bar_colour(self, val: Colour):
        self._title_bar_colour = val
        self._cfg['titleBarColour'] = str(val.value)

    @property
    def grid_view(self) -> bool:
        return self._cfg['gridView']

    @grid_view.setter
    def grid_view(self, val: bool):
        self._cfg['gridView'] = val

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg['iconName'] = val.value

    @property
    def text(self):
        return self._cfg['text']

    @text.setter
    def text(self, val):
        self._cfg['text'] = val
