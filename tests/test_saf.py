"""Store and forward (SaF) on the Dash server: SAF END, and the server's CFG DASH request for the layout."""
import copy
import time
import unittest

import dashio
from dashio.iotcontrol.enums import ConnectionState
from dashio.load_config import decode_cfg64


class Recorder:
    """Stands in for the device's zmq PUB socket."""

    def __init__(self):
        self.sent = []

    def send_multipart(self, parts):
        self.sent.append((parts[0], parts[1].decode()))

    def close(self):
        pass


class SentMessage:
    """Stands in for paho's MQTTMessageInfo."""

    def wait_for_publish(self, timeout=None):
        return True


class TestServerLayoutRequest(unittest.TestCase):
    def setUp(self):
        self.device = dashio.Device("TestType", "DEV1", "Test")
        self.device.add_control(dashio.Knob("KB1", "Knob"))
        self.device.tx_zmq_pub.close()
        self.device.tx_zmq_pub = Recorder()

    def tearDown(self):
        self.device.close()

    def test_cfg_dash_answered_on_announce(self):
        reply = self.device._on_message(b"\tDEV1\tCFG\tDASH\t1\n", b"DASH:abc")
        self.assertEqual(reply, "", "Nothing goes back on the data topic")
        self.assertEqual(len(self.device.tx_zmq_pub.sent), 1)
        topic, message = self.device.tx_zmq_pub.sent[0]
        self.assertEqual(topic, b"ANNOUNCE")
        self.assertTrue(message.startswith("\tDEV1\tCFG\tDASH\tC64\t"))
        self.assertTrue(message.endswith("\n"))
        layout = decode_cfg64(message.split("\t")[5].strip())
        self.assertEqual([knob["controlID"] for knob in layout["KNOB"]], ["KB1"])

    def test_cfg_dash_is_c64_after_use_cfg(self):
        self.device.use_cfg()
        self.device._on_message(b"\tDEV1\tCFG\tDASH\t1\n", b"DASH:abc")
        self.assertTrue(self.device.tx_zmq_pub.sent[0][1].startswith("\tDEV1\tCFG\tDASH\tC64\t"))

    def test_cfg_dash_sends_the_one_column_layout(self):
        one = self.device.get_generated_cfg_dict()
        three = copy.deepcopy(one)
        three["KNOB"][0]["title"] = "Tablet"
        self.device.add_cfg64(one, 1)
        self.device.add_cfg64(three, 3)
        self.device._on_message(b"\tDEV1\tCFG\tDASH\t1\n", b"DASH:abc")
        layout = decode_cfg64(self.device.tx_zmq_pub.sent[0][1].split("\t")[5].strip())
        self.assertEqual(layout["KNOB"][0]["title"], "Knob")

    def test_app_cfg_request_unchanged(self):
        reply = self.device._on_message(b"\tDEV1\tCFG\t5D8E1A2B-0000\t1\n", b"TCP:abc")
        self.assertTrue(reply.startswith("\tDEV1\tCFG\t5D8E1A2B-0000\tC64\t"))
        self.assertEqual(self.device.tx_zmq_pub.sent, [])


class TestSafEnd(unittest.TestCase):
    def setUp(self):
        self.device = dashio.Device("TestType", "DEV1", "Test")
        self.device.tx_zmq_pub.close()
        self.device.tx_zmq_pub = Recorder()
        self.device.store_and_forward = True
        self.ends = []
        self.device.set_saf_end_callback(self.ends.append)

    def tearDown(self):
        self.device.close()

    def announce(self, connection_uuid="DASH:abc"):
        self.device._local_command({"msgType": "send_announce", "deviceID": "DEV1", "connectionUUID": connection_uuid})

    def test_end_after_held_messages(self):
        knob = dashio.Knob("KB1")
        values = []
        knob.add_receive_message_callback(lambda msg: values.append((msg[3], list(self.ends))))
        self.device.add_control(knob)
        self.announce()
        reply = self.device._on_message(b"\tDEV1\tKNOB\tKB1\t20.5\n\tDEV1\tSAF\tEND\n", b"DASH:abc")
        self.assertEqual(reply, "")
        self.assertEqual(values, [("20.5", [])], "The held message is handled before END")
        self.assertEqual(self.ends, [True])

    def test_end_only_once_per_connection(self):
        self.announce()
        self.device._on_message(b"\tDEV1\tSAF\tEND\n", b"DASH:abc")
        self.device._on_message(b"\tDEV1\tSAF\tEND\n", b"DASH:abc")
        self.assertEqual(self.ends, [True])

    def test_timeout(self):
        self.device.saf_end_timeout = 0.2
        self.announce()
        time.sleep(0.5)  # The device thread checks the timeout.
        self.assertEqual(self.ends, [False])

    def test_no_wait_without_store_and_forward(self):
        self.device.store_and_forward = False
        self.device.saf_end_timeout = 0.1
        self.announce()
        time.sleep(0.3)
        self.assertEqual(self.ends, [])

    def test_no_wait_for_other_connections(self):
        self.device.saf_end_timeout = 0.1
        self.announce("TCP:abc")
        time.sleep(0.3)
        self.assertEqual(self.ends, [])

    def test_end_ignored_without_callback(self):
        self.device.unset_saf_end_callback()
        self.announce()
        self.assertEqual(self.device._on_message(b"\tDEV1\tSAF\tEND\n", b"DASH:abc"), "")


class TestDisconnectPublishesWhatsWaiting(unittest.TestCase):
    def test_reply_sent_just_before_disconnect_is_published(self):
        # Connect to localhost so the test doesn't contact the Dash server.
        connection = dashio.DashConnection("USERNAME", "PASSWORD", host="localhost", auto_connect=False)
        published = []

        def publish(topic, payload, qos=0, **kwargs):
            published.append((topic, payload))
            return SentMessage()

        connection._dash_c.publish = publish
        device = dashio.Device("TestType", "DEV1", "Test")
        connection.add_device(device)
        time.sleep(0.8)  # Let the device and connection threads connect.
        try:
            connection._planned_disconnect = False
            connection.connection_state = ConnectionState.CONNECTED
            for _ in range(20):
                device._on_message(b"\tDEV1\tCFG\tDASH\t1\n", b"DASH:abc")
            device.tx_zmq_pub.send_multipart([b"ANNOUNCE", b"\tDEV1\tCFG\tDASH\tC64\tLAST\n"])
            connection.disconnect()
            topics = [topic for topic, _ in published]
            self.assertIn("USERNAME/DEV1/announce", topics)
            self.assertTrue(any("LAST" in payload for _, payload in published), "Everything the device sent is published")
            self.assertEqual(published[-1], ("USERNAME/DEV1/data", "\tDEV1\tOFFLINE\n"), "OFFLINE comes last")
            self.assertEqual(connection.connection_state, ConnectionState.DISCONNECTED)
        finally:
            connection.close()
            device.close()


if __name__ == '__main__':
    unittest.main()
