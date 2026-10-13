import datetime
import json
import time
import unittest

import dashio
from dashio.iotcontrol.event import Event


def since(hours: float) -> str:
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)).isoformat()


class TestEvent(unittest.TestCase):
    def test_fire_joins_string_replies(self):
        event = Event()
        event += lambda msg: "a\n"
        event += lambda msg: None
        event += lambda msg: True
        self.assertEqual(event("msg"), "a\n", "String replies are returned and other return values ignored")

    def test_fire_without_replies(self):
        event = Event()
        event += lambda msg: None
        self.assertEqual(event("msg"), "")


class TestHistoryReplies(unittest.TestCase):
    def setUp(self):
        self.device = dashio.Device("DEVICETYPE", "DEVICEID", "DEVICENAME")

    def tearDown(self):
        self.device.close()

    def request(self, ctrl_type: str, control_id: str, from_time: str) -> str:
        return self.device._on_message(f"\tDEVICEID\t{ctrl_type}\t{control_id}\tDASHID\t{from_time}\n".encode())

    def test_event_log_history(self):
        log = dashio.EventLog("LOG1")
        self.device.add_control(log)
        log.log.append(dashio.EventData("Something happened"))
        reply = self.request("LOG", "LOG1", since(1))
        fields = reply.rstrip("\n").split("\t")
        self.assertEqual(fields[1:5], ["DEVICEID", "LOG", "LOG1", "DASHID"])
        self.assertEqual(json.loads(fields[5])["lines"], ["Something happened"])
        self.assertTrue(reply.endswith("\n"))

    def test_event_log_history_empty(self):
        log = dashio.EventLog("LOG1")
        self.device.add_control(log)
        log.log.append(dashio.EventData("Something happened"))
        self.assertEqual(self.request("LOG", "LOG1", since(-1)), "", "No reply when there are no events after the time")

    def test_time_graph_history(self):
        graph = dashio.TimeGraph("TG1")
        graph.add_line("L1", dashio.TimeGraphLine("Line 1"))
        self.device.add_control(graph)
        graph.line_dict["L1"].add_data_point(1.5)
        reply = self.request("TGRPH", "TG1", since(1))
        fields = reply.rstrip("\n").split("\t")
        self.assertEqual(fields[1:6], ["DEVICEID", "TGRPH", "TG1", "DASHID", "L1"])
        self.assertTrue(fields[-1].endswith(",1.5"))

    def test_map_history(self):
        a_map = dashio.Map("MAP1")
        self.device.add_control(a_map)
        a_map.add_location_to_track(dashio.MapLocation("-45.0", "168.0"), "T1")
        reply = self.request("MAP", "MAP1", since(1))
        fields = reply.rstrip("\n").split("\t")
        self.assertEqual(fields[1:6], ["DEVICEID", "MAP", "MAP1", "DASHID", "T1"], "The track should keep its track_id")
        self.assertEqual(json.loads(fields[-1])["latitude"], "-45.0")

    def test_map_history_bad_time(self):
        a_map = dashio.Map("MAP1")
        self.device.add_control(a_map)
        a_map.add_location_to_track(dashio.MapLocation("-45.0", "168.0"), "T1")
        self.assertEqual(self.request("MAP", "MAP1", "not a time"), "")

    def test_receive_callback_reply(self):
        log = dashio.EventLog("LOG1")
        self.device.add_control(log)
        log.add_receive_message_callback(lambda msg: f"\t{{device_id}}\tLOG\tLOG1\t{msg[3]}\t{{\"time\": \"x\"}}\n")
        reply = self.request("LOG", "LOG1", since(1))
        self.assertEqual(reply, "\tDEVICEID\tLOG\tLOG1\tDASHID\t{\"time\": \"x\"}\n", "A receive callback's reply should be sent")


class TestServerStoredHistory(unittest.TestCase):
    """The Dash server is the app's source of truth for the history of controls with storage_enable()."""

    def setUp(self):
        self.device = dashio.Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.graph = dashio.TimeGraph("TG1")
        self.graph.add_line("L1", dashio.TimeGraphLine("Line 1"))
        self.device.add_control(self.graph)
        self.graph.line_dict["L1"].add_data_point(1.5)
        time.sleep(0.2)  # storage_enable() sends STE on the device thread's socket.

    def tearDown(self):
        self.device.close()

    def request(self, msg_from: bytes) -> str:
        return self.device._on_message(f"\tDEVICEID\tTGRPH\tTG1\tDASHID\t{since(1)}\n".encode(), msg_from)

    def test_not_answered_over_local_connections(self):
        self.device.storage_enable(dashio.ControlName.TGRPH, "TG1")
        self.assertEqual(self.request(b"TCP:abc"), "", "The app should get the history from the Dash server")
        self.assertEqual(self.request(b"ZMQ:abc"), "")

    def test_answered_for_the_dash_server(self):
        self.device.storage_enable(dashio.ControlName.TGRPH, "TG1")
        self.assertIn(",1.5\n", self.request(b"DASH:abc"))

    def test_answered_over_local_connections_without_server_storage(self):
        self.assertIn(",1.5\n", self.request(b"TCP:abc"))


if __name__ == '__main__':
    unittest.main()
