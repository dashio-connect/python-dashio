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
import datetime

import dateutil.parser

from ..constants import BAD_CHARS
from .control import Control, ControlPosition, _get_title_position
from .enums import Color, TimeGraphLineType, TitlePosition
from .ring_buffer import RingBuffer


class DataPoint:
    """
    A time stamped data point for a Time Graph
    """
    def __init__(self, data):
        """
        A time stamped data point for a time series graph.

        Parameters
        ----------
            data: A data point can be an int, float, or boolean, or string representing a number.
        """
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        if isinstance(data, str):
            data = data.translate(BAD_CHARS)
        self.data_point = data

    def __str__(self):
        return "{ts},{data}".format(ts=self.timestamp.isoformat(), data=self.data_point)


class TimeGraphLine:
    """A TimeGraphLine for a TimeGraph control
    """
    def __init__(
        self, name="", line_type=TimeGraphLineType.LINE, color=Color.BLACK, max_data_points=60, break_data=False
    ):
        """A TimeGraphLine for a TimeGraph control

        Parameters
        ----------
        name : str, optional
            The name of the line, by default ""
        line_type : TimeGraphLineType, optional
            Which line type to use, by default TimeGraphLineType.LINE
        color : Color, optional
            The color of the line, by default Color.BLACK
        max_data_points : int, optional
            The data is stored in a ring buffer this sets the ring buffer size, by default 60
        break_data : bool, optional
            If true draws the line with breaks between missing data, by default False
        """
        self.name = name.translate(BAD_CHARS)
        self.line_type = line_type
        self.color = color
        self.break_data = break_data
        self.data = RingBuffer(max_data_points)

    def get_line_from_timestamp(self, timestamp: str) -> str:
        """Converts data from timestamp to a string formatted for the iotdashboard app

        Returns
        -------
        str
            Formatted line data
        """
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}"
        try:
            d_stamp = dateutil.parser.isoparse(timestamp)
        except ValueError:
            return ""
        first = True
        valid_data = False
        data_list = self.data.get()
        for data_p in data_list:
            if data_p.timestamp > d_stamp:
                if first and self.break_data:
                    data_str += "\t" + "{ts},{ldata}".format(ts=data_p.timestamp.isoformat(), ldata="b")
                data_str += "\t" + str(data_p)
                valid_data = True
            first = False
        data_str += "\n"
        if not valid_data:
            data_str = ""
        return data_str

    def add_data_point(self, data_point):
        """Add and sends a single datapoint to the line. It automatically timestamps to the current time.

        Parameters
        ----------
            data_point : DataPoint
                A single data point
        """
        data_p = DataPoint(data_point)
        self.data.append(data_p)

    def get_latest_data(self) -> str:
        """Get the last inserted datapoint

        Returns
        -------
        str
            The last datapoint
        """
        if self.data.empty():
            return ""
        data_str = "\t" + str(self.data.get_latest()) + "\n"
        return data_str


class TimeGraph(Control):
    """A TimeGraph control
    """
    def __init__(
        self,
        control_id: str,
        title="A TimeGraph",
        title_position=TitlePosition.BOTTOM,
        y_axis_label="Y axis",
        y_axis_min=0.0,
        y_axis_max=100.0,
        y_axis_num_bars=5,
        control_position=None,
    ):
        """A Timegraph control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A TimeGraph"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        y_axis_label : str, optional
            Label for the Y axis, by default "Y axis"
        y_axis_min : float, optional
            Min value for the Y axis, by default 0.0
        y_axis_max : float, optional
            Max value for the Y axis, by default 100.0
        y_axis_num_bars : int, optional
            The number of bars to display on the graph, by default 5
        """
        super().__init__("TGRPH", control_id, title=title, control_position=control_position, title_position=title_position)

        self.message_rx_event = self._get_lines_from_timestamp
        self.y_axis_label = y_axis_label
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max
        self.y_axis_num_bars = y_axis_num_bars

        self.line_dict = {}

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates TimeGraph from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        TimeGraph
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["yAxisLabel"],
            cfg_dict["yAxisMin"],
            cfg_dict["yAxisMax"],
            cfg_dict["yAxisNumBars"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def add_line(self, line_id: str, gline: TimeGraphLine):
        """Add a line to the TimeGraph

        Parameters
        ----------
        line_id : str
            A unique to the graph line id
        gline : TimeGraphLine
            The Line to add
        """
        self.line_dict[line_id] = gline

    def _get_lines_from_timestamp(self, msg):
        state_str = ""
        try:
            dashboard_id = msg[3]
            from_timestamp = msg[4]
        except IndexError:
            return ""
        for key in self.line_dict:
            if self.line_dict[key].data:
                line_data = self.line_dict[key].get_line_from_timestamp(from_timestamp)
                if line_data:
                    state_str += self._control_hdr_str + dashboard_id + "\t" + key + line_data
        return state_str

    def send_data(self):
        """Sends the latest Data to the iotdashboard app.
        """
        state_str = ""
        for key in self.line_dict:
            if self.line_dict[key].data:
                line_data = self.line_dict[key].get_latest_data()
                if line_data:
                    state_str += self._control_hdr_str + key + line_data
        self.state_str = state_str

    @property
    def y_axis_label(self) -> str:
        """Label for the Y axis

        Returns
        -------
        str
            The label
        """
        return self._cfg["yAxisLabel"]

    @y_axis_label.setter
    def y_axis_label(self, val: str):
        self._cfg["yAxisLabel"] = val

    @property
    def y_axis_min(self) -> float:
        """Min value for the Y axis

        Returns
        -------
        float
            The min value
        """
        return self._cfg["yAxisMin"]

    @y_axis_min.setter
    def y_axis_min(self, val: float):
        self._cfg["yAxisMin"] = val

    @property
    def y_axis_max(self) -> float:
        """Max value for the Y axis

        Returns
        -------
        float
            The max value
        """
        return self._cfg["yAxisMax"]

    @y_axis_max.setter
    def y_axis_max(self, val: float):
        self._cfg["yAxisMax"] = val

    @property
    def y_axis_num_bars(self) -> int:
        """The number of bars to display on the graph

        Returns
        -------
        int
            The number of bars
        """
        return self._cfg["yAxisNumBars"]

    @y_axis_num_bars.setter
    def y_axis_num_bars(self, val: int):
        self._cfg["yAxisNumBars"] = val
