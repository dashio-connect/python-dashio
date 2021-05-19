import json
import unittest

from dashio import Page
from dashio.iotcontrol.enums import Color, Icon


def _get_cfg_dict(cfg_str):
    json_str = cfg_str.rpartition('\t')[2]
    return json.loads(json_str)


class TestPage(unittest.TestCase):

    def test_page_cfg_icon_name(self):
        test_control = Page("PAGEID", icon=Icon.RIGHT_DOUBLE)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Icon(cfg_dict['iconName']), Icon.RIGHT_DOUBLE, "CFG iconName should be RIGHT_DOUBLE")

    def test_page_cfg_page_color(self):
        test_control = Page("PAGEID", page_color=Color.BURLY_WOOD)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Color(int(cfg_dict['pageColor'])), Color.BURLY_WOOD, "CFG pageColor should be BURLY_WOOD")

    def test_page_cfg_control_title_box_color(self):
        test_control = Page("PAGEID", control_title_box_color=Color.CHOCOLATE)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Color(int(cfg_dict['ctrlTitleBoxColor'])), Color.CHOCOLATE, "CFG ctrlTitleBoxColor should be CHOCOLATE")

    def test_page_cfg_control_title_box_transparency(self):
        test_control = Page("PAGEID", control_title_box_transparency=2)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['ctrlTitleBoxTransparency'], 2, "CFG ctrlTitleBoxTransparency should be 2")

    def test_page_cfg_control_color(self):
        test_control = Page("PAGEID", control_color=Color.TOMATO)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Color(int(cfg_dict['ctrlColor'])), Color.TOMATO, "CFG ctrlColor should be TOMATO")

    def test_page_cfg_control_border_color(self):
        test_control = Page("PAGEID", control_border_color=Color.TURQUOISE)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Color(int(cfg_dict['ctrlBorderColor'])), Color.TURQUOISE, "CFG ctrlBorderColor should be TURQUOISE")

    def test_page_cfg_control_border_on(self):
        test_control = Page("PAGEID", control_border_on=True)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['ctrlBorderOn'], True, "CFG ctrlBorderColor should be True")

    def test_page_control_background_color(self):
        test_control = Page("PAGEID", control_background_color=Color.BISQUE)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(Color(int(cfg_dict['ctrlBkgndColor'])), Color.BISQUE, "CFG ctrlBkgndColor should be BISQUE")

    def test_page_cfg_control_title_font_size(self):
        test_control = Page("PAGEID", control_title_font_size=20)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['ctrlTitleFontSize'], 20, "CFG ctrlTitleFontSize should be 20")

    def test_page_cfg_control_max_font_size(self):
        test_control = Page("PAGEID", control_max_font_size=20)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['ctrlMaxFontSize'], 20, "CFG ctrlMaxFontSize should be 20")

    def test_page_cfg_control_background_transparency(self):
        test_control = Page("PAGEID", control_background_transparency=50)
        cfg_dict = _get_cfg_dict(test_control.get_cfg(1, 1))
        self.assertEqual(cfg_dict['ctrlBkgndTransparency'], 50, "CFG ctrlBkgndTransparency should be 50")

if __name__ == '__main__':
    unittest.main()
