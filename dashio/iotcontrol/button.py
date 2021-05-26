from .control import Control
from .enums import ButtonState, Color, Icon, TitlePosition


class Button(Control):
    def toggle_btn(self):
        if self.btn_state == ButtonState.FLASH:
            return
        if self.btn_state == ButtonState.OFF:
            self.btn_state = ButtonState.ON
        else:
            self.btn_state = ButtonState.OFF

    def __init__(
        self,
        control_id,
        title="A Button",
        title_position=TitlePosition.BOTTOM,
        button_enabled=True,
        icon_name=Icon.NONE,
        on_color=Color.BLUE,
        off_color=Color.RED,
        text="",
        control_position=None,
    ):
        super().__init__("BTTN", control_id, title=title, control_position=control_position, title_position=title_position)
        self._btn_state = ButtonState.OFF
        self.button_enabled = button_enabled
        self._icon_name = icon_name
        self.on_color = on_color
        self.off_color = off_color
        self.text = text

    def get_state(self):
        text = self._cfg["text"]
        if (not text) and ( self.icon_name == Icon.NONE):
            return self._control_hdr_str + f"{self._btn_state.value}\n"
        if (not text) and self.icon_name != Icon.NONE:
            return self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\n"
        return self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\t{text}\n"

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
        self.state_str = self._control_hdr_str + f"{self._btn_state.value}\t{val.value}\n"

    @property
    def text(self) -> str:
        return self._cfg["text"]

    @text.setter
    def text(self, val: str):
        self._cfg["text"] = val
        self.state_str = self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\t{val}\n"

    @property
    def btn_state(self) -> ButtonState:
        return self._btn_state

    @btn_state.setter
    def btn_state(self, val: ButtonState):
        self._btn_state = val
        self.state_str = self._control_hdr_str + f"{val.value}\n"

    def send_button(self, btn_state: ButtonState, btn_icon: Icon, text: str):
        self._btn_state = btn_state
        self._icon_name = btn_icon
        self._cfg["iconName"] = btn_icon.value
        self._cfg["text"] = text
        self.state_str = self._control_hdr_str + f"{self._btn_state.value}\t{self._icon_name.value}\t{text}\n"
