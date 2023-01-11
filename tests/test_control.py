import json
import unittest

from dashio import Control


class TestControl(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_control_id(self):
        test_control = Control("CONTROLTYPE", "CONTROLID")
        self.assertEqual(test_control._control_hdr_str, '\t{device_id}\tCONTROLTYPE\tCONTROLID\t', "ControlID Should be CONTROLID")


if __name__ == '__main__':
    unittest.main()
