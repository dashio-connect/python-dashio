import json
import unittest

from dashio import TCPConnection
from dashio.iotcontrol.enums import Color


class TestTCPConnection(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_TCP_connection_username(self):
        test_connection = TCPConnection()
        test_cfg = self._get_cfg_dict(test_connection.tcp_control.get_cfg(["DEVICEID", "CONTROLID", "DASHID", 1]))
        self.assertEqual(test_cfg['ipAddress'], '', "ipAddress should be ''")



if __name__ == '__main__':
    unittest.main()
