from .slider_single_bar import SliderSingleBar


class SliderDoubleBar(SliderSingleBar):
    def __init__(self, control_id, control_position=None):
        super().__init__(control_id, control_position=control_position)

        self._bar2_value = 0.0
        self._bar_state_str = "\t{}\t{}\t{:.2f}\t{:.2f}\n".format(
            self._control_id_bar, self.control_id, self._bar1_value, self._bar2_value
        )
        self._state_str = self._slider_state_str + self._bar_state_str

    @property
    def bar1_value(self):
        return self._bar1_value

    @bar1_value.setter
    def bar1_value(self, val):
        self._bar1_value = val
        self._bar_state_str = "\t{}\t{}\t{:.2f}\t{:.2f}\n".format(
            self._control_id_bar, self.control_id, val, self._bar2_value
        )
        self.message_tx_event(self._bar_state_str)
        self._state_str = self._slider_state_str + self._bar_state_str

    @property
    def bar2_value(self):
        return self._bar2_value

    @bar2_value.setter
    def bar2_value(self, val):
        self._bar2_value = val
        self._bar_state_str = "\t{}\t{}\t{:.2f}\t{:.2f}\n".format(
            self._control_id_bar, self.control_id, self._bar1_value, val
        )
        self.message_tx_event(self._bar_state_str)
        self._state_str = self._slider_state_str + self._bar_state_str

    @property
    def slider_value(self):
        return self._slider_value

    @slider_value.setter
    def slider_value(self, val):
        self._slider_value = val
        self._slider_state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._slider_value)
        self.message_tx_event(self._slider_state_str)
        self._state_str = self._slider_state_str + self._bar_state_str
