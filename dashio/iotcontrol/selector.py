"""menu.py

Class
-----
Selector
    A Selector control
"""
from .control import Control
from .enums import TitlePosition


class Selector(Control):
    """A Selector control
    """
    def __init__(self, control_id: str, title="A Selector", title_position=TitlePosition.BOTTOM, control_position=None):
        """A Selector control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Selector"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        """
        super().__init__("SLCTR", control_id, title=title, control_position=control_position, title_position=title_position)
        self.selection_list = []
        self._position = 0
        self._cfg["selection"] = self.selection_list

    def get_state(self):
        _state_str = self._control_hdr_str + f"{self.position}\t"
        _state_str += "\t".join(map(str, self.selection_list))
        _state_str += "\n"
        return _state_str

    def add_selection(self, text):
        """Add a selector entry

        Parameters
        ----------
        text : str
            The text for the selection
        """
        self.selection_list.append(text)

    def set_selected(self, selected_text: str):
        """Set the selector to the selected text

        Parameters
        ----------
        selected_text : str
            The selection to display
        """
        if selected_text in self.selection_list:
            self._position = self.selection_list.index(selected_text)
            slctr_str = self._control_hdr_str + f"{self._position}\t"
            slctr_str += "\t".join(map(str, self.selection_list))
            slctr_str += "\n"
            self.state_str = slctr_str

    @property
    def position(self) -> int:
        """Position index of the selected Text

        Returns
        -------
        int
            Position index
        """
        return self._position

    @position.setter
    def position(self, val: int):
        try:
            _ = self.selection_list[val]
            self._position = val
            self.state_str = self._control_hdr_str + f"{self._position}\n"
        except IndexError:
            pass
