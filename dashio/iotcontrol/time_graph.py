from .enums import TimeGraphLineType, Color, TimeGraphTimeScale, TimeGraphPositionOfKey
from .control import Control

import datetime
import dateutil.parser


class DataPoint:
    def __init__(self, data):
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.data_point = data

    def to_string(self):
        data_str = "{ts},{data}".format(ts=self.timestamp.isoformat(), data=self.data_point)
        return data_str


class TimeGraphLine:
    def __init__(
        self, name="", line_type=TimeGraphLineType.LINE, color=Color.BLACK, transparency=1.0, max_data_points=60
    ):
        self.max_data_points = max_data_points
        self.name = name
        self.line_type = line_type
        self.color = color
        self.transparency = transparency
        self.data = []

    def get_line_data(self):
        if not self.data:
            return ""
        data_str = "\t{l_name}\t{l_type}\t{l_color}\t{l_transparency}".format(
            l_name=self.name, l_type=self.line_type.value, l_color=self.color.value, l_transparency=self.transparency
        )
        for d in self.data:
            data_str += "\t" + d.to_string()
        data_str += "\n"
        return data_str

    def get_line_from_timestamp(self, timestamp):
        if not self.data:
            return ""
        data_str = "\t{l_name}\t{l_type}\t{l_color}\t{l_transparency}".format(
            l_name=self.name, l_type=self.line_type.value, l_color=self.color.value, l_transparency=self.transparency
        )

        dt = dateutil.parser.isoparse(timestamp)

        for d in self.data:
            if d.timestamp > dt:
                data_str += "\t" + d.to_string()
        data_str += "\n"
        return data_str

    def add_data_point(self, data_point):
        """Add and sends a single datapoint to the line. It automatically timestamps to the current time.

        Arguments:
            data_point {str} -- A single data point
        """
        dp = DataPoint(data_point)
        # now = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat()
        # data_str = "{ts},{data}".format(ts=now, data=data_point)
        if len(self.data) < self.max_data_points:
            self.data.append(dp)
            return
        for i in range(len(self.data) - 1):
            self.data[i] = self.data[i + 1]
        self.data[-1] = dp

    def get_latest_data(self):
        if not self.data:
            return ""
        data_str = "\t{l_name}\t{l_type}\t{l_color}\t{l_transparency}".format(
            l_name=self.name, l_type=self.line_type.value, l_color=self.color.value, l_transparency=self.transparency
        )
        data_str += "\t" + self.data[-1].to_string()
        data_str += "\n"
        return data_str


class TimeGraph(Control):
    def get_state(self):
        state_str = ""
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                state_str += self.get_state_str + key + self.line_dict[key].get_latest_data()
        return state_str

    def __init__(
        self,
        control_id,
        timescale=TimeGraphTimeScale.FIFTEENMINS,
        y_axis_label="",
        y_axis_min="0.0",
        y_axis_max=100.0,
        y_axis_num_bars=5,
        graph_key_font_size=12,
        show_connection_in_key=False,
        position_of_key=TimeGraphPositionOfKey.TOPLEFT,
        control_position=None,
    ):
        super().__init__("TGRPH", control_id, control_position=control_position)

        self.message_rx_event += self.__get_lines_from_timestamp

        self.time_scale = timescale
        self.y_axis_label = y_axis_label
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max
        self.y_axis_num_bars = y_axis_num_bars
        self.graph_key_font_size = graph_key_font_size
        self.show_connection_in_key = show_connection_in_key
        self.position_of_key = position_of_key

        self.line_dict = {}
        self.get_state_str = "\t{}\t{}\t".format(self.msg_type, self.control_id)

    def add_line(self, line_id, gline):
        self.line_dict[line_id] = gline

    def send_graph(self):
        state_str = ""
        for key in self.line_dict.keys():
            state_str += self.get_state_str + key + self.line_dict[key].get_line_data()
        self.state_str = state_str

    def __get_lines_from_timestamp(self, msg):
        state_str = ""
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                state_str += self.get_state_str + key + self.line_dict[key].get_line_from_timestamp(msg[0])
        self.state_str = state_str

    def send_data(self):
        state_str = ""
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                state_str += self.get_state_str + key + self.line_dict[key].get_latest_data()
        self.state_str = state_str

    @property
    def time_scale(self) -> TimeGraphTimeScale:
        return self._time_scale

    @time_scale.setter
    def time_scale(self, val: TimeGraphTimeScale):
        self._time_scale = val
        self._cfg["timeScale"] = val.value

    @property
    def y_axis_label(self):
        return self._cfg["yAxisLabel"]

    @y_axis_label.setter
    def y_axis_label(self, val):
        self._cfg["yAxisLabel"] = val

    @property
    def y_axis_min(self):
        return self._cfg["yAxisMin"]

    @y_axis_min.setter
    def y_axis_min(self, val):
        self._cfg["yAxisMin"] = val

    @property
    def y_axis_max(self):
        return self._cfg["yAxisMax"]

    @y_axis_max.setter
    def y_axis_max(self, val):
        self._cfg["yAxisMax"] = val

    @property
    def y_axis_num_bars(self):
        return self._cfg["yAxisNumBars"]

    @y_axis_num_bars.setter
    def y_axis_num_bars(self, val):
        self._cfg["yAxisNumBars"] = val

    @property
    def graph_key_font_size(self):
        return self._cfg["graphKeyFontSize"]

    @graph_key_font_size.setter
    def graph_key_font_size(self, val):
        self._cfg["graphKeyFontSize"] = val

    @property
    def show_connection_in_key(self):
        return self._cfg["showConnectionInKey"]

    @show_connection_in_key.setter
    def show_connection_in_key(self, val):
        self._cfg["showConnectionInKey"] = val

    @property
    def position_of_key(self) -> TimeGraphPositionOfKey:
        return self._position_of_key

    @position_of_key.setter
    def position_of_key(self, val: TimeGraphPositionOfKey):
        self._position_of_key = val
        self._cfg["positionOfKey"] = val.value

