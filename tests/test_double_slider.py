import unittest
from dashio import SliderDoubleBar


class TestSliderDoubleBar(unittest.TestCase):

    def test_slider_single_bar_control_type(self):
        test_control = SliderDoubleBar("SLIDERID")
        test_str_list = test_control._state_str.split('\t')
        self.assertEqual(test_str_list[2], 'SLDR', "control type should be SLCTR")

    def test_slider_single_bar_control_id(self):
        test_control = SliderDoubleBar("SLIDERID")
        test_str_list = test_control._state_str.split('\t')
        self.assertEqual(test_str_list[3], 'SLIDERID', "control type should be SLIDERID")


if __name__ == '__main__':
    unittest.main()
