import json
import unittest


class TestTCPConnection(unittest.TestCase):
    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)


if __name__ == '__main__':
    unittest.main()
