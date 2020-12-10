from .enums import Color, Icon, TitlePosition
from .control import Control


class Page(Control):
    """A Config only control"""

    def __init__(
        self,
        control_id,
        control_title="A page",
        icon_name=Icon.SQUARE,
        page_Color=Color.BLACK,
        control_title_box_Color=Color.BLACK,
        control_title_box_transparency=0,
        control_text_icon_Color=Color.WHITE_SMOKE,
        control_border_on=False,
        control_background_Color=Color.BLACK,
        control_title_font_size=16,
        control_max_font_size=20,
        control_background_transparency=0,
    ):
        super().__init__("PAGE", control_id)
        self.title = control_title
        self.icon_name = icon_name
        self.page_Color = page_Color
        self.control_title_box_Color = control_title_box_Color
        self.control_title_box_transparency = control_title_box_transparency
        self.control_text_icon_Color = control_text_icon_Color
        self.control_border_on = control_border_on
        self.control_background_Color = control_background_Color
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
    def page_Color(self) -> Color:
        return self._page_Color

    @page_Color.setter
    def page_Color(self, val: Color):
        self._dial_Color = val
        self._cfg["pageColor"] = str(val.value)

    @property
    def control_title_box_Color(self) -> Color:
        return self._control_title_box_Color

    @control_title_box_Color.setter
    def control_title_box_Color(self, val: Color):
        self._control_title_box_Color = val
        self._cfg["ctrlTitleBoxColor"] = str(val.value)

    @property
    def control_title_box_transparency(self) -> int:
        return self._cfg["ctrlTitleBoxTransparency"]

    @control_title_box_transparency.setter
    def control_title_box_transparency(self, val: int):
        self._cfg["ctrlTitleBoxTransparency"] = val

    @property
    def control_text_icon_Color(self) -> Color:
        return self._control_text_icon_Color

    @control_text_icon_Color.setter
    def control_text_icon_Color(self, val: Color):
        self._control_text_icon_Color = val
        self._cfg["ctrlTextIconColor"] = str(val.value)

    @property
    def control_border_on(self) -> bool:
        return self._cfg["ctrlBorderOn"]

    @control_border_on.setter
    def control_border_on(self, val: bool):
        self._cfg["ctrlBorderOn"] = val

    @property
    def control_background_Color(self) -> Color:
        return self._control_background_Color

    @control_background_Color.setter
    def control_background_Color(self, val: Color):
        self._control_background_Color = val
        self._cfg["ctrlBkgndColor"] = str(val.value)

    @property
    def control_title_font_size(self) -> int:
        return self._control_title_font_size

    @control_title_font_size.setter
    def control_title_font_size(self, val: int):
        self._cfg["ctrlTitleFontSize"] = val

    @property
    def control_max_font_size(self) -> int:
        return self._control_max_font_size

    @control_max_font_size.setter
    def control_max_font_size(self, val: int):
        self._cfg["ctrlMaxFontSize"] = val

    @property
    def control_background_transparency(self) -> int:
        return self._cfg["ctrlBkgndTransparency"]

    @control_background_transparency.setter
    def control_background_transparency(self, val: int):
        self._cfg["ctrlBkgndTransparency"] = val
