import json
import unittest

from dashio import ButtonGroup


def _get_cfg_dict(cfg_str):
    json_str = cfg_str.rpartition('\t')[2]
    return json.loads(json_str)


class TestButtonGroup(unittest.TestCase):

    def test_button_group_control_type(self):
        test_control = ButtonGroup("BGROUPID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'BTGP', "control type should be BTGP")

    def test_button_group_control_id(self):
        test_control = ButtonGroup("BGROUPID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'BGROUPID', "control type should be BGROUPID")


if __name__ == '__main__':
    unittest.main()
