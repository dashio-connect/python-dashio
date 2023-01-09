import json
import unittest

from dashio import Label
from dashio.iotcontrol.enums import Color, LabelStyle


class TestLabel(unittest.TestCase):
    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_label_control_type(self):
        test_control = Label("LABELID", color=Color.BLUE)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Color(int(cfg_dict['color'])), Color.BLUE, "CFG yAxisMax Should be 1.0")

    def test_label_control_id(self):
        test_control = Label("LABELID", style=LabelStyle.BORDER)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(LabelStyle(cfg_dict['style']), LabelStyle.BORDER, "CFG style Should be 1.0")


if __name__ == '__main__':
    unittest.main()
