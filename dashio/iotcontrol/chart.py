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
from .control import Control, ControlPosition, ControlConfig, _get_title_position, _get_chart_x_axis_labels_style
from .enums import Color, ChartLineType, ChartXAxisLabelsStyle, TitlePosition


class ChartLine:
    """ChartLine class
    """
    def __init__(self, name="", line_type=ChartLineType.LINE, color=Color.BLACK, right_axis=False):
        self.name = name.translate(BAD_CHARS)
        self.line_type = line_type
        self.color = color
        self.data = []
        self.axis_side = 'left'
        if right_axis:
            self.axis_side = 'right'

    def get_line_data(self):
        """Returns the line data formated for the iotdashboard app

        Returns
        -------
        str
            The formatted line data
        """
        data_str = f"\t{self.name}\t{self.line_type.value}\t{self.color.value}\t{self.axis_side}\t"
        data_str += "\t".join(map(str, self.data))
        data_str += "\n"
        return data_str


class ChartConfig(ControlConfig):
    """ChartConfig"""
    def __init__(
        self,
        control_id,
        title: str,
        title_position: TitlePosition,
        x_axis_label: str,
        x_axis_min: float,
        x_axis_max: float,
        x_axis_num_bars: int,
        x_axis_labels_style: ChartXAxisLabelsStyle,
        y_axis_label: str,
        y_axis_min: float,
        y_axis_max: float,
        y_axis_num_bars: int,
        y_axis_label_rt: str,
        y_axis_min_rt: float,
        y_axis_max_rt: float,
        control_position: ControlPosition,
    ) -> None:
        super().__init__(control_id, title, control_position, title_position)
        self.cfg["xAxisLabel"] = x_axis_label.translate(BAD_CHARS)
        self.cfg["xAxisMin"] = x_axis_min
        self.cfg["xAxisMax"] = x_axis_max
        self.cfg["xAxisNumBars"] = x_axis_num_bars
        self.cfg["xAxisLabelsStyle"] = x_axis_labels_style.value
        self.cfg["yAxisLabel"] = y_axis_label.translate(BAD_CHARS)
        self.cfg["yAxisMin"] = y_axis_min
        self.cfg["yAxisMax"] = y_axis_max
        self.cfg["yAxisNumBars"] = y_axis_num_bars
        self.cfg["yAxisLabelRt"] = y_axis_label_rt.translate(BAD_CHARS)
        self.cfg["yAxisMinRt"] = y_axis_min_rt
        self.cfg["yAxisMaxRt"] = y_axis_max_rt

    @classmethod
    def from_dict(cls, cfg_dict: dict):
        """Instantiates GraphConfig from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        GraphConfig
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["xAxisLabel"],
            cfg_dict["xAxisMin"],
            cfg_dict["xAxisMax"],
            cfg_dict["xAxisNumBars"],
            _get_chart_x_axis_labels_style(cfg_dict["xAxisLabelsStyle"]),
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


class Chart(Control):
    """A Chart control

    Parameters
    ----------
    Control :
        The control base class
    """

    def get_state(self):
        """Called by iotdashboard"""
        state_str = ""
        for key, line in self.line_dict.items():
            state_str += self._control_hdr_str + key + line.get_line_data()
        return state_str

    def __init__(
        self,
        control_id,
        title="A Chart",
        title_position=TitlePosition.BOTTOM,
        x_axis_label="",
        x_axis_min=0.0,
        x_axis_max=100.0,
        x_axis_num_bars=5,
        x_axis_labels_style=ChartXAxisLabelsStyle.ON,
        y_axis_label="",
        y_axis_min=0.0,
        y_axis_max=1000.0,
        y_axis_num_bars=5,
        y_axis_label_rt="",
        y_axis_min_rt=0.0,
        y_axis_max_rt=1000.0,
        control_position=None,
        column_no=1
    ):
        """A Chart Control

        Parameters
        ----------
        control_id : str
            A unique identifier for this control
        title : str, optional
            The title for this control will be displayed on the iotdashboard app, by default "A Chart"
        title_position : TitlePosition, optional
            The position of the title, by default TitlePosition.BOTTOM
        x_axis_label : str, optional
            The label for the X axis, by default ""
        x_axis_min : float, optional
            Min value for the X axis, by default 0.0
        x_axis_max : float, optional
            Max value for the X axis, by default 100.0
        x_axis_num_bars : int, optional
            Number of bars on the X axis, by default 5
        x_axis_labels_style : ChartXAxisLabelsStyle, optional
            The style for the X axis, by default ChartXAxisLabelsStyle.ON
        y_axis_label : str, optional
            The label for the Y axis,, by default ""
        y_axis_min : float, optional
            Min value for the Y axis, by default 0.0
        y_axis_max : float, optional
            Max value for the Y axis, by default 100.0
        y_axis_num_bars : int, optional
            Number of bars on the Y axis, by default 5
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        column_no : int, optional default is 1. Must be 1..3
            The Dash App reports its screen size in columns. column_no allows you to specify which column no to load into.
            Each control can store three configs that define how the device looks for Dash apps installed on single column
            phones or 2 column fold out phones or 3 column tablets.
        """
        super().__init__("CHRT", control_id)
        self._app_columns_cfg[str(column_no)].append(
            ChartConfig(
                control_id,
                title,
                title_position,
                x_axis_label,
                x_axis_min,
                x_axis_max,
                x_axis_num_bars,
                x_axis_labels_style,
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
        self.line_dict = {}
        self._x_axis_min = x_axis_min
        self._x_axis_max = x_axis_max
        self._x_axis_num_bars = x_axis_num_bars
        self._y_axis_min = y_axis_min
        self._y_axis_max = y_axis_max
        self._y_axis_num_bars = y_axis_num_bars
        self._y_axis_min_rt = y_axis_min_rt
        self._y_axis_max_rt = y_axis_max_rt

    @property
    def x_axis_min(self):
        """Returns the X axis minimum value"""
        return self._x_axis_min

    @property
    def x_axis_max(self):
        """Returns the X axis maximum value"""
        return self._x_axis_max

    @property
    def x_axis_num_bars(self):
        """Returns the x axis number of bars"""
        return self._x_axis_num_bars

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
        """Returns the Y axis minimum value right side"""
        return self._y_axis_min_rt

    @property
    def y_axis_max_rt(self):
        """Returns the Y axis maximum value right side"""
        return self._y_axis_max_rt

    @property
    def y_axis_num_bars(self):
        """Returns the y axis number of bars"""
        return self.y_axis_num_bars

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict, column_no=1):
        """Instatiates Chart from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Chart
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            cfg_dict["xAxisLabel"],
            cfg_dict["xAxisMin"],
            cfg_dict["xAxisMax"],
            cfg_dict["xAxisNumBars"],
            _get_chart_x_axis_labels_style(cfg_dict["xAxisLabelsStyle"]),
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

    def add_line(self, line_id: str, gline: ChartLine):
        """Add a line to the chart

        Parameters
        ----------
        line_id : str
            A unique to this chart line identifier
        gline : GraphLine
            The line to add
        """
        self.line_dict[line_id.translate(BAD_CHARS)] = gline

    def send_chart(self):
        """Sends the chart to any connected iotdashboard app.
        """
        state_str = ""
        for key, line in self.line_dict.items():
            state_str += self._control_hdr_str + key + line.get_line_data()
        self.state_str = state_str
