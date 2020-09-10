from .enums import Colour, Icon, ButtonState
from .control import Control, ControlPosition


class Button(Control):
    def toggle_btn(self):
        self.btn_state = not self.btn_state

    def __init__(
        self,
        control_id,
        control_title="A Button",
        max_font_size=20,
        button_enabled=True,
        icon_name=Icon.NONE,
        on_colour=Colour.BLACK,
        off_colour=Colour.RED,
        flash_colour=Colour.GREEN,
        text="",
        text_colour=Colour.WHITE,
        control_position=None,
    ):
        super().__init__("BTTN", control_id, control_position=control_position)
        self.title = control_title
        self.max_font_size = max_font_size
        self._btn_state = ButtonState.OFF
        self._state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._btn_state.value)
        self.button_enabled = button_enabled
        self.icon_name = icon_name
        self.on_colour = on_colour
        self.off_colour = off_colour
        self.flash_colour = flash_colour
        self.text = text
        self.text_colour = text_colour

    @property
    def max_font_size(self):
        return self._cfg["maxFontSize"]

    @max_font_size.setter
    def max_font_size(self, val):
        self._cfg["maxFontSize"] = val

    @property
    def button_enabled(self) -> bool:
        return self._cfg["buttonEnabled"]

    @button_enabled.setter
    def button_enabled(self, val: bool):
        self._cfg["buttonEnabled"] = val

    @property
    def on_colour(self) -> Colour:
        return self._on_colour

    @on_colour.setter
    def on_colour(self, val: Colour):
        self._on_colour = val
        self._cfg["onColour"] = str(val.value)

    @property
    def off_colour(self) -> Colour:
        return self._off_colour

    @off_colour.setter
    def off_colour(self, val: Colour):
        self._off_colour = val
        self._cfg["offColour"] = str(val.value)

    @property
    def flash_colour(self) -> Colour:
        return self._flash_colour

    @flash_colour.setter
    def flash_colour(self, val: Colour):
        self._flash_colour = val
        self._cfg["flashColour"] = str(val.value)

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value
        self.state_str = "\t{}\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._btn_state.value, val.value)

    @property
    def text(self):
        return self._cfg["text"]

    @text.setter
    def text(self, val):
        self._cfg["text"] = val
        self.state_str = "\t{}\t{}\t{}\t{}\t{}\n".format(
            self.msg_type, self.control_id, self._btn_state.value, self._icon_name, val
        )

    @property
    def text_colour(self) -> Colour:
        return self._text_colour

    @text_colour.setter
    def text_colour(self, val: Colour):
        self._text_colour = val
        self._cfg["textColour"] = str(val.value)

    @property
    def btn_state(self) -> ButtonState:
        return self._btn_state

    @btn_state.setter
    def btn_state(self, val: ButtonState):
        self._btn_state = val
        self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, val.value)
