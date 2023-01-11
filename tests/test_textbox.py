import json
import unittest

from dashio import TextBox
from dashio.iotcontrol.enums import (
    Keyboard,
    Precision,
    TextAlignment,
    TextFormat
)


def _get_cfg_dict(cfg_list: list):
    json_str = cfg_list[0].rpartition('\t')[2]
    return json.loads(json_str)


class TestTextBox(unittest.TestCase):

    def test_text_box_control_type(self):
        test_control = TextBox("TEXTBOXID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'TEXT', "control type should be TEXT")

    def test_text_box_control_id(self):
        test_control = TextBox("TEXTBOXID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'TEXTBOXID', "control type should be TEXTBOXID")

    def test_text_box_cfg_text_align(self):
        test_control = TextBox("TEXTBOXID", text_align=TextAlignment.CENTER)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(TextAlignment(cfg_dict['textAlign']), TextAlignment.CENTER, "CFG textAlign should be CENTER")

    def test_text_box_cfg_text_format(self):
        test_control = TextBox("TEXTBOXID", text_format=TextFormat.NUMBER)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(TextFormat(cfg_dict['format']), TextFormat.NUMBER, "CFG format should be CENTER")

    def test_text_box_cfg_units(self):
        test_control = TextBox("TEXTBOXID", units='Amps')
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['units'], 'Amps', "CFG units should be 'Amps'")

    def test_text_box_cfg_keyboard_type(self):
        test_control = TextBox("TEXTBOXID", keyboard_type=Keyboard.HEX)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Keyboard(cfg_dict['kbdType']), Keyboard.HEX, "CFG kbdType should be HEX")

    def test_text_box_cfg_precision(self):
        test_control = TextBox("TEXTBOXID", precision=Precision.SIX)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Precision(cfg_dict['precision']), Precision.SIX, "CFG precision should be SIX")

    def test_text_box_cfg_close_keyboard_on_send(self):
        test_control = TextBox("TEXTBOXID", close_keyboard_on_send=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['closeKbdOnSend'], True, "CFG closeKbdOnSend should be True")


if __name__ == '__main__':
    unittest.main()
