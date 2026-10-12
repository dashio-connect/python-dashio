import json
import unittest

from dashio import Control, Dial


class TestControl(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_control_id(self):
        test_control = Control("CONTROLTYPE", "CTRLID")
        self.assertEqual(test_control._control_hdr_str, '\t{device_id}\tCONTROLTYPE\tCTRLID\t', "ControlID Should be CTRLID")

    def test_control_id_up_to_7_characters(self):
        self.assertEqual(Control("CONTROLTYPE", "ABCDEFG").control_id, "ABCDEFG")

    def test_control_id_over_7_characters(self):
        with self.assertRaises(ValueError):
            Control("CONTROLTYPE", "ABCDEFGH")
        with self.assertRaises(ValueError):
            Dial("ABCDEFGH")


if __name__ == '__main__':
    unittest.main()
