import json
import unittest

from dashio import Direction
from dashio.iotcontrol.enums import Color, DirectionStyle, Precision


class TestDial(unittest.TestCase):

    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_direction_direction_value(self):
        test_control = Direction("DIRECTIONID")
        test_control.direction_value = 1
        self.assertEqual(test_control.get_state(), '\t{device_id}\tDIR\tDIRECTIONID\t1\n', "Should be 1")

    def test_direction_direction_text(self):
        test_control = Direction("DIRECTIONID")
        test_control.direction_text = 'THAT WAY'
        self.assertEqual(test_control.get_state(), '\t{device_id}\tDIR\tDIRECTIONID\t0\tTHAT WAY\n', "Should be 1")

    def test_direction_pointer_color(self):
        test_control = Direction("DIRECTIONID", pointer_color=Color.BLUE)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['pointerColor'], '18', "CFG pointerColor should be '18'")

    def test_direction_calibration_angle(self):
        test_control = Direction("DIRECTIONID", calibration_angle=1.2)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['calAngle'], 1.2, "CFG calAngle should be 1.2")

    def test_direction_style(self):
        test_control = Direction("DIRECTIONID", style=DirectionStyle.NSEW)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['style'], 'nsew', "CFG style should be 'nsew'")

    def test_direction_units(self):
        test_control = Direction("DIRECTIONID", units='Volts')
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['units'], 'Volts', "CFG units should be 'Volts'")

    def test_direction_precision(self):
        test_control = Direction("DIRECTIONID", precision=Precision.FIVE)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(cfg_dict['precision'], 5, "CFG precision should be 5")


if __name__ == '__main__':
    unittest.main()
