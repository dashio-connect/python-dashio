from .enums import Colour, Icon, TitlePosition
from .control import Control


class Page(Control):
    """A Config only control"""

    def __init__(self,
                 control_id,
                 control_title='A page',
                 number_pages=1,
                 icon_name=Icon.SQUARE,
                 page_colour=Colour.BLACK,
                 control_title_box_colour=Colour.BLACK,
                 control_title_box_transparency=0,
                 control_title_position=TitlePosition.BOTTOM,
                 control_text_icon_colour=Colour.WHITE_SMOKE,
                 control_border_on=False,
                 control_background_colour=Colour.BLACK,
                 control_title_font_size=16,
                 control_max_font_size=20,
                 control_background_transparency=0):
        super().__init__('PAGE', control_id)
        self.title = control_title
        self.number_pages = number_pages
        self.page_colour = page_colour
        self.control_title_box_colour = control_title_box_colour
        self.control_title_box_transparency = control_title_box_transparency
        self.control_title_position = control_title_position
        self.control_text_icon_colour = control_text_icon_colour
        self.control_border_on = control_border_on
        self.control_background_colour = control_background_colour
        self.control_title_font_size = control_title_font_size
        self.control_max_font_size = control_max_font_size
        self.control_background_transparency = control_background_transparency
        self._state_str = ''

    def add_control(self, control):
        control.parent_id = self.control_id

    @property
    def number_pages(self) -> int:
        return self._cfg['numPages']

    @number_pages.setter
    def number_pages(self, val: int):
        self._cfg['numPages'] = val

    @property
    def icon_name(self) -> Icon:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, val: Icon):
        self._icon_name = val
        self._cfg['iconName'] = val.value

    @property
    def page_colour(self) -> Colour:
        return self._page_colour

    @page_colour.setter
    def page_colour(self, val: Colour):
        self._dial_colour = val
        self._cfg['pageColour'] = str(val.value)

    @property
    def control_title_box_colour(self) -> Colour:
        return self._control_title_box_colour

    @control_title_box_colour.setter
    def control_title_box_colour(self, val: Colour):
        self._control_title_box_colour = val
        self._cfg['ctrlTitleBoxColour'] = str(val.value)

    @property
    def control_title_box_transparency(self) -> int:
        return self._cfg['ctrlTitleBoxTransparency']

    @control_title_box_transparency.setter
    def control_title_box_transparency(self, val: int):
        self._cfg['ctrlTitleBoxTransparency'] = val

    @property
    def control_title_position(self) -> TitlePosition:
        return self._cfg['ctrlTitlePosition']

    @control_title_position.setter
    def control_title_position(self, val: TitlePosition):
        self._control_title_position = val
        self._cfg['ctrlTitlePosition'] = val.value

    @property
    def control_text_icon_colour(self) -> Colour:
        return self._control_text_icon_colour

    @control_text_icon_colour.setter
    def control_text_icon_colour(self, val: Colour):
        self._control_text_icon_colour = val
        self._cfg['ctrlTextIconColour'] = str(val.value)

    @property
    def control_border_on(self) -> bool:
        return self._cfg['ctrlBorderOn']

    @control_border_on.setter
    def control_border_on(self, val: bool):
        self._cfg['ctrlBorderOn'] = val

    @property
    def control_background_colour(self) -> Colour:
        return self._control_background_colour

    @control_background_colour.setter
    def control_background_colour(self, val: Colour):
        self._control_background_colour = val
        self._cfg['ctrlBkgndColour'] = str(val.value)

    @property
    def control_title_font_size(self) -> int:
        return self._control_title_font_size

    @control_title_font_size.setter
    def control_title_font_size(self, val: int):
        self._cfg['ctrlTitleFontSize'] = val

    @property
    def control_max_font_size(self) -> int:
        return self._control_max_font_size

    @control_max_font_size.setter
    def control_max_font_size(self, val: int):
        self._cfg['ctrlMaxFontSize'] = val

    @property
    def control_background_transparency(self) -> int:
        return self._cfg['ctrlBkgndTransparency']

    @control_background_transparency.setter
    def control_background_transparency(self, val: int):
        self._cfg['ctrlBkgndTransparency'] = val
