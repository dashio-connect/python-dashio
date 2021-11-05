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
import copy
import json
import logging

from ..constants import BAD_CHARS
from .enums import TitlePosition
from .event import Event


class ControlPosition:
    """
    ControlPosition
        Used to describe a controls position.
        Inherit this class to overide the set_size() if you want
        to alter the device layout based on the iotdashboards number of columns.
    """
    def __init__(self, x_position_ratio: float, y_position_ratio: float, width_ratio: float, height_ratio: float):
        """The ControlPosition class describes the location and size of a control on a DeviceView. The
        x_postion and y_position ratio place the top left hand corner of the control. The width and height ratio
        describe the controls size. The ratio is a number betwwen 0 and 1 representing the width and height of the
        DeviceView.

        Parameters
        ----------
        x_position_ratio : float
            Left side position expressed as a ration between 0 and 1
        y_position_ratio : float
            Upper side position expressed as a ration between 0 and 1
        width_ratio : float
            Control width expressed as a ration between 0 and 1
        height_ratio : float
            Control height expressed as a ration between 0 and 1
        """
        self.x_position_ratio = x_position_ratio
        self.y_position_ratio = y_position_ratio
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio

    def set_size(self, num_columns: str):
        """Called by iotdashboard when a CFG is asked for

        Parameters
        ----------
        num_columns : str
            The number of columns available on the dashboard.
        """
        logging.debug("Number of Columns: %s", num_columns)


class Control:
    """Base class for controls.
    """

    def get_state(self) -> str:
        """This is called by iotdashboard app. Controls need to implement their own version."""
        return ""

    def get_cfg(self, num_columns):
        """Returns the CFG for the control called when the iotdashboard app asks for a CFG

        Parameters
        ----------
        num_columns : str
            The number of columns available on the dashboard

        Returns
        -------
        str
            The CFG for this control
        """
        if self.control_position:
            self.control_position.set_size(num_columns)
        cfg_str = "\tCFG\t" + self.cntrl_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, cntrl_type: str, control_id: str, title=None, control_position=None, title_position=None):
        """Control base type - all controls have these charactoristics and methods.

        Parameters
        ----------
        cntrl_type : str
            The type of control to implement
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : [type], optional
            Title of the control, by default None
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        """
        # Dictionary to store CFG json
        self._cfg = {}
        self._title = None
        # Remove incompatible characters
        if title is not None:
            self.title = title.translate(BAD_CHARS)
        self._title_position = None
        if title_position is not None:
            self.title_position = title_position
        self.cntrl_type = cntrl_type.translate(BAD_CHARS)
        self.control_id = control_id.translate(BAD_CHARS)
        self.message_rx_event = Event()
        self.message_tx_event = Event()
        self._control_hdr_str = f"\t{{device_id}}\t{self.cntrl_type}\t{self.control_id}\t"
        self._tx_message = ""
        self._control_position = None
        if control_position is not None:
            self.control_position = control_position

    @property
    def state_str(self) -> str:
        """The current state of the control

        Returns
        -------
        str
            The current state of the control
        """
        return self._control_hdr_str

    @state_str.setter
    def state_str(self, val):
        self._tx_message = val
        self.message_tx_event(val)

    # Use getter, setter properties to store the settings in the config dictionary
    @property
    def parent_id(self) -> str:
        """The parent control or deviceview this control belongs to

        Returns
        -------
        str
            The parent_id
        """
        return self._cfg["parentID"]

    @parent_id.setter
    def parent_id(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["parentID"] = _val

    @property
    def control_id(self) -> str:
        """The control id of the control

        Returns
        -------
        str
            The control id should be a unique string for all controls on a device
        """
        return self._cfg["controlID"]

    @control_id.setter
    def control_id(self, val: str):
        self._cfg["controlID"] = val

    @property
    def title(self) -> str:
        """The title of the control

        Returns
        -------
        str
            The title of the control thats is displayed on the iotdashboard app
        """
        return self._cfg["title"]

    @title.setter
    def title(self, val: str):
        _val = val.translate(BAD_CHARS)
        self._cfg["title"] = _val

    @property
    def control_position(self) -> ControlPosition:
        """Control Position

        Returns:
            ControlPosition: The position of the control on the DeviceView
        """
        return self._control_position

    @control_position.setter
    def control_position(self, val: ControlPosition):
        self._control_position = copy.copy(val)
        self._cfg["xPositionRatio"] = val.x_position_ratio
        self._cfg["yPositionRatio"] = val.y_position_ratio
        self._cfg["widthRatio"] = val.width_ratio
        self._cfg["heightRatio"] = val.height_ratio

    @property
    def title_position(self) -> TitlePosition:
        """Title position

        Returns:
            TitlePosition: The position of the title
        """
        return self._title_position

    @title_position.setter
    def title_position(self, val: TitlePosition):
        self._title_position = val
        self._cfg["titlePosition"] = val.value
