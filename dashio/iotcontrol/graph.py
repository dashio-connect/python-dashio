from .control import Control
from .enums import Color, GraphLineType, GraphXAxisLabelsStyle, TitlePosition


class GraphLine:
    def __init__(self, name="", line_type=GraphLineType.LINE, color=Color.BLACK):
        self.name = name
        self.line_type = line_type
        self.color = color
        self.data = []

    def get_line_data(self):
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}\t"
        data_str += "\t".join(map(str, self.data))
        data_str += "\n"
        return data_str


class Graph(Control):
    def get_state(self):
        state_str = ""
        for key in self.line_dict.keys():
            state_str += self._control_hdr_str + key + self.line_dict[key].get_line_data()
        return state_str

    def __init__(
        self,
        control_id,
        title="A Graph",
        title_position=TitlePosition.BOTTOM,
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
        super().__init__("GRPH", control_id, title=title, control_position=control_position, title_position=title_position)
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

    def add_line(self, line_id, gline):
        self.line_dict[line_id] = gline

    def send_graph(self):
        state_str = ""
        for key in self.line_dict.keys():
            state_str += self._control_hdr_str + key + self.line_dict[key].get_line_data()
        self.state_str = state_str

    @property
    def x_axis_label(self) -> str:
        return self._cfg["xAxisLabel"]

    @x_axis_label.setter
    def x_axis_label(self, val: str):
        self._cfg["xAxisLabel"] = val

    @property
    def x_axis_min(self) -> float:
        return self._cfg["xAxisMin"]

    @x_axis_min.setter
    def x_axis_min(self, val: float):
        self._cfg["xAxisMin"] = val

    @property
    def x_axis_max(self) -> float:
        return self._cfg["xAxisMax"]

    @x_axis_max.setter
    def x_axis_max(self, val: float):
        self._cfg["xAxisMax"] = val

    @property
    def x_axis_num_bars(self) -> int:
        return self._cfg["xAxisNumBars"]

    @x_axis_num_bars.setter
    def x_axis_num_bars(self, val: int):
        self._cfg["xAxisNumBars"] = val

    @property
    def x_axis_labels_style(self) -> GraphXAxisLabelsStyle:
        return self._x_axis_labels_style

    @x_axis_labels_style.setter
    def x_axis_labels_style(self, val: GraphXAxisLabelsStyle):
        self._x_axis_labels_style = val
        self._cfg["xAxisLabelsStyle"] = val.value

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
