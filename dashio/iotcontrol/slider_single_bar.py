from .enums import Colour, SliderBarType
from .control import Control


class SliderSingleBar(Control):

    def __init__(self,
                 control_id,
                 control_title='A Single Slider',
                 min=0.0,
                 max=1000.0,
                 red_value=750,
                 show_min_max=False,
                 slider_enabled=True,
                 send_only_on_release=True,
                 bar_follows_slider=False,
                 bar_colour=Colour.BLUE,
                 bar_style=SliderBarType.SEGMENTED):
        super().__init__('SLDR', control_id)

        self._control_id_bar = 'BAR'

        self._bar1_value = 0.0
        self._slider_value = 0.0

        self.min = min
        self.max = max
        self.red_value = red_value
        self.show_min_max = show_min_max
        self.slider_enabled = slider_enabled
        self.send_only_on_release = send_only_on_release
        self.bar_follows_slider = bar_follows_slider
        self.bar_colour = bar_colour
        self.bar_style = bar_style

        self._slider_state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._slider_value)
        self._bar1_state_str = '\t{}\t{}\t{}\n'.format(self._control_id_bar, self.control_id, self._bar1_value)
        self._state_str = self._slider_state_str + self._bar1_state_str

    @property
    def bar1_value(self):
        return self._bar1_value

    @bar1_value.setter
    def bar1_value(self, val):
        self._bar1_value = val
        self._bar1_state_str = '\t{}\t{}\t{}\n'.format(self._control_id_bar, self.control_id, self._bar1_value)
        self.message_tx_event(self._bar1_state_str)
        self._state_str = self._slider_state_str + self._bar1_state_str

    @property
    def slider_value(self):
        return self._slider_value

    @slider_value.setter
    def slider_value(self, val):
        self._slider_value = val
        self._slider_state_str = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._slider_value)
        self.message_tx_event(self._slider_state_str)
        self._state_str = self._slider_state_str + self._bar1_state_str

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
    def slider_enabled(self):
        return self._cfg['sliderEnabled']

    @slider_enabled.setter
    def slider_enabled(self, val):
        self._cfg['sliderEnabled'] = val

    @property
    def send_only_on_release(self):
        return self._cfg['sendOnlyOnRelease']

    @send_only_on_release.setter
    def send_only_on_release(self, val):
        self._cfg['sendOnlyOnRelease'] = val

    @property
    def bar_follows_slider(self):
        return self._cfg['barFollowsSlider']

    @bar_follows_slider.setter
    def bar_follows_slider(self, val):
        self._cfg['barFollowsSlider'] = val

    @property
    def bar_colour(self) -> Colour:
        return self._bar_colour

    @bar_colour.setter
    def bar_colour(self, val: Colour):
        self._bar_colour = val
        self._cfg['barColour'] = str(val.value)

    @property
    def bar_style(self) -> SliderBarType:
        return self._bar_style

    @bar_style.setter
    def bar_style(self, val: SliderBarType):
        self._bar_style = val
        self._cfg['barStyle'] = val.value