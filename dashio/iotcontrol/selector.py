from .control import Control


class Selector(Control):
    def __init__(self, control_id, control_title="A Selector", max_font_size=20, control_position=None):
        super().__init__("SLCTR", control_id, control_position=control_position)
        self.title = control_title
        self.selection_list = []
        self._position = 0
        self._cfg["selection"] = self.selection_list

    def get_state(self):
        _state_str = "\t{}\t{}\t{}\t".format(self.msg_type, self.control_id, self.position)
        _state_str += "\t".join(map(str, self.selection_list))
        _state_str += "\n"
        return _state_str

    def add_selection(self, text):
        self.selection_list.append(text)

    def set_selected(self, selected_text):
        if selected_text in self.selection_list:
            self._position = self.selection_list.index(selected_text)
            slctr_str = "\t{}\t{}\t{}\t".format(self.msg_type, self.control_id, self._position)
            slctr_str += "\t".join(map(str, self.selection_list))
            slctr_str += "\n"
            self.state_str = slctr_str

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, val):
        try:
            _ = self.selection_list[val]
            self._position = val
            self.state_str = "\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self._position)
        except IndexError:
            pass
