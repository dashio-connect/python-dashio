import json
import unittest

from dashio import Alarm, SoundName


class TestControl(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)


if __name__ == '__main__':
    unittest.main()
