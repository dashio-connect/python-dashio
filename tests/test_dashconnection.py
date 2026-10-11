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


if __name__ == '__main__':
    unittest.main()
