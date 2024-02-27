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
from .control import Control, ControlPosition, ControlConfig, _get_title_position
from .enums import Color, TimeGraphLineType, TitlePosition
from .ring_buffer import RingBuffer
from .event import Event


class DataPointArray:
    """
    A time stamped data array for a Time Graph
    """
    def __init__(self, data: list):
        """
        A time stamped data array for a time series graph.

        Parameters
        ----------
            data: A data array can contain an int, float, or string representing a number.
        """
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        for item in data:
            if isinstance(item, str):
                item = item.translate(BAD_CHARS)
        self.data_point = data

    def __str__(self):
        dp_str = ','.join([str(i) for i in self.data_point])
        return f"{self.timestamp.isoformat()},[{dp_str}]"


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
        return f"{self.timestamp.isoformat()},{self.data_point}"


class TimeGraphLine:
    """A TimeGraphLine for a TimeGraph control
    """
    def __init__(
        self,
        name: str = "",
        line_type: TimeGraphLineType = TimeGraphLineType.LINE,
        color: Color = Color.BLACK,
        max_data_points: int = 60,
        break_data: bool = False,
        right_axis: bool = False
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
        self.axis_side = 'left'
        if right_axis:
            self.axis_side = 'right'

    def get_line_format(self):
        return f"\t{self.name}\t{self.line_type.value}\t{self.color.value}\t{self.axis_side}\n"

    def get_line_from_timestamp(self, timestamp: str) -> str:
        """Converts data from timestamp to a string formatted for the iotdashboard app

        Returns
        -------
        str
            Formatted line data
        """
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}\t{self.axis_side}"

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
                    data_str += "\t" + f"{data_p.timestamp.isoformat()},b"
                data_str += "\t" + str(data_p)
                valid_data = True
            first = False
        data_str += "\n"
        if not valid_data:
            data_str = ""
        return data_str

    def add_data_point(self, data):
        """Add and sends a datapoint to the line. It automatically timestamps to the current time.

        Parameters
        ----------
            data_point : str, int, float, DataPoint, DataPointArray
                A data point to add to the line.
        """
        if isinstance(data, DataPoint) or isinstance(data, DataPointArray):
            self.data.append(data)
        elif isinstance(data, str) or isinstance(data, float) or isinstance(data, int) or isinstance(data, bool):
            data_p = DataPoint(data)
            self.data.append(data_p)
        else:
            raise TypeError("Not a valid data point")

    def add_break(self):
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        dp_break = DataPoint("B")
        self.data.append(dp_break)

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


class TimeGraphConfig(ControlConfig):
    """TimeGraphConfig"""
    def __init__(
        self,
        control_id: str,
        title: str,
        title_position: TitlePosition,
        y_axis_label: str,
        y_axis_min: float,
        y_axis_max: float,
        y_axis_num_bars: int,
        y_axis_label_rt: str,
        y_axis_min_rt: float,
        y_axis_max_rt: float,
        control_position: ControlPosition
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["yAxisLabel"] = y_axis_label.translate(BAD_CHARS)
        self.cfg["yAxisMin"] = y_axis_min
        self.cfg["yAxisMax"] = y_axis_max
        self.cfg["yAxisNumBars"] = y_axis_num_bars
        self.cfg["yAxisLabelRt"] = y_axis_label_rt.translate(BAD_CHARS)
        self.cfg["yAxisMinRt"] = y_axis_min_rt
        self.cfg["yAxisMaxRt"] = y_axis_max_rt

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates TimeGraphConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        SliderConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["yAxisLabel"],
            cfg_dict["yAxisMin"],
            cfg_dict["yAxisMax"],
            cfg_dict["yAxisNumBars"],
            cfg_dict["yAxisLabelRt"],
            cfg_dict["yAxisMinRt"],
            cfg_dict["yAxisMaxRt"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls


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
        y_axis_max=1000.0,
        y_axis_num_bars=5,
        y_axis_label_rt='',
        y_axis_min_rt=0.0,
        y_axis_max_rt=1000.0,
        control_position=None,
        column_no=1
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
        column_no : int, optional default is 1. Must be 1..3
            The Dash App reports its screen size in columns. column_no allows you to specify which column no to load into.
            Each control can store three configs that define how the device looks for Dash apps installed on single column
            phones or 2 column fold out phones or 3 column tablets.
        """
        super().__init__("TGRPH", control_id)
        self._app_columns_cfg[str(column_no)].append(
            TimeGraphConfig(
                control_id,
                title,
                title_position,
                y_axis_label,
                y_axis_min,
                y_axis_max,
                y_axis_num_bars,
                y_axis_label_rt,
                y_axis_min_rt,
                y_axis_max_rt,
                control_position
            )
        )
        self._message_rx_event = Event()
        self._message_rx_event += self._get_lines_from_timestamp
        self._y_axis_min = y_axis_min
        self._y_axis_max = y_axis_max
        self._y_axis_num_bars = y_axis_num_bars
        self._y_axis_min_rt = y_axis_min_rt
        self._y_axis_max_rt = y_axis_max_rt

        self.line_dict = {}

    @property
    def y_axis_min(self):
        """Returns the Y axis minimum value"""
        return self._y_axis_min

    @property
    def y_axis_max(self):
        """Returns the Y axis maximum value"""
        return self._y_axis_max

    @property
    def y_axis_min_rt(self):
        """Returns the Y axis minimum value"""
        return self._y_axis_min_rt

    @property
    def y_axis_max_rt(self):
        """Returns the Y axis maximum value"""
        return self._y_axis_max_rt

    @property
    def y_axis_num_bars(self):
        """Returns the y axis number of bars"""
        return self.y_axis_num_bars

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict, column_no=1):
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
            cfg_dict.get("yAxisLabelRt", ''),
            cfg_dict.get("yAxisMinRt", 0.0),
            cfg_dict.get("yAxisMaxRt", 1000.0),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
            column_no
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def get_state(self):
        state_str = ""
        for key, line in self.line_dict.items():
            line_format = line.get_line_format()
            if line_format:
                state_str += self._control_hdr_str + "BRDCST\t" + key + line_format
        return state_str

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
        for key, line in self.line_dict.items():
            if line.data:
                line_data = line.get_line_from_timestamp(from_timestamp)
                if line_data:
                    state_str += self._control_hdr_str + dashboard_id + "\t" + key + line_data
        return state_str

    def send_data(self):
        """Sends the latest Data to the iotdashboard app.
        """
        state_str = ""
        for key, line in self.line_dict.items():
            if line.data:
                line_data = line.get_latest_data()
                if line_data:
                    state_str += self._control_hdr_str + key + line_data
        self.state_str = state_str
