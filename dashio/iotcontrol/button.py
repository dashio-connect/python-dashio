from .enums import Colour, Icon
from .control import Control

class Button(Control):

    def toggle_btn(self):
        self.btn_state = not self.btn_state

    def __init__(self,
                 control_id,
                 control_title='A Button',
                 icon_name=Icon.NONE,
                 on_colour=Colour.BLACK,
                 off_colour=Colour.RED,
                 flash_colour=Colour.GREEN,
                 text='',
                 text_colour=Colour.WHITE):
        super().__init__('BTTN', control_id)
        self.title = control_title
        self._btn_state = False
        self._state_str = '\t{}\t{}\tOFF\n'.format(self.msg_type, self.control_id)

        self.icon_name = icon_name
        self.on_colour = on_colour
        self.off_colour = off_colour
        self.flash_colour = flash_colour
        self.text = text
        self.text_colour = text_colour

    @property
    def on_colour(self) -> Colour:
        return self._on_colour

    @on_colour.setter
    def on_colour(self, val: Colour):
        self._on_colour = val
        self._cfg['onColour'] = str(val.value)

    @property
    def off_colour(self) -> Colour:
        return self._off_colour

    @off_colour.setter
    def off_colour(self, val: Colour):
        self._off_colour = val
        self._cfg['offColour'] = str(val.value)

    @property
    def flash_colour(self) -> Colour:
        return self._flash_colour

    @flash_colour.setter
    def flash_colour(self, val: Colour):
        self._flash_colour = val
        self._cfg['flashColour'] = str(val.value)

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

    @property
    def text_colour(self) -> Colour:
        return self._text_colour

    @text_colour.setter
    def text_colour(self, val: Colour):
        self._text_colour = val
        self._cfg['textColour'] = str(val.value)

    @property
    def btn_state(self):
        return self.__btn_state

    @btn_state.setter
    def btn_state(self, val):
        self.__btn_state = val
        if self.btn_state:
            self.state_str = '\t{}\t{}\tON\n'.format(self.msg_type, self.control_id)
        else:
            self.state_str = '\t{}\t{}\tOFF\n'.format(self.msg_type, self.control_id)
