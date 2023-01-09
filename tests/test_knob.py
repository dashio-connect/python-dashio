import json
import unittest

from dashio import Knob
from dashio.iotcontrol.enums import Color


class TestKnob(unittest.TestCase):
    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_knob_control_type(self):
        test_control = Knob("KNOBID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'KNOB', "control type should be KNOB")

    def test_knob_control_id(self):
        test_control = Knob("KNOBID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'KNOBID', "control type should be KNOBID")

    def test_knob_cfg_min(self):
        test_control = Knob("KNOBID", dial_min=10)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['min'], 10, "CFG min should be 10")

    def test_knob_cfg_max(self):
        test_control = Knob("KNOBID", dial_max=10)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['max'], 10, "CFG max should be 10")

    def test_knob_cfg_red_value(self):
        test_control = Knob("KNOBID", red_value=10)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['redValue'], 10, "CFG redValue should be 10")

    def test_knob_cfg_show_min_max(self):
        test_control = Knob("KNOBID", show_min_max=True)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['showMinMax'], True, "CFG showMinMax should be True")

    def test_knob_cfg_send_only_on_release(self):
        test_control = Knob("KNOBID", send_only_on_release=True)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['sendOnlyOnRelease'], True, "CFG sendOnlyOnRelease should be True")

    def test_knob_cfg_dial_follows_knob(self):
        test_control = Knob("KNOBID", dial_follows_knob=True)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['dialFollowsKnob'], True, "CFG dialFollowsKnob should be True")

    def test_knob_cfg_dial_color(self):
        test_control = Knob("KNOBID", dial_color=Color.AQUA)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Color(int(cfg_dict['dialColor'])), Color.AQUA, "CFG dialColor should be AQUA")

    def test_knob_cfg_knob_color(self):
        test_control = Knob("KNOBID", knob_color=Color.AQUAMARINE)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Color(int(cfg_dict['knobColor'])), Color.AQUAMARINE, "CFG knobColor should be AQUA")


if __name__ == '__main__':
    unittest.main()
