import json
import unittest
from datetime import datetime

import dateutil
from dashio import EventData, EventLog
from dashio.iotcontrol.enums import Color


class TestEventLog(unittest.TestCase):
    def _get_cfg_dict(self, cfg_str):
        json_str = cfg_str.rpartition('\t')[2]
        return json.loads(json_str)

    def test_event_data(self):
        test_data = EventData("HEADER", "BODY")
        test_str_list = test_data.to_string().split('\t')
        self.assertIsInstance(dateutil.parser.isoparse(test_str_list[0]), datetime, "Should be datetime")
        self.assertEqual(Color(int(test_str_list[1])), Color.WHITE, "Color whould be WHITE")
        self.assertEqual(test_str_list[2], 'HEADER', "header should be 'HEADER'")
        self.assertEqual(test_str_list[3], 'BODY\n', "body should be 'BODY\n'")
        self.assertEqual(len(test_str_list), 4, "should be 4 elements")

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
