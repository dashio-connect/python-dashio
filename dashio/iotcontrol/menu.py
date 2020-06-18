from .control import Control
from .enums import Icon, Colour
from .slider_single_bar import SliderSingleBar
from .button import Button
from .textbox import TextBox
from .selector import Selector


class Menu(Control):
    def get_state(self):
        menu_status = ''
        return menu_status

    def __get_menu_controls_state(self, msg):
        menu_status = ''
        for key in self.control_dict.keys():
            menu_status += self.control_dict[key].get_state()
        self.state_str = menu_status

    def __init__(self,
                 control_id,
                 title='A Menu',
                 text='A Menu with Text',
                 max_font_size=20,
                 icon=Icon.MENU,
                 background_colour=Colour.BLUE,
                 title_bar_colour=Colour.WHEAT,
                 text_colour=Colour.WHEAT):
        super().__init__('MENU', control_id)
        self.title = title
        self.control_list = []
        self.control_dict = {}
        self._cfg['list'] = self.control_list
        self.max_font_size = max_font_size
        self.get_state_str = '\t{}\t{}\t'.format(self.msg_type, self.control_id)
        self.icon_name = icon
        self.text = text
        self.background_colour = background_colour
        self.title_bar_colour = title_bar_colour
        self.text_colour = text_colour

        self.message_rx_event += self.__get_menu_controls_state

    def add_control(self, control):
        if isinstance(control, TextBox) or \
           isinstance(control, Button) or \
           isinstance(control, SliderSingleBar) or \
           isinstance(control, Selector):
            str_cfg = control.msg_type + ',' + control.control_id
            self.control_list.append(str_cfg)
            key = control.msg_type + '_' + control.control_id
            self.control_dict[key] = control
        else:
            raise TypeError("Only TextBox, Button, or SliderSingleBar are allowed")

    @property
    def max_font_size(self):
        return self._cfg['maxFontSize']

    @max_font_size.setter
    def max_font_size(self, val):
        self._cfg['maxFontSize'] = val

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
    def text_colour(self) -> Colour:
        return self._text_colour

    @text_colour.setter
    def text_colour(self, val: Colour):
        self._text_colour = val
        self._cfg['textColour'] = str(val.value)

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