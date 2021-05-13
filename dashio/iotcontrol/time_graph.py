from .enums import TimeGraphLineType, Color, TitlePosition
from .control import Control
from .ring_buffer import RingBuffer
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
        self, name="", line_type=TimeGraphLineType.LINE, color=Color.BLACK, max_data_points=60, break_data=False
    ):
        self.name = name
        self.line_type = line_type
        self.color = color
        self.break_data = break_data
        self.data = RingBuffer(max_data_points)

    def get_line_data(self):
        if self.data.empty():
            return ""
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}"
        for d in self.data.get():
            data_str += "\t" + d.to_string()
        data_str += "\n"
        return data_str

    def get_line_from_timestamp(self, timestamp):
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}"
        dt = dateutil.parser.isoparse(timestamp)
        first = True
        valid_data = False
        data_list = self.data.get()
        for d in data_list:
            if d.timestamp > dt:
                if first and self.break_data:
                    data_str += "\t" + "{ts},{ldata}".format(ts=d.timestamp.isoformat(), ldata="b") 
                data_str += "\t" + d.to_string()
                valid_data = True
            first = False
        data_str += "\n"
        if not valid_data:
             data_str = ""
        return data_str

    def add_data_point(self, data_point):
        """Add and sends a single datapoint to the line. It automatically timestamps to the current time.

        Arguments:
            data_point {str} -- A single data point
        """
        dp = DataPoint(data_point)
        self.data.append(dp)

    def get_latest_data(self):
        if self.data.empty():
            return ""
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}"
        data_str += "\t" + self.data.get_latest().to_string()
        data_str += "\n"
        return data_str


class TimeGraph(Control):
    def get_state(self):
        return ""

    def __init__(
        self,
        control_id,
        title="A TimeGraph",
        title_position=TitlePosition.BOTTOM,
        y_axis_label="Y axis",
        y_axis_min=0.0,
        y_axis_max=100.0,
        y_axis_num_bars=5,
        control_position=None,
    ):
        super().__init__("TGRPH", control_id, title=title, control_position=control_position, title_position=title_position)
        self.message_rx_event = self.__get_lines_from_timestamp

        self.y_axis_label = y_axis_label
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max
        self.y_axis_num_bars = y_axis_num_bars

        self.line_dict = {}

    def add_line(self, line_id: str, gline: TimeGraphLine):
        self.line_dict[line_id] = gline

    def send_graph(self):
        state_str = ""
        for key in self.line_dict.keys():
            state_str += self._state_str + key + self.line_dict[key].get_line_data()
        self.state_str = state_str

    def __get_lines_from_timestamp(self, msg):
        state_str = ""
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                line_data = self.line_dict[key].get_line_from_timestamp(msg[3])
                if line_data:
                    state_str += self._state_str + key + line_data
        self.state_str = state_str

    def send_data(self):
        state_str = ""
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                line_data = self.line_dict[key].get_latest_data()
                if line_data:
                    state_str += self._state_str + key + line_data
        self.state_str = state_str

    @property
    def y_axis_label(self) -> str:
        return self._cfg["yAxisLabel"]

    @y_axis_label.setter
    def y_axis_label(self, val: str):
        self._cfg["yAxisLabel"] = val

    @property
    def y_axis_min(self) -> float:
        return self._cfg["yAxisMin"]

    @y_axis_min.setter
    def y_axis_min(self, val: float):
        self._cfg["yAxisMin"] = val

    @property
    def y_axis_max(self) -> float:
        return self._cfg["yAxisMax"]

    @y_axis_max.setter
    def y_axis_max(self, val: float):
        self._cfg["yAxisMax"] = val

    @property
    def y_axis_num_bars(self) -> int:
        return self._cfg["yAxisNumBars"]

    @y_axis_num_bars.setter
    def y_axis_num_bars(self, val: int):
        self._cfg["yAxisNumBars"] = val
