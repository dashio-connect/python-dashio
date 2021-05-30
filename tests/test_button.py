import json
import unittest

from dashio import Button, ButtonState, Color, Icon, TitlePosition


class TestButton(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_button_button_enabled(self):
        test_control = Button("BUTTONID", button_enabled=True)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['buttonEnabled'], True, "CFG buttonEnabled Should be True")

    def test_button_icon_name(self):
        test_control = Button("BUTTONID", icon_name=Icon.PAD)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['iconName'], "Pad", "CFG iconName Should be Pad")

    def test_button_on_color(self):
        test_control = Button("BUTTONID", on_color=Color.GREEN)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['onColor'], '10', "CFG onColor Should be '10'")

    def test_button_off_color(self):
        test_control = Button("BUTTONID", off_color=Color.GREEN)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['offColor'], '10', "CFG onColor Should be '10'")

    def test_button_text(self):
        test_control = Button("BUTTONID", text="TEXT")
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['text'], 'TEXT', "CFG text Should be 'TEXT'")

    def test_button_state_on(self):
        test_control = Button("BUTTONID")
        test_control.btn_state = ButtonState.ON
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tON\n', "Should be 'ON'")

    def test_button_state_off(self):
        test_control = Button("BUTTONID")
        test_control.btn_state = ButtonState.OFF
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tOFF\n', "Should be 'OFF'")

    def test_button_state_flash(self):
        test_control = Button("BUTTONID")
        test_control.btn_state = ButtonState.FLASH
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tFLASH\n', "Should be 'FLASH'")

    def test_button_set_icon(self):
        test_control = Button("BUTTONID")
        test_control.icon_name = Icon.UP
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tOFF\tUp\n', "Icon Should be UP")

    def test_button_set_text(self):
        test_control = Button("BUTTONID")
        test_control.text = "HELLO"
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tOFF\tNone\tHELLO\n', "text Should be Hello")

    def test_button_text_icon(self):
        test_control = Button("BUTTONID")
        test_control.send_button(ButtonState.ON, Icon.PAD, "HELLO")
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tON\tPad\tHELLO\n', "icon Should be Pad")

if __name__ == '__main__':
    unittest.main()
