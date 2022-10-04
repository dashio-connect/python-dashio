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
from .control import Control, ControlPosition, _get_title_position
from .enums import (TitlePosition)

class AudioVisualDisplay(Control):
    """AudioVisualDisplay Control
    """
    def __init__(
        self,
        control_id: str,
        title="A Audio visual display",
        title_position=TitlePosition.BOTTOM,
        control_position=None
    ):
        """AudioVisualDisplay
        Set the URL for IoTDashboard to play the media pointed to by the URL

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : [type], optional
            Title of the control, by default None
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        """
        super().__init__("AVD", control_id, title=title, control_position=control_position, title_position=title_position)
        self.url = ""

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Button from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Button
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
        """get_state is called by iotdashboard

        Returns
        -------
        str
            The controls state
        """
        if self.url:
            return self._control_hdr_str + f"{self.url}\n"
        return ""
        
    @property
    def url(self) -> str:
        """URL

        Returns
        -------
        str
            The url of the media to play
        """
        return self._url

    @url.setter
    def url(self, val: str):
        self._url = val
        self.state_str = self._control_hdr_str + f"{val}\n"
