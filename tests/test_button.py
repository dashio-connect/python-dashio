import json
import unittest

from dashio import Button, ButtonState, Icon


class TestButton(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_button_state_on(self):
        test_control = Button("BUTTONID")
        test_control.btn_state = ButtonState.ON
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tON\n', "Should be 'ON'")

    def test_button_state_off(self):
        test_control = Button("BUTTONID")
        test_control.btn_state = ButtonState.OFF
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tOFF\n', "Should be 'OFF'")
    """
    def test_button_state_flash(self):
        test_control = Button("BUTTONID")
        test_control.btn_state = ButtonState.FLASH
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tFLASH\n', "Should be 'FLASH'")
    """
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
        test_control.send_button(ButtonState.ON, Icon.SQUARE, "HELLO")
        self.assertEqual(test_control.get_state(), '\t{device_id}\tBTTN\tBUTTONID\tON\tSquare\tHELLO\n', "icon Should be Square")


if __name__ == '__main__':
    unittest.main()
