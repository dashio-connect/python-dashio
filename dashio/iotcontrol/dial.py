from .enums import Colour, DialPosition, DialStyle, Precision
from .control import Control


class Dial(Control):

    def __init__(self,
                 control_id,
                 control_title='A Dial',
                 min=0.0,
                 max=100.0,
                 red_value=75.0,
                 dial_fill_colour=Colour.RED,
                 pointer_colour=Colour.BLUE,
                 number_position=DialPosition.LEFT,
                 show_min_max=False,
                 style=DialStyle.STD,
                 precision=Precision.OFF,
                 units=''):
        super().__init__('DIAL', control_id)
        self._dial_value = 0
        self.title = control_title
        self.min = min
        self.max = max
        self.red_value = red_value
        self.dial_fill_colour = dial_fill_colour
        self.pointer_colour = pointer_colour
        self.number_position = number_position
        self.show_min_max = show_min_max
        self.style = style
        self.precision = precision
        self.units = units
        self.state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._dial_value)

    @property
    def dial_value(self):
        return self._dial_value

    @dial_value.setter
    def dial_value(self, val):
        self._dial_value = val
        self.state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._dial_value)

    @property
    def min(self):
        return self._cfg['min']

    @min.setter
    def min(self, val):
        self._cfg['min'] = val

    @property
    def max(self):
        return self._cfg['max']

    @max.setter
    def max(self, val):
        self._cfg['max'] = val

    @property
    def red_value(self):
        return self._cfg['redValue']

    @red_value.setter
    def red_value(self, val):
        self._cfg['redValue'] = val

    @property
    def show_min_max(self):
        return self._cfg['showMinMax']

    @show_min_max.setter
    def show_min_max(self, val):
        self._cfg['showMinMax'] = val

    @property
    def dial_fill_colour(self) -> Colour:
        return self._dial_fill_colour

    @dial_fill_colour.setter
    def dial_fill_colour(self, val):
        self._dial_fill_colour = val
        self._cfg['dialFillColour'] = str(val.value)

    @property
    def pointer_colour(self) -> Colour:
        return self._pointer_colour

    @pointer_colour.setter
    def pointer_colour(self, val: Colour):
        self._pointer_colour = val
        self._cfg['pointerColour'] = str(val.value)

    @property
    def number_positions(self) -> DialPosition:
        return self._number_position

    @number_positions.setter
    def number_positions(self, val: DialPosition):
        self._number_position = val
        self._cfg['numberPosition'] = val.value

    @property
    def style(self) -> DialStyle:
        return self._style

    @style.setter
    def style(self, val: DialStyle):
        self._style = val
        self._cfg['style'] = val.value

    @property
    def precision(self) -> Precision:
        return self._cfg['precision']

    @precision.setter
    def precision(self, val: Precision):
        self._precision = val
        self._cfg['precision'] = val.value

    @property
    def units(self):
        return self._cfg['units']

    @units.setter
    def units(self, val):
        self._cfg['units'] = val