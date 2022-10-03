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
from .control import Control, ControlPosition, _get_title_position, _get_graph_x_axis_labels_style
from .enums import Color, GraphLineType, GraphXAxisLabelsStyle, TitlePosition

class GraphLine:
    """GraphLine class
    """
    def __init__(self, name="", line_type=GraphLineType.LINE, color=Color.BLACK):
        self.name = name.translate(BAD_CHARS)
        self.line_type = line_type
        self.color = color
        self.data = []

    def get_line_data(self):
        """Returns the line data formated for the iotdashboard app

        Returns
        -------
        str
            The formatted line data
        """
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}\t"
        data_str += "\t".join(map(str, self.data))
        data_str += "\n"
        return data_str


class Graph(Control):
    """A Graph control

    Parameters
    ----------
    Control :
        The control base class
    """
    def get_state(self):
        """Called by iotdashboard"""
        state_str = ""
        for key in self.line_dict:
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

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Graph from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Graph
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["xAxisLabel"],
            cfg_dict["xAxisMin"],
            cfg_dict["xAxisMax"],
            cfg_dict["xAxisNumBars"],
            _get_graph_x_axis_labels_style(cfg_dict["xAxisLabelsStyle"]),
            cfg_dict["yAxisLabel"],
            cfg_dict["yAxisMin"],
            cfg_dict["yAxisMax"],
            cfg_dict["yAxisNumBars"],
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def add_line(self, line_id: str, gline: GraphLine):
        """Add a line to the graph

        Parameters
        ----------
        line_id : str
            A unique to this graph line identifier
        gline : GraphLine
            The line to add
        """
        self.line_dict[line_id.translate(BAD_CHARS)] = gline

    def send_graph(self):
        """Sends the graph to any connected iotdashboard app.
        """
        state_str = ""
        for key in self.line_dict:
            state_str += self._control_hdr_str + key + self.line_dict[key].get_line_data()
        self.state_str = state_str

    @property
    def x_axis_label(self) -> str:
        """Returns the x_axis_label string.

        Returns
        -------
        str
            The x_axis_label
        """
        return self._cfg["xAxisLabel"]

    @x_axis_label.setter
    def x_axis_label(self, val: str):
        self._cfg["xAxisLabel"] = val.translate(BAD_CHARS)

    @property
    def x_axis_min(self) -> float:
        """Returns the x_axis_min

        Returns
        -------
        float
            The x_axis_min
        """
        return self._cfg["xAxisMin"]

    @x_axis_min.setter
    def x_axis_min(self, val: float):
        self._cfg["xAxisMin"] = val

    @property
    def x_axis_max(self) -> float:
        """Returns the x_axis_max

        Returns
        -------
        float
            The x_axis_max
        """
        return self._cfg["xAxisMax"]

    @x_axis_max.setter
    def x_axis_max(self, val: float):
        self._cfg["xAxisMax"] = val

    @property
    def x_axis_num_bars(self) -> int:
        """Returns the x_axis_num_bars

        Returns
        -------
        int
            The x_axis_num_bars
        """
        return self._cfg["xAxisNumBars"]

    @x_axis_num_bars.setter
    def x_axis_num_bars(self, val: int):
        self._cfg["xAxisNumBars"] = val

    @property
    def x_axis_labels_style(self) -> GraphXAxisLabelsStyle:
        """Returns the x_axis_labels_style

        Returns
        -------
        GraphXAxisLabelsStyle
            The x_axis_labels_style
        """
        return self._x_axis_labels_style

    @x_axis_labels_style.setter
    def x_axis_labels_style(self, val: GraphXAxisLabelsStyle):
        self._x_axis_labels_style = val
        self._cfg["xAxisLabelsStyle"] = val.value

    @property
    def y_axis_label(self) -> str:
        """Returns the y_axis_label

        Returns
        -------
        str
            The y_axis_label
        """
        return self._cfg["yAxisLabel"]

    @y_axis_label.setter
    def y_axis_label(self, val: str):
        self._cfg["yAxisLabel"] = val.translate(BAD_CHARS)

    @property
    def y_axis_min(self) -> float:
        """Returns the y_axis_min

        Returns
        -------
        float
            The y_axis_min
        """
        return self._cfg["yAxisMin"]

    @y_axis_min.setter
    def y_axis_min(self, val: float):
        self._cfg["yAxisMin"] = val

    @property
    def y_axis_max(self) -> float:
        """Returns the y_axis_max

        Returns
        -------
        float
            The y_axis_max
        """
        return self._cfg["yAxisMax"]

    @y_axis_max.setter
    def y_axis_max(self, val: float):
        self._cfg["yAxisMax"] = val

    @property
    def y_axis_num_bars(self) -> int:
        """Returns the y_axis_num_bars

        Returns
        -------
        int
            The y_axis_num_bars
        """
        return self._cfg["yAxisNumBars"]

    @y_axis_num_bars.setter
    def y_axis_num_bars(self, val: int):
        self._cfg["yAxisNumBars"] = val
