import json
import unittest

from dashio import TimeGraph


def _get_cfg_dict(cfg_list: list):
    json_str = cfg_list[0].rpartition('\t')[2]
    return json.loads(json_str)


class TestTimeGraph(unittest.TestCase):

    def test_time_graph_control_type(self):
        test_control = TimeGraph("TIMEGRAPHID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'TGRPH', "control type should be TEXT")

    def test_time_graph_control_id(self):
        test_control = TimeGraph("TIMEGRAPHID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'TIMEGRAPHID', "control type should be TEXTBOXID")

    def test_time_graph_cfg_y_axis_label(self):
        test_control = TimeGraph("TIMEGRAPHID", y_axis_label='YAXIS')
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisLabel'], 'YAXIS', "CFG yAxisLabel should be YAXIS")

    def test_time_graph_cfg_y_axis_min(self):
        test_control = TimeGraph("TIMEGRAPHID", y_axis_min=1.2)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisMin'], 1.2, "CFG yAxisMin should be 1.2")

    def test_time_graph_cfg_y_axis_max(self):
        test_control = TimeGraph("TIMEGRAPHID", y_axis_max=1.9)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisMax'], 1.9, "CFG yAxisMin should be 1.9")

    def test_time_graph_cfg_y_axis_num_bars(self):
        test_control = TimeGraph("TIMEGRAPHID", y_axis_num_bars=3)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['yAxisNumBars'], 3, "CFG yAxisNumBars should be 3")


if __name__ == '__main__':
    unittest.main()
