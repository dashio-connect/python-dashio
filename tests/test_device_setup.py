import time
import unittest

from dashio import DashConnection, Device, TCPConnection


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
        self.assertNotIn("NAME", self.device._cfg["deviceSetup"].split(","))

    def test_reset_replies_before_calling_callback(self):
        self.device.set_reset_callback(lambda msg: self.events.append(("reset", msg[1])))
        self.assertIn("RST", self.device._cfg["deviceSetup"].split(","), "The device should advertise it can be reset")
        self.command("\tDEVICEID\tRST\n")
        self.assertEqual(self.events, [("sent", "\tDEVICEID\tRST\n"), ("reset", "RST")],
                         "The device must reply before resetting")

    def test_reset_without_callback(self):
        self.device.set_reset_callback(lambda msg: self.events.append(("reset", msg[1])))
        self.device.unset_reset_callback()
        self.assertNotIn("RST", self.device._cfg["deviceSetup"].split(","))
        self.command("\tDEVICEID\tRST\n")
        self.assertEqual(self.events, [], "A device without a reset callback ignores RST")

    def test_announce_and_who_reply_include_cfg_rev(self):
        self.device.config_revision = 5
        who = "\tDEVICEID\tWHO\tDEVICETYPE\tDEVICENAME\t5\n"
        self.assertEqual(self.command("\tWHO\n"), who)
        self.device._send_announce()
        self.assertIn(("sent", who), self.events, "The announce must include cfgRev, or the app takes it as 0")


class TestDeviceSetupConnections(unittest.TestCase):
    """CFG deviceSetup lists the device's connections, then the settings the Dash app can change."""

    def setUp(self):
        self.device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.connections = []

    def tearDown(self):
        for connection in self.connections:
            connection.close()
        self.device.close()

    def test_connections_and_settings(self):
        tcp = TCPConnection(port=5663, use_zero_conf=False)
        dash = DashConnection("USERNAME", "PASSWORD", host="localhost", auto_connect=False)
        self.connections += [tcp, dash]
        self.device.set_name_callback(lambda msg: msg[2])
        tcp.add_device(self.device)
        dash.add_device(self.device)
        self.device.set_dashio_callback(lambda msg: True)
        self.assertEqual(self.device._cfg["deviceSetup"], "TCP,MQTT,NAME,DASH")
        self.assertIn("DASHIO", self.device._device_commands_dict, "DASH still handles the DASHIO message")

    def test_removing_a_connection(self):
        tcp = TCPConnection(port=5664, use_zero_conf=False)
        self.connections.append(tcp)
        tcp.add_device(self.device)
        self.assertEqual(self.device._cfg["deviceSetup"], "TCP")
        self.device.de_register_connection(tcp)
        self.assertEqual(self.device._cfg["deviceSetup"], "")

    def test_store_and_forward(self):
        self.device.store_and_forward = True
        self.assertTrue(self.device.store_and_forward)
        self.assertEqual(self.device._cfg["deviceSetup"], "SAF", "The Dash app can then turn SAF on and off on the server")
        self.device.store_and_forward = False
        self.assertEqual(self.device._cfg["deviceSetup"], "")

    def test_changes_the_cfg_hash(self):
        cfg_hash = self.device.get_cfg_hash()
        tcp = TCPConnection(port=5665, use_zero_conf=False)
        self.connections.append(tcp)
        tcp.add_device(self.device)
        self.assertNotEqual(self.device.get_cfg_hash(), cfg_hash, "Adding a connection changes the CFG, so cfgRev must change")


if __name__ == '__main__':
    unittest.main()
