import json
import unittest
from datetime import datetime

import dateutil
from dashio import EventData, EventLog
from dashio.iotcontrol.enums import Color


class TestEventLog(unittest.TestCase):
    def _get_cfg_dict(self, cfg_list: list):
        json_str = cfg_list[0].rpartition('\t')[2]
        return json.loads(json_str)

    def test_event_data(self):
        test_data = EventData("HEADER")
        test_str_list = str(test_data).split('\t')
        self.assertIsInstance(dateutil.parser.isoparse(test_str_list[0]), datetime, "Should be datetime")
        self.assertEqual(Color(int(test_str_list[1])), Color.WHITE, "Color whould be WHITE")

    def test_event_log_control_type(self):
        test_control = EventLog("EVENTLOGID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'LOG', "control type should be LOG")

    def test_event_log_control_id(self):
        test_control = EventLog("EVENTLOGID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'EVENTLOGID', "control_id type should be EVENTLOGID")


if __name__ == '__main__':
    unittest.main()
