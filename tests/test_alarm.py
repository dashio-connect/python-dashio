import json
import unittest

from dashio import Alarm, SoundName


class TestControl(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_alarm_description(self):
        test_control = Alarm("ALARMID", description="DESCRIPTION")
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['description'], "DESCRIPTION", "CFG description Should be DESCRIPTION")

    def test_alarm_soundName(self):
        test_control = Alarm("ALARMID", sound_name=SoundName.BELL)
        cfg_dict = self._get_cfg_dict(test_control.get_cfg(1,1))
        self.assertEqual(cfg_dict['soundName'], "Bell", "CFG soundName Should be Bell")


if __name__ == '__main__':
    unittest.main()
