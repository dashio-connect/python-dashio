import unittest
import json

from dashio import Control, ControlPosition, TitlePosition

class TestControl(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_control_id(self):
        test_control = Control("CONTROLTYPE","CONTROLID")
        self.assertEqual(test_control._state_str, '\t{device_id}\tCONTROLTYPE\tCONTROLID\t', "ControlID Should be CONTROLID")

    def test_control_cfg(self):
        test_control = Control("CONTROLTYPE","CONTROLID")
        self.assertEqual(test_control.get_cfg(1,1), '\tCFG\tCONTROLTYPE\t{"controlID": "CONTROLID"}\n', "CFG ControlType Should be CONTROLTYPE")

    def test_control_title(self):
        test_control = Control("CONTROLTYPE","CONTROLID", title="TITLE")
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['title'], "TITLE", "CFG title Should be TITLE")

    def test_control_title_position(self):
        test_control = Control("CONTROLTYPE","CONTROLID", title_position=TitlePosition.BOTTOM)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['titlePosition'], "Bottom", "CFG titlePosition Should be Bottom")

    def test_control_control_position(self):
        test_control = Control("CONTROLTYPE", "CONTROLID", control_position=ControlPosition(0.1, 0.2, 0.9, 1))
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['xPositionRatio'], 0.1, "CFG xPositionRatio should be 0")
        self.assertEqual(cfg_dict['yPositionRatio'], 0.2, "CFG yPositionRatio should be 0")
        self.assertEqual(cfg_dict['widthRatio'], 0.9, "CFG widthRatio should be 0")
        self.assertEqual(cfg_dict['heightRatio'], 1, "CFG heightRatio should be 0")

if __name__ == '__main__':
    unittest.main()
