import time
import unittest

from dashio import Device


class RecordingPublisher:
    """Stands in for the device's ZMQ publisher, recording what is sent."""

    def __init__(self, events, publisher):
        self.events = events
        self.publisher = publisher

    def send_multipart(self, parts):
        self.events.append(("sent", parts[1].decode()))

    def close(self):
        self.publisher.close()


class TestDeviceSetup(unittest.TestCase):
    def setUp(self):
        self.device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.events = []
        time.sleep(0.2)  # Let the device thread create its publisher.
        self.device.tx_zmq_pub = RecordingPublisher(self.events, self.device.tx_zmq_pub)

    def tearDown(self):
        self.device.close()

    def command(self, message: str) -> str:
        return self.device._on_message(message.encode())

    def test_name_request_without_callback(self):
        self.assertEqual(self.command("\tDEVICEID\tNAME\t\n"), "\tDEVICEID\tNAME\tDEVICENAME\n",
                         "An empty NAME is a request for the current name, and must be answered")

    def test_name_request_with_callback(self):
        calls = []
        self.device.set_name_callback(lambda msg: calls.append(msg) or msg[2])
        self.assertEqual(self.command("\tDEVICEID\tNAME\t\n"), "\tDEVICEID\tNAME\tDEVICENAME\n")
        self.assertEqual(calls, [], "A request for the name shouldn't call the name callback")

    def test_name_change_with_callback(self):
        self.device.set_name_callback(lambda msg: msg[2])
        self.command("\tDEVICEID\tNAME\tNew Name\n")
        self.assertEqual(self.device.device_name, "New Name")
        self.assertIn(("sent", "\tDEVICEID\tNAME\tNew Name\n"), self.events)

    def test_name_change_without_callback(self):
        self.command("\tDEVICEID\tNAME\tNew Name\n")
        self.assertEqual(self.device.device_name, "DEVICENAME", "The name can't be changed without a name callback")

    def test_name_request_after_unset(self):
        self.device.set_name_callback(lambda msg: msg[2])
        self.device.unset_name_callback()
        self.assertEqual(self.command("\tDEVICEID\tNAME\t\n"), "\tDEVICEID\tNAME\tDEVICENAME\n")
        self.assertNotIn("name", self.device._cfg["deviceSetup"].split(","))

    def test_reset_replies_before_calling_callback(self):
        self.device.set_reset_callback(lambda msg: self.events.append(("reset", msg[1])))
        self.assertIn("rst", self.device._cfg["deviceSetup"].split(","), "The device should advertise it can be reset")
        self.command("\tDEVICEID\tRST\n")
        self.assertEqual(self.events, [("sent", "\tDEVICEID\tRST\n"), ("reset", "RST")],
                         "The device must reply before resetting")

    def test_reset_without_callback(self):
        self.device.set_reset_callback(lambda msg: self.events.append(("reset", msg[1])))
        self.device.unset_reset_callback()
        self.assertNotIn("rst", self.device._cfg["deviceSetup"].split(","))
        self.command("\tDEVICEID\tRST\n")
        self.assertEqual(self.events, [], "A device without a reset callback ignores RST")

    def test_announce_and_who_reply_include_cfg_rev(self):
        self.device.config_revision = 5
        who = "\tDEVICEID\tWHO\tDEVICETYPE\tDEVICENAME\t5\n"
        self.assertEqual(self.command("\tWHO\n"), who)
        self.device._send_announce()
        self.assertIn(("sent", who), self.events, "The announce must include cfgRev, or the app takes it as 0")


if __name__ == '__main__':
    unittest.main()
