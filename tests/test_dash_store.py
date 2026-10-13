import json
import os
import tempfile
import time
import unittest

import dashio
from dashio.iotcontrol.enums import ConnectionState
from dashio.dash_store import SDU_MAX_PACKET_LENGTH, DashStore, SDUSession, fnv1a_64

TS = 1760000000  # October 2025, so the stores below keep entries whatever their age (max_days=None).


def split_packet(packet):
    """Return the JSON body of an SDU UPDATE packet, checking its header and hash."""
    assert packet.startswith("\tDEV1\tDATA\tSDU\tUPDATE\t") and packet.endswith("\n"), packet
    body, packet_hash = packet[len("\tDEV1\tDATA\tSDU\tUPDATE\t"):-1].rsplit("\t", 1)
    assert packet_hash == f"{fnv1a_64(body.encode()):016x}", "The hash is FNV-1a over the JSON"
    return body


class TestDashStore(unittest.TestCase):
    def test_fnv1a_golden_vectors(self):
        self.assertEqual(f"{fnv1a_64(b''):016x}", "cbf29ce484222325")
        self.assertEqual(f"{fnv1a_64(b'a'):016x}", "af63dc4c8601ec8c")
        empty_packet = b'{"controlInfo":[],"data":[]}'
        self.assertEqual(f"{fnv1a_64(empty_packet):016x}", "e31bb7a9a23e0d6e")

    def test_entries_after_timestamp(self):
        store = DashStore(max_days=None)
        self.addCleanup(store.close)
        for offset in range(3):
            store.add("TGRPH", "TG1", "L1", TS + offset, 20 + offset)
        store.add("TGRPH", "TG1", "L2", TS, 1)
        self.assertEqual([entry.data for entry in store.entries("TGRPH", "TG1", "L1", TS)], [21, 22])
        self.assertEqual(store.sub_ids("TGRPH", "TG1"), ["L1", "L2"])

    def test_max_entries(self):
        store = DashStore(max_entries=5, max_days=None)
        self.addCleanup(store.close)
        for offset in range(8):
            store.add("TGRPH", "TG1", "L1", TS + offset, offset)
        self.assertEqual([entry.data for entry in store.entries("TGRPH", "TG1", "L1")], [3, 4, 5, 6, 7])

    def test_max_days(self):
        store = DashStore(max_days=1)
        self.addCleanup(store.close)
        store.add("LOG", "LOG1", "", time.time() - 2 * 86400, {"color": "4", "lines": ["old"]})
        store._last_age_prune = None  # As if a minute has passed, so old entries are deleted on the next add.
        store.add("LOG", "LOG1", "", time.time(), {"color": "4", "lines": ["new"]})
        self.assertEqual([entry.data["lines"] for entry in store.entries("LOG", "LOG1")], [["new"]])

    def test_kept_after_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "store.db")
            store = DashStore(path, max_days=None)
            store.add("TGRPH", "TG1", "L1", TS, 21.5)
            store.close()
            store = DashStore(path, max_days=None)
            self.assertEqual([entry.data for entry in store.entries("TGRPH", "TG1", "L1")], [21.5])
            store.close()


REGISTRY = [
    {"type": "TGRPH", "id": "TG1", "sub": "L1", "name": "Temp", "lineType": "LINE", "color": "4", "axis": "L"},
    {"type": "TGRPH", "id": "TG1", "sub": "L2", "name": "Hum", "lineType": "BAR", "color": "", "axis": "R"},
    {"type": "MAP", "id": "M1", "sub": "T1", "name": "Trip", "color": "4"},
    {"type": "LOG", "id": "LOG1", "sub": ""},
]


class TestSDUSession(unittest.TestCase):
    def setUp(self):
        self.store = DashStore(max_days=None)
        self.addCleanup(self.store.close)
        self.sent = []
        self.session = SDUSession("DEV1", self.store, lambda: REGISTRY, self.sent.append)

    def test_timestamp_request(self):
        self.assertEqual(
            self.session.timestamp_request(),
            '\tDEV1\tDATA\tSDU\tREQUEST\t{"tgrphList":[{"controlID":"TG1","lineList":["L1","L2"]}],'
            '"mapList":[{"controlID":"M1","trackList":["T1"]}],"logList":["LOG1"]}\n'
        )

    def test_no_timestamp_request_without_controls(self):
        session = SDUSession("DEV1", self.store, lambda: [], self.sent.append)
        self.assertEqual(session.timestamp_request(), "")

    def test_update_packet(self):
        self.store.add("TGRPH", "TG1", "L1", TS + 1, 23.5)
        self.store.add("TGRPH", "TG1", "L2", TS, 5)  # Not newer than the server's ts, so skipped.
        self.store.add("TGRPH", "TG1", "L2", TS + 2, [21.3, 20])
        self.store.add("TGRPH", "TG1", "L1", TS + 3, True)
        self.store.add("MAP", "M1", "T1", TS + 4, {"latitude": "-36.85", "longitude": "174.76"})
        self.store.add("LOG", "LOG1", "", TS + 5, {"color": "4", "lines": ["a \"b\"", "c"]})
        self.session.request(json.dumps({
            "tgrphList": [{"controlID": "TG1", "lineList": [{"id": "L1", "sendInfo": True}, {"id": "L2", "ts": TS}]}],
            "mapList": [{"controlID": "M1", "trackList": [{"id": "T1", "ts": TS}]}],
            "logList": [{"controlID": "LOG1", "ts": TS}],
        }))
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(split_packet(self.sent[0]), (
            '{"controlInfo":['
            '{"type":"TGRPH","id":"TG1","lineID":"L1","name":"Temp","lineType":"LINE","color":"4","axis":"L"},'
            '{"type":"TGRPH","id":"TG1","lineID":"L2"},'
            '{"type":"MAP","id":"M1","trackID":"T1"},'
            '{"type":"LOG","id":"LOG1"}],"data":['
            f'{{"idx":0,"ts":{TS + 1},"data":"23.500000"}},'
            f'{{"idx":1,"ts":{TS + 2},"data":"[21.3,20]"}},'
            f'{{"idx":0,"ts":{TS + 3},"data":"T"}},'
            f'{{"idx":2,"ts":{TS + 4},"data":{{"time":"2025-10-09T08:53:24Z","latitude":-36.850000,"longitude":174.760000}}}},'
            f'{{"idx":3,"ts":{TS + 5},"data":{{"color":"4","lines":["a \\"b\\"","c"]}}}}]}}'
        ))
        self.session.ack()
        self.assertEqual(len(self.sent), 1, "Nothing more to send")
        self.assertEqual(self.session.state, SDUSession.IDLE)

    def test_packets_split_and_short_control_info_after_first_ack(self):
        for offset in range(400):
            self.store.add("TGRPH", "TG1", "L1", TS + 1 + offset, offset + 0.5)
        self.session.request(json.dumps({"tgrphList": [{"controlID": "TG1", "lineList": [{"id": "L1", "sendInfo": True}]}]}))
        sent_ts = []
        while self.session.state != SDUSession.IDLE:
            packet = self.sent[-1]
            self.assertLessEqual(len(packet.encode()), SDU_MAX_PACKET_LENGTH)
            body = json.loads(split_packet(packet))
            self.assertEqual("name" in body["controlInfo"][0], len(self.sent) == 1, "Line details only in the first packet")
            sent_ts += [item["ts"] for item in body["data"]]
            self.session.ack()
        self.assertGreater(len(self.sent), 1)
        self.assertEqual(sent_ts, [TS + 1 + offset for offset in range(400)], "Every entry sent once, in order")

    def test_nack_retries_then_ends(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        self.session.request(json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}]}))
        self.session.nack()
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(self.sent[0], self.sent[1], "A NACK sends the same packet again")
        self.session.nack()
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(self.session.state, SDUSession.IDLE, "A second failure ends the session")

    def test_ack_timeout_retries(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        self.session.request(json.dumps({"logList": [{"controlID": "LOG1", "sendInfo": True}]}))
        self.session.poll()
        self.assertEqual(len(self.sent), 1, "No retry before the timeout")
        self.session._deadline = 0
        self.session.poll()
        self.assertEqual(len(self.sent), 2)
        self.session.ack()
        self.assertEqual(self.session.state, SDUSession.IDLE)

    def test_request_without_control_id_is_rejected(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        self.session.request(json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}], "tgrphList": [{"lineList": []}]}))
        self.assertEqual(self.sent, [])

    def test_element_without_ts_or_send_info_is_ignored(self):
        self.store.add("TGRPH", "TG1", "L1", TS + 1, 1)
        self.store.add("TGRPH", "TG1", "L2", TS + 1, 2)
        self.session.request(json.dumps({"tgrphList": [{"controlID": "TG1", "lineList": [{"id": "L1"}, {"id": "L2", "ts": TS}]}]}))
        body = json.loads(split_packet(self.sent[0]))
        self.assertEqual([item["idx"] for item in body["data"]], [1])

    def test_request_during_session_ignored(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        request = json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}]})
        self.session.request(request)
        self.session.request(request)
        self.assertEqual(len(self.sent), 1)


class TestDeviceStore(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "device.db")
        self.devices = []

    def tearDown(self):
        for device in self.devices:
            device.close()
            device.store.close()
        self.directory.cleanup()

    def make_device(self):
        device = dashio.Device("TestType", "DEV1", "Test", store=DashStore(self.path))
        self.devices.append(device)
        graph = dashio.TimeGraph("TG1")
        graph.add_line("L1", dashio.TimeGraphLine("Temp", color=dashio.Color.RED))
        device.add_control(graph)
        log = dashio.EventLog("LOG1")
        device.add_control(log)
        map_control = dashio.Map("M1")
        device.add_control(map_control)
        return device, graph, log, map_control

    def test_history_from_store_after_restart(self):
        device, graph, log, map_control = self.make_device()
        graph.line_dict["L1"].add_data_point(21.5)
        log.add_event_data(dashio.EventData("Started", dashio.Color.GREEN))
        map_control.add_location_to_track(dashio.MapLocation("-36.85", "174.76"), "T1")
        device.close()
        device.store.close()

        device, graph, log, map_control = self.make_device()
        graph_reply = device._on_message(b"\tDEV1\tTGRPH\tTG1\tDB1\t2020-01-01T00:00:00+00:00\n")
        self.assertRegex(graph_reply, r"^\tDEV1\tTGRPH\tTG1\tDB1\tL1\tTemp\tLINE\t4\tleft\t[^\t]+\+00:00,21.5\n$")
        log_reply = device._on_message(b"\tDEV1\tLOG\tLOG1\tDB1\t2020-01-01T00:00:00+00:00\n")
        self.assertIn('"lines": ["Started"]', log_reply)
        map_reply = device._on_message(b"\tDEV1\tMAP\tM1\tDB1\t2020-01-01T00:00:00+00:00\n")
        self.assertIn('\tT1\t\t4\t{"time": ', map_reply)
        self.assertIn('"latitude": "-36.85"', map_reply)

    def test_sdu_session_through_device(self):
        device, graph, log, map_control = self.make_device()
        sent = []
        device._sdu._send = sent.append
        graph.line_dict["L1"].add_data_point(21.5)
        map_control.add_location_to_track(dashio.MapLocation("-36.85", "174.76"), "T1")
        self.assertEqual(
            device._sdu.timestamp_request(),
            '\tDEV1\tDATA\tSDU\tREQUEST\t{"tgrphList":[{"controlID":"TG1","lineList":["L1"]}],'
            '"mapList":[{"controlID":"M1","trackList":["T1"]}],"logList":["LOG1"]}\n'
        )
        request = {"tgrphList": [{"controlID": "TG1", "lineList": [{"id": "L1", "sendInfo": True}]}]}
        device._on_message(f"\tDEV1\tDATA\tSDU\tREQUEST\t{json.dumps(request)}\n".encode())
        body = json.loads(split_packet(sent[0]))
        self.assertEqual(body["controlInfo"][0], {"type": "TGRPH", "id": "TG1", "lineID": "L1", "name": "Temp", "lineType": "LINE", "color": "4", "axis": "L"})
        self.assertEqual([item["data"] for item in body["data"]], ["21.500000"])
        device._on_message(b"\tDEV1\tDATA\tSDU\tACK\n")
        self.assertEqual(device._sdu.state, SDUSession.IDLE)

    def test_without_store_unchanged(self):
        device = dashio.Device("TestType", "DEV2", "Test")
        graph = dashio.TimeGraph("TG1")
        graph.add_line("L1", dashio.TimeGraphLine("Temp"))
        device.add_control(graph)
        graph.line_dict["L1"].add_data_point(1.5)
        self.assertIsNone(graph._store)
        self.assertIn(",1.5\n", device._on_message(b"\tDEV2\tTGRPH\tTG1\tDB1\t2020-01-01T00:00:00+00:00\n"))
        device.close()


class SentMessage:
    """Stands in for paho's MQTTMessageInfo."""

    def wait_for_publish(self, timeout=None):
        return True


class FakeMQTTMessage:
    def __init__(self, payload):
        self.payload = payload.encode()


class TestDashServerSync(unittest.TestCase):
    def test_sync_through_dash_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = dashio.DashConnection("USERNAME", "PASSWORD", host="localhost", batch_delay=0)
            published = []

            def publish(topic, payload, qos=0, **kwargs):
                published.append((topic, payload))
                return SentMessage()

            connection._dash_c.publish = publish
            connection.connection_state = ConnectionState.CONNECTED
            store = DashStore(os.path.join(directory, "device.db"))
            device = dashio.Device("TestType", "DEV1", "Test", store=store)
            log = dashio.EventLog("LOG1")
            device.add_control(log)
            connection.add_device(device)
            time.sleep(0.8)  # Let the device and connection threads connect.
            try:
                log.add_event_data(dashio.EventData("Stored"))
                published.clear()
                connection._send_dash_announce("DEV1")
                time.sleep(0.3)
                announces = [payload for topic, payload in published if topic == "USERNAME/DEV1/announce"]
                self.assertEqual(announces[-1], '\tDEV1\tDATA\tSDU\tREQUEST\t{"logList":["LOG1"]}\n', "Sent after the WHO")

                connection._on_message(None, None, FakeMQTTMessage('\tDEV1\tDATA\tSDU\tREQUEST\t{"logList":[{"controlID":"LOG1","sendInfo":true}]}\n'))
                time.sleep(0.3)
                updates = [payload for topic, payload in published if "\tSDU\tUPDATE\t" in payload]
                self.assertEqual([topic for topic, payload in published if "\tSDU\tUPDATE\t" in payload], ["USERNAME/DEV1/announce"], "The server handles SDU on the announce topic")
                self.assertIn('"lines":["Stored"]', split_packet(updates[0]))
                connection._on_message(None, None, FakeMQTTMessage("\tDEV1\tDATA\tSDU\tACK\n"))
                time.sleep(0.3)
                self.assertEqual(device._sdu.state, SDUSession.IDLE)
            finally:
                connection.running = False
                device.close()
                time.sleep(0.2)
                store.close()


class TestStoreSyncFinished(unittest.TestCase):
    """on_finished tells a device that only connects now and then when it can disconnect."""

    def setUp(self):
        self.store = DashStore(max_days=None)
        self.addCleanup(self.store.close)
        self.sent = []
        self.finished = []
        self.session = SDUSession("DEV1", self.store, lambda: REGISTRY, self.sent.append)
        self.session.on_finished = self.finished.append

    def test_finished_after_last_ack(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        self.assertTrue(self.session.start().startswith("\tDEV1\tDATA\tSDU\tREQUEST\t"))
        self.session.request(json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}]}))
        self.assertEqual(self.finished, [])
        self.session.ack()
        self.assertEqual(self.finished, [True])

    def test_finished_when_nothing_to_send(self):
        self.session.start()
        self.session.request(json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}]}))
        self.assertEqual(self.sent, [])
        self.assertEqual(self.finished, [True])

    def test_finished_without_stored_controls(self):
        session = SDUSession("DEV1", self.store, lambda: [], self.sent.append)
        session.on_finished = self.finished.append
        self.assertEqual(session.start(), "")
        self.assertEqual(self.finished, [True])

    def test_no_request_from_server(self):
        self.session.start()
        self.session.poll()
        self.assertEqual(self.finished, [])
        self.session._deadline = 0
        self.session.poll()
        self.assertEqual(self.finished, [False])
        self.assertEqual(self.session.state, SDUSession.IDLE)

    def test_failed_after_retry(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        self.session.start()
        self.session.request(json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}]}))
        self.session.nack()
        self.session.nack()
        self.assertEqual(self.finished, [False])

    def test_request_not_understood(self):
        self.session.start()
        self.session.request("not json")
        self.assertEqual(self.finished, [False])

    def test_reconnecting_abandons_a_running_session(self):
        self.store.add("LOG", "LOG1", "", TS + 1, {"color": "4", "lines": ["a"]})
        request = json.dumps({"logList": [{"controlID": "LOG1", "ts": TS}]})
        self.session.start()
        self.session.request(request)
        self.session.start()
        self.session.request(request)
        self.assertEqual(len(self.sent), 2, "The new connection's request starts a new session")

    def test_device_callback(self):
        device = dashio.Device("TestType", "DEV3", "Test", store=self.store)
        self.addCleanup(device.close)
        device.set_store_sync_callback(self.finished.append)
        self.assertEqual(device._sdu.on_finished, self.finished.append)
        device.unset_store_sync_callback()
        self.assertIsNone(device._sdu.on_finished)
        without_store = dashio.Device("TestType", "DEV4", "Test")
        self.addCleanup(without_store.close)
        with self.assertRaises(ValueError):
            without_store.set_store_sync_callback(self.finished.append)


if __name__ == '__main__':
    unittest.main()
