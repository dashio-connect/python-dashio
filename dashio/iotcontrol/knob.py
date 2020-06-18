from .enums import Colour
from .control import Control


class Knob(Control):

    def __init__(self,
                 control_id,
                 control_title='A Knob',
                 min=0.0,
                 max=100.0,
                 red_value=75.0,
                 show_min_max=False,
                 send_only_on_release=True,
                 dial_follows_knob=False,
                 dial_colour=Colour.BLUE):
        super().__init__('KNOB', control_id)
        self.title = control_title
        self._control_id_dial = 'KBDL'
        self._knob_value = 0
        self._knob_dial_value = 0

        self.min = min
        self.max = max
        self.red_value = red_value
        self.show_min_max = show_min_max
        self.send_only_on_release = send_only_on_release
        self.dial_follows_knob = dial_follows_knob
        self.dial_colour = dial_colour
        self._state_str_knob = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, self._knob_value)
        self._state_str_dial = '\t{}\t{}\t{}\n'.format(self._control_id_dial, self.control_id, self._knob_dial_value)
        self._state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_value(self):
        return self._knob_value

    @knob_value.setter
    def knob_value(self, val):
        self._knob_value = val
        self._state_str_knob = '\t{}\t{}\t{}\n'.format(self.msg_type, self.control_id, val)
        self.message_tx_event(self._state_str_knob)
        self._state_str = self._state_str_knob + self._state_str_dial

    @property
    def knob_dial_value(self):
        return self._knob_dial_value

    @knob_dial_value.setter
    def knob_dial_value(self, val):
        self._knob_dial_value = val
        self._state_str_dial = '\t{}\t{}\t{}\n'.format(self._control_id_dial, self.control_id, val)
        self.message_tx_event(self._state_str_dial)
        self._state_str = self._state_str_knob + self._state_str_dial

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
    def send_only_on_release(self):
        return self._cfg['sendOnlyOnRelease']

    @send_only_on_release.setter
    def send_only_on_release(self, val):
        self._cfg['sendOnlyOnRelease'] = val

    @property
    def dial_follows_knob(self):
        return self._cfg['dialFollowsKnob']

    @dial_follows_knob.setter
    def dial_follows_knob(self, val):
        self._cfg['dialFollowsKnob'] = val

    @property
    def dial_colour(self) -> Colour:
        return self._dial_colour

    @dial_colour.setter
    def dial_colour(self, val: Colour):
        self._dial_colour = val
        self._cfg['dialColour'] = str(val.value)