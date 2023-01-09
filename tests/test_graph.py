import json
import unittest

from dashio import Graph, GraphLine
from dashio.iotcontrol.enums import Color, GraphLineType, GraphXAxisLabelsStyle


class TestGraph(unittest.TestCase):
    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_graph_line(self):
        test_data = GraphLine("GRAPHLINE", line_type=GraphLineType.LINE, color=Color.BLACK)
        test_str_list = test_data.get_line_data().split('\t')
        self.assertEqual(GraphLineType(test_str_list[2]), GraphLineType.LINE, "line type should be LINE")
        self.assertEqual(Color(int(test_str_list[3])), Color.BLACK, "Color should be BLACK")

    def test_graph_control_type(self):
        test_control = Graph("GRAPHID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'GRPH', "control type should be GRPH")

    def test_graph_control_id(self):
        test_control = Graph("GRAPHID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'GRAPHID', "control_id type should be GRAPHID")

    def test_graph_x_axis_label(self):
        test_control = Graph("GRAPHID", x_axis_label="XAXISLABEL")
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['xAxisLabel'], 'XAXISLABEL', "CFG xAxisLabel Should be 'XAXISLABEL'")

    def test_graph_y_axis_label(self):
        test_control = Graph("GRAPHID", y_axis_label="YAXISLABEL")
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisLabel'], 'YAXISLABEL', "CFG yAxisLabel Should be 'YAXISLABEL'")

    def test_graph_x_axis_min(self):
        test_control = Graph("GRAPHID", x_axis_min=1.0)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['xAxisMin'], 1.0, "CFG xAxisMin Should be 1.0")

    def test_graph_y_axis_min(self):
        test_control = Graph("GRAPHID", y_axis_min=1.0)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisMin'], 1.0, "CFG yAxisMin Should be 1.0")

    def test_graph_x_axis_max(self):
        test_control = Graph("GRAPHID", x_axis_max=1.0)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['xAxisMax'], 1.0, "CFG xAxisMax Should be 1.0")

    def test_graph_y_axis_max(self):
        test_control = Graph("GRAPHID", y_axis_max=1.0)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisMax'], 1.0, "CFG yAxisMax Should be 1.0")

    def test_graph_x_axis_num_bars(self):
        test_control = Graph("GRAPHID", x_axis_num_bars=5)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['xAxisNumBars'], 5, "CFG xAxisNumBars Should be 5")

    def test_graph_x_axis_labels_style(self):
        test_control = Graph("GRAPHID", x_axis_labels_style=GraphXAxisLabelsStyle.BETWEEN)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(GraphXAxisLabelsStyle(cfg_dict['xAxisLabelsStyle']), GraphXAxisLabelsStyle.BETWEEN, "CFG xAxisLabelsStyle Should be BETWEEN")


if __name__ == '__main__':
    unittest.main()
