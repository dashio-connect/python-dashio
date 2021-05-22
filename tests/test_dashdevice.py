import json
import unittest

from dashio import DashDevice
from dashio.iotcontrol.enums import Color


class TestDashDevice(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_dash_device_type(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.assertEqual(test_device.device_type, 'DEVICETYPE', "device_type type should be DEVICETYPE")

    def test_dash_device_id(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.assertEqual(test_device.device_id, 'DEVICEID', "device_id type should be DEVICEID")

    def test_dash_device_name(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.assertEqual(test_device._device_name, 'DEVICENAME', "_device_name type should be DEVICENAME")

    def test_dash_device_cfg_edit_lock(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME", edit_lock=True)
        self.assertEqual(test_device._cfg['editLock'], True, "editLock type should be True")

    def test_dash_device_cfg_number_of_pages(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME",)
        self.assertEqual(test_device._cfg['numPages'], 0, "editLock type should be 0")

    def test_dash_device_cfg_name_setable(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME", name_setable=True)
        self.assertEqual(test_device._cfg['deviceSetup'], 'name', "editLock type should be name")

    def test_dash_device_cfg_wifi_setable(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME", wifi_setable=True)
        self.assertEqual(test_device._cfg['deviceSetup'], 'wifi', "editLock type should be wifi")

    def test_dash_device_cfg_dashio_setable(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME", dashio_setable=True)
        self.assertEqual(test_device._cfg['deviceSetup'], 'dashio', "editLock type should be dashio")

    def test_dash_device_cfg_tcp_setable(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME", tcp_setable=True)
        self.assertEqual(test_device._cfg['deviceSetup'], 'tcp', "editLock type should be tcp")

    def test_dash_device_cfg_mqtt_setable(self):
        test_device = DashDevice("DEVICETYPE", "DEVICEID", "DEVICENAME", mqtt_setable=True)
        self.assertEqual(test_device._cfg['deviceSetup'], 'mqtt', "editLock type should be mqtt")


if __name__ == '__main__':
    unittest.main()
