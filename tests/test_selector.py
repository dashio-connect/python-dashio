import json
import unittest

from dashio import Selector

def _get_cfg_dict(cfg_str):
    json_str = cfg_str.rpartition('\t')[2]
    return json.loads(json_str)


class TestSelector(unittest.TestCase):

    def test_selector_control_type(self):
        test_control = Selector("SELECTORID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'SLCTR', "control type should be SLCTR")

    def test_selector_control_id(self):
        test_control = Selector("SELECTORID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'SELECTORID', "control type should be SELECTORID")

    def test_selector_set_selected(self):
        test_control = Selector("SELECTORID")
        test_control.add_selection("ASELECTION")
        test_control.set_selected("ASELECTION")
        test_str_list = test_control._tx_message.split('\t')
        self.assertEqual(test_str_list[5], 'ASELECTION\n', "control type should be SELECTORID")



if __name__ == '__main__':
    unittest.main()
