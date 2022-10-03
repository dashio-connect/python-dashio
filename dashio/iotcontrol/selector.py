"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from ..constants import BAD_CHARS
from .control import Control, ControlPosition, _get_title_position
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

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Selector from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Selector
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

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
        self.selection_list.append(text.translate(BAD_CHARS))

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
