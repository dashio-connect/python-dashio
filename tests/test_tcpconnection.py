import json
import unittest

from dashio import Device, TCPConnection


class TestTCPConnection(unittest.TestCase):
    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_add_device_without_zeroconf(self):
        device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        tcp_connection = TCPConnection(port=5659, use_zero_conf=False)
        tcp_connection.add_device(device)
        self.assertIn("DEVICEID", tcp_connection.local_device_id_list)
        tcp_connection.close()
        device.close()


if __name__ == '__main__':
    unittest.main()
