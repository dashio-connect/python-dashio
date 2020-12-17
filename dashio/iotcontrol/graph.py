from .enums import GraphLineType, Color, GraphXAxisLabelsStyle
from .control import Control


class GraphLine:
    def __init__(self, name="", line_type=GraphLineType.LINE, color=Color.BLACK):
        self.name = name
        self.line_type = line_type
        self.color = color
        self.data = []

    def get_line_data(self):
        data_str = "\t{l_name}\t{l_type}\t{l_color}\t".format(
            l_name=self.name, l_type=self.line_type.value, l_color=self.color.value
        )
        data_str += "\t".join(map(str, self.data))
        data_str += "\n"
        return data_str


class Graph(Control):
    def get_state(self):
        state_str = ""
        for key in self.line_dict.keys():
            state_str += self.get_state_str + key + self.line_dict[key].get_line_data()
        return state_str

    def __init__(
        self,
        control_id,
        x_axis_label="",
        x_axis_min=0.0,
        x_axis_max=100.0,
        x_axis_num_bars=5,
        x_axis_labels_style=GraphXAxisLabelsStyle.ON,
        y_axis_label="",
        y_axis_min=0.0,
        y_axis_max=100.0,
        y_axis_num_bars=5,
        control_position=None,
    ):
        super().__init__("GRPH", control_id, control_position=control_position)

        self.x_axis_label = x_axis_label
        self.x_axis_min = x_axis_min
        self.x_axis_max = x_axis_max
        self.x_axis_num_bars = x_axis_num_bars
        self.x_axis_labels_style = x_axis_labels_style
        self.y_axis_label = y_axis_label
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max
        self.y_axis_num_bars = y_axis_num_bars

        self.line_dict = {}
        self.get_state_str = "\t{}\t{}\t".format(self.msg_type, self.control_id)

    def add_line(self, line_id, gline):
        self.line_dict[line_id] = gline

    def send_graph(self):
        state_str = ""
        for key in self.line_dict.keys():
            state_str += self.get_state_str + key + self.line_dict[key].get_line_data()
        self.state_str = state_str

    @property
    def x_axis_label(self):
        return self._cfg["xAxisLabel"]

    @x_axis_label.setter
    def x_axis_label(self, val):
        self._cfg["xAxisLabel"] = val

    @property
    def x_axis_min(self):
        return self._cfg["xAxisMin"]

    @x_axis_min.setter
    def x_axis_min(self, val):
        self._cfg["xAxisMin"] = val

    @property
    def x_axis_max(self):
        return self._cfg["xAxisMax"]

    @x_axis_max.setter
    def x_axis_max(self, val):
        self._cfg["xAxisMax"] = val

    @property
    def x_axis_num_bars(self):
        return self._cfg["xAxisNumBars"]

    @x_axis_num_bars.setter
    def x_axis_num_bars(self, val):
        self._cfg["xAxisNumBars"] = val

    @property
    def x_axis_labels_style(self):
        return self._x_axis_labels_style

    @x_axis_labels_style.setter
    def x_axis_labels_style(self, val):
        self._x_axis_labels_style = val
        self._cfg["xAxisLabelsStyle"] = val.value

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
