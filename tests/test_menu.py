import json
import unittest

from dashio import Menu
from dashio.iotcontrol.enums import Icon


def _get_cfg_dict(cfg_list: list):
    json_str = cfg_list[0].rpartition('\t')[2]
    return json.loads(json_str)


class TestMenu(unittest.TestCase):

    def test_menu_control_type(self):
        test_control = Menu("MENUID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'MENU', "control type should be KNOB")

    def test_menu_control_id(self):
        test_control = Menu("MENUID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'MENUID', "control type should be KNOBID")

    def test_menu_cfg_icon_name(self):
        test_control = Menu("MENUID", icon_name=Icon.ON_OFF)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Icon(cfg_dict['iconName']), Icon.ON_OFF, "CFG iconName should be iconName")

    def test_menu_cfg_text(self):
        test_control = Menu("MENUID", text="TEXT")
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['text'], "TEXT", "CFG text should be TEXT")


if __name__ == '__main__':
    unittest.main()
