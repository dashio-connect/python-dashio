import json
import unittest

from dashio import Color, TextBox
from dashio.iotcontrol.control import _get_color_str
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
        test_control = TextBox("TEXTID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'TEXT', "control type should be TEXT")

    def test_text_box_control_id(self):
        test_control = TextBox("TEXTID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'TEXTID', "control type should be TEXTID")

    def test_text_box_cfg_text_align(self):
        test_control = TextBox("TEXTID", text_align=TextAlignment.CENTER)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(TextAlignment(cfg_dict['textAlign']), TextAlignment.CENTER, "CFG textAlign should be CENTER")

    def test_text_box_cfg_text_format(self):
        test_control = TextBox("TEXTID", text_format=TextFormat.NUM)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(TextFormat(cfg_dict['format']), TextFormat.NUM, "CFG format should be CENTER")

    def test_text_box_cfg_units(self):
        test_control = TextBox("TEXTID", units='Amps')
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['units'], 'Amps', "CFG units should be 'Amps'")

    def test_text_box_cfg_keyboard_type(self):
        test_control = TextBox("TEXTID", keyboard_type=Keyboard.HEX)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Keyboard(cfg_dict['kbdType']), Keyboard.HEX, "CFG kbdType should be HEX")

    def test_text_box_cfg_precision(self):
        test_control = TextBox("TEXTID", precision=Precision.SIX)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Precision(cfg_dict['precision']), Precision.SIX, "CFG precision should be SIX")

    def test_text_box_cfg_close_keyboard_on_send(self):
        test_control = TextBox("TEXTID", close_keyboard_on_send=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['closeKbdOnSend'], True, "CFG closeKbdOnSend should be True")

    def _sent(self, control):
        sent = []
        control._message_tx_event += sent.append
        return sent

    def test_color_is_sent_when_set(self):
        test_control = TextBox("TEXTID")
        test_control.text = "CC"
        sent = self._sent(test_control)
        test_control.color = Color.ORANGE
        self.assertEqual(sent, [f"\t{{device_id}}\tTEXT\tTEXTID\tCC\t{_get_color_str(Color.ORANGE)}\n"])

    def test_state_has_color(self):
        test_control = TextBox("TEXTID")
        test_control.color = Color.ORANGE
        test_control.text = "CC"
        self.assertEqual(test_control.get_state(), f"\t{{device_id}}\tTEXT\tTEXTID\tCC\t{_get_color_str(Color.ORANGE)}\n")

    def test_state_has_caption(self):
        test_control = TextBox("TEXTID")
        test_control.text = "21.5"
        test_control.caption_color = Color.RED
        test_control.caption = "Too hot"
        self.assertEqual(test_control.get_state(),
                         f"\t{{device_id}}\tTEXT\tTEXTID\t21.5\t{_get_color_str(Color.WHITE)}\n"
                         f"\t{{device_id}}\tTXTC\tTEXTID\tToo hot\t{_get_color_str(Color.RED)}\n")

    def test_caption_color_is_sent_with_caption(self):
        test_control = TextBox("TEXTID")
        sent = self._sent(test_control)
        test_control.caption_color = Color.RED  # No caption yet: nothing to send
        self.assertEqual(sent, [])
        test_control.caption = "Too hot"
        test_control.caption_color = Color.GREEN
        self.assertEqual(sent[-1], f"\t{{device_id}}\tTXTC\tTEXTID\tToo hot\t{_get_color_str(Color.GREEN)}\n")


if __name__ == '__main__':
    unittest.main()
