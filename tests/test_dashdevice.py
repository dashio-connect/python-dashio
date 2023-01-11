import json
import unittest

from dashio import Device


class TestDashDevice(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_dash_device_type(self):
        test_device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.assertEqual(test_device.device_type, 'DEVICETYPE', "device_type type should be DEVICETYPE")

    def test_dash_device_id(self):
        test_device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.assertEqual(test_device.device_id, 'DEVICEID', "device_id type should be DEVICEID")

    def test_dash_device_name(self):
        test_device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.assertEqual(test_device._device_name, 'DEVICENAME', "_device_name type should be DEVICENAME")

    def test_dash_device_cfg_number_of_controls_boxes(self):
        test_device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME",)
        self.assertEqual(test_device._cfg['numDeviceViews'], 0, "editLock type should be 0")


if __name__ == '__main__':
    unittest.main()
