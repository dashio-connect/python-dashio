from dashio.iotcontrol.enums import Color
import unittest
import json
from dashio import Knob

class TestKnob(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_knob_control_type(self):
        test_control = Knob("KNOBID")
        test_str_list = test_control._state_str.split('\t')
        self.assertEqual(test_str_list[2], 'KNOB', "control type should be KNOB")

    def test_knob_control_id(self):
        test_control = Knob("KNOBID")
        test_str_list = test_control._state_str.split('\t')
        self.assertEqual(test_str_list[3], 'KNOBID', "control type should be KNOBID")
        
    
    
if __name__ == '__main__':
    unittest.main()
