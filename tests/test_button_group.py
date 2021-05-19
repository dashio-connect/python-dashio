import unittest
import json
from dashio import ButtonGroup
from dashio.iotcontrol.enums import Color, Icon

def _get_cfg_dict(cfg_str):
    json_str = cfg_str.rpartition('\t')[2]
    return json.loads(json_str)


class TestButtonGroup(unittest.TestCase):

    def test_button_group_control_type(self):
        test_control = ButtonGroup("BGROUPID")
        test_str_list = test_control._state_str.split('\t')
        self.assertEqual(test_str_list[2], 'BTGP', "control type should be BTGP")

    def test_button_group_control_id(self):
        test_control = ButtonGroup("BGROUPID")
        test_str_list = test_control._state_str.split('\t')
        self.assertEqual(test_str_list[3], 'BGROUPID', "control type should be BGROUPID")

    def test_time_graph_cfg_grid_view(self):
        test_control = ButtonGroup("BGROUPID", grid_view=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['gridView'], True, "CFG gridView should be True")

    def test_time_graph_cfg_icon_name(self):
        test_control = ButtonGroup("BGROUPID", icon=Icon.BEDROOM)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Icon(cfg_dict['iconName']), Icon.BEDROOM, "CFG icon_name should be BEDROOM")

    def test_time_graph_cfg_text(self):
        test_control = ButtonGroup("BGROUPID", text="TEXT")
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['text'], "TEXT", "CFG text should be TEXT")


if __name__ == '__main__':
    unittest.main()
