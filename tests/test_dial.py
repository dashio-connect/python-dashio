import json
import unittest

from dashio import Color, Dial, DialNumberPosition, DialStyle, Precision


class TestDial(unittest.TestCase):

    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_dial(self):
        test_control = Dial("DIALID")
        test_control.dial_value = 1
        self.assertEqual(test_control.get_state(), '\t{device_id}\tDIAL\tDIALID\t1\n', "Should be 1")

    def test_dial_min(self):
        test_control = Dial("DIALID", dial_min=1)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['min'], 1, "CFG min should be 1")

    def test_dial_max(self):
        test_control = Dial("DIALID", dial_max=1)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['max'], 1, "CFG min should be 1")

    def test_dial_red_value(self):
        test_control = Dial("DIALID", red_value=50)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['redValue'], 50, "CFG redValue should be 50")

    def test_dial_show_min_max(self):
        test_control = Dial("DIALID", show_min_max=True)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['showMinMax'], True, "CFG showMinMax should be True")

    def test_dial_dial_fill_color(self):
        test_control = Dial("DIALID", dial_fill_color=Color.WHEAT)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['dialFillColor'], '110', "CFG dialFillColor should be '110'")

    def test_dial_pointer_color(self):
        test_control = Dial("DIALID", pointer_color=Color.AZURE)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['pointerColor'], '136', "CFG pointerColor should be '136'")

    def test_dial_number_position(self):
        test_control = Dial("DIALID", number_position=DialNumberPosition.LEFT)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['numberPosition'], 'left', "CFG numberPosition should be 'left'")

    def test_dial_style(self):
        test_control = Dial("DIALID", style=DialStyle.BAR)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['style'], 'bar', "CFG style should be 'bar'")

    def test_dial_precision(self):
        test_control = Dial("DIALID", precision=Precision.FIVE)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['precision'], 5, "CFG precision should be 5")

    def test_dial_units(self):
        test_control = Dial("DIALID", units='Watts')
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['units'], 'Watts', "CFG units should be 'Watts'")


if __name__ == '__main__':
    unittest.main()
