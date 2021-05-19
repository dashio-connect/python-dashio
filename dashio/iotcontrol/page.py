from .control import Control
from .enums import Color, Icon


class Page(Control):
    """A Config only control"""

    def __init__(
        self,
        control_id,
        title="A page",
        icon=Icon.SQUARE,
        page_color=Color.BLACK,
        control_title_box_color=Color.BLACK,
        control_title_box_transparency=0,
        control_color=Color.WHITE_SMOKE,
        control_border_color=Color.WHITE_SMOKE,
        control_border_on=False,
        control_background_color=Color.BLACK,
        control_title_font_size=16,
        control_max_font_size=20,
        control_background_transparency=0,
    ):
        super().__init__("PAGE", control_id,  title=title)
        self.icon_name = icon
        self.page_color = page_color
        self.control_title_box_color = control_title_box_color
        self.control_title_box_transparency = control_title_box_transparency
        self.control_color = control_color
        self.control_border_color = control_border_color
        self.control_border_on = control_border_on
        self.control_background_color = control_background_color
        self.control_title_font_size = control_title_font_size
        self.control_max_font_size = control_max_font_size
        self.control_background_transparency = control_background_transparency
        self._state_str = ""

    def add_control(self, control):
        control.parent_id = self.control_id

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg["iconName"] = val.value

    @property
    def page_color(self) -> Color:
        return self._page_color

    @page_color.setter
    def page_color(self, val: Color):
        self._page_color = val
        self._cfg["pageColor"] = str(val.value)

    @property
    def control_title_box_color(self) -> Color:
        return self._control_title_box_color

    @control_title_box_color.setter
    def control_title_box_color(self, val: Color):
        self._control_title_box_color = val
        self._cfg["ctrlTitleBoxColor"] = str(val.value)

    @property
    def control_title_box_transparency(self) -> int:
        return self._cfg["ctrlTitleBoxTransparency"]

    @control_title_box_transparency.setter
    def control_title_box_transparency(self, val: int):
        if 0 <= val <= 100:
            self._cfg["ctrlTitleBoxTransparency"] = val
        else:
            raise ValueError("Value must be in the range 0 to 100")

    @property
    def control_color(self) -> Color:
        return self._control_color

    @control_color.setter
    def control_color(self, val: Color):
        self._control_color = val
        self._cfg["ctrlColor"] = str(val.value)

    @property
    def control_border_color(self) -> Color:
        return self._control_border_color

    @control_border_color.setter
    def control_border_color(self, val: Color):
        self._control_border_color = val
        self._cfg["ctrlBorderColor"] = str(val.value)

    @property
    def control_border_on(self) -> bool:
        return self._cfg["ctrlBorderOn"]

    @control_border_on.setter
    def control_border_on(self, val: bool):
        self._cfg["ctrlBorderOn"] = val

    @property
    def control_background_color(self) -> Color:
        return self._control_background_color

    @control_background_color.setter
    def control_background_color(self, val: Color):
        self._control_background_color = val
        self._cfg["ctrlBkgndColor"] = str(val.value)

    @property
    def control_title_font_size(self) -> int:
        return self._cfg["ctrlTitleFontSize"]

    @control_title_font_size.setter
    def control_title_font_size(self, val: int):
        self._cfg["ctrlTitleFontSize"] = val

    @property
    def control_max_font_size(self) -> int:
        return self._cfg["ctrlMaxFontSize"]

    @control_max_font_size.setter
    def control_max_font_size(self, val: int):
        self._cfg["ctrlMaxFontSize"] = val

    @property
    def control_background_transparency(self) -> int:
        return self._cfg["ctrlBkgndTransparency"]

    @control_background_transparency.setter
    def control_background_transparency(self, val: int):
        if 0 <= val <= 100:
            self._cfg["ctrlBkgndTransparency"] = val
        else:
            raise ValueError("Value must be in the range 0 to 100")
