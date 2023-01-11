import json
import unittest

from dashio import Slider
from dashio.iotcontrol.enums import Color, SliderBarStyle


def _get_cfg_dict(cfg_list: list):
    json_str = cfg_list[0].rpartition('\t')[2]
    return json.loads(json_str)


class TestSlider(unittest.TestCase):

    def test_slider_single_bar_control_type(self):
        test_control = Slider("SLIDERID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'SLDR', "control type should be SLCTR")

    def test_slider_single_bar_control_id(self):
        test_control = Slider("SLIDERID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'SLIDERID', "control type should be SLIDERID")

    def test_slider_single_bar_cfg_min(self):
        test_control = Slider("SLIDERID", bar_min=10)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['min'], 10, "CFG min should be 10")

    def test_slider_single_bar_cfg_max(self):
        test_control = Slider("SLIDERID", bar_max=10)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['max'], 10, "CFG max should be 10")

    def test_slider_single_bar_cfg_red_value(self):
        test_control = Slider("SLIDERID", red_value=10)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['redValue'], 10, "CFG redValue should be 10")

    def test_slider_single_bar_cfg_show_min_max(self):
        test_control = Slider("SLIDERID", show_min_max=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['showMinMax'], True, "CFG showMinMax should be 10")

    def test_slider_single_bar_cfg_slider_enabled(self):
        test_control = Slider("SLIDERID", slider_enabled=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['sliderEnabled'], True, "CFG sliderEnabled should be True")

    def test_slider_single_bar_cfg_send_only_on_release(self):
        test_control = Slider("SLIDERID", send_only_on_release=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['sendOnlyOnRelease'], True, "CFG sendOnlyOnRelease should be True")

    def test_slider_single_bar_cfg_bar_follows_slider(self):
        test_control = Slider("SLIDERID", bar_follows_slider=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['barFollowsSlider'], True, "CFG barFollowsSlider should be True")

    def test_slider_single_bar_cfg_bar_color(self):
        test_control = Slider("SLIDERID", bar_color=Color.CHARTREUSE)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Color(int(cfg_dict['barColor'])), Color.CHARTREUSE, "CFG barColor should be True")

    def test_slider_single_bar_cfg_bar_style(self):
        test_control = Slider("SLIDERID", bar_style=SliderBarStyle.SEG)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(SliderBarStyle(cfg_dict['barStyle']), SliderBarStyle.SEG, "CFG barStyle should be SEGMENTED")

    def test_slider_single_bar_cfg_knob_color(self):
        test_control = Slider("SLIDERID", knob_color=Color.CORAL)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(Color(int(cfg_dict['knobColor'])), Color.CORAL, "CFG barStyle should be CORAL")


if __name__ == '__main__':
    unittest.main()
