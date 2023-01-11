import json
import unittest


class TestMQTTConnection(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)


if __name__ == '__main__':
    unittest.main()
