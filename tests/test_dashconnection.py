import json
import unittest

import zmq

from dashio import DashConnection, Device, decode_cfg64
from dashio.dash_connection import DashControl


class TestDashConnection(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_dash_connection_username(self):
        # Connect to localhost so the test doesn't contact the Dash server.
        test_connection = DashConnection("USERNAME", "PASSWORD", host="localhost")
        self.assertEqual(test_connection.username, 'USERNAME', "username type should be USERNAME")
        test_connection.close()

    def test_dash_control_cfg_in_device(self):
        device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME", context=zmq.Context())
        self.assertTrue(device.add_control(DashControl("DASH1", "USERNAME", "dash.dashio.io")))
        reply = device._make_cfg64(["", "DEVICEID", "DASHID", "1"])
        device.close()
        cfg = decode_cfg64(reply.rstrip("\n").rpartition("\t")[2])
        self.assertEqual(cfg["DASHIO"], {"controlID": "DASH1", "userName": "USERNAME", "hostURL": "dash.dashio.io"})

    def test_will_is_offline_for_first_device(self):
        # Connect to localhost so the test doesn't contact the Dash server.
        test_connection = DashConnection("USERNAME", "PASSWORD", host="localhost", offline_delay=7)
        first = Device("DEVICETYPE", "DEVICEID1", "DEVICENAME", context=zmq.Context())
        second = Device("DEVICETYPE", "DEVICEID2", "DEVICENAME", context=zmq.Context())
        test_connection.add_device(first)
        test_connection.add_device(second)
        test_connection._set_will()
        client = test_connection._dash_c
        self.assertEqual(client._will_topic, b"USERNAME/DEVICEID1/data", "The will should be on the first device's data topic")
        self.assertEqual(client._will_payload, b"\tDEVICEID1\tOFFLINE\n")
        self.assertEqual((client._will_qos, client._will_retain), (1, False))
        self.assertEqual(client._will_properties.WillDelayInterval, 7)
        test_connection.close()
        first.close()
        second.close()

    def test_no_will_without_devices(self):
        test_connection = DashConnection("USERNAME", "PASSWORD", host="localhost")
        test_connection._set_will()
        self.assertFalse(test_connection._dash_c._will, "There should be no will without a device")
        test_connection.close()

    def test_offline_delay_zero_has_no_will_delay(self):
        test_connection = DashConnection("USERNAME", "PASSWORD", host="localhost", offline_delay=0)
        device = Device("DEVICETYPE", "DEVICEID1", "DEVICENAME", context=zmq.Context())
        test_connection.add_device(device)
        test_connection._set_will()
        self.assertIsNone(test_connection._dash_c._will_properties, "offline_delay=0 should publish the will straight away")
        test_connection.close()
        device.close()


if __name__ == '__main__':
    unittest.main()
