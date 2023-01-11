import json
import unittest

from dashio import DashConnection


class TestDashConnection(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_dash_connection_username(self):
        test_connection = DashConnection("USERNAME", "PASSWORD")
        self.assertEqual(test_connection.username, 'USERNAME', "username type should be USERNAME")


if __name__ == '__main__':
    unittest.main()
