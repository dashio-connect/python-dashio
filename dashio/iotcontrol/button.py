from .enums import Color, Icon, ButtonState
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
        on_color=Color.BLACK,
        off_color=Color.RED,
        text="",
        control_position=None,
    ):
        super().__init__("BTTN", control_id, control_position=control_position)
        self.title = control_title
        self.max_font_size = max_font_size
        self._btn_state = ButtonState.OFF
        self._state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._btn_state.value)
        self.button_enabled = button_enabled
        self.icon_name = icon_name
        self.on_color = on_color
        self.off_color = off_color
        self.text = text

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
    def on_color(self) -> Color:
        return self._on_color

    @on_color.setter
    def on_color(self, val: Color):
        self._on_color = val
        self._cfg["onColor"] = str(val.value)

    @property
    def off_color(self) -> Color:
        return self._off_color

    @off_color.setter
    def off_color(self, val: Color):
        self._off_color = val
        self._cfg["offColor"] = str(val.value)

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value
        self._state_str = "\t{}\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._btn_state.value, val.value)

    @property
    def text(self):
        return self._cfg["text"]

    @text.setter
    def text(self, val):
        self._cfg["text"] = val
        self._state_str = "\t{}\t{}\t{}\t{}\t{}\n".format(
            self.msg_type, self.control_id, self._btn_state.value, self._icon_name.value, val
        )

    @property
    def btn_state(self) -> ButtonState:
        return self._btn_state

    @btn_state.setter
    def btn_state(self, val: ButtonState):
        self._btn_state = val
        self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, val.value)
