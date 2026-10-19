import time
import unittest

import dashio
from dashio.iotcontrol.enums import ConnectionState


class SentMessage:
    """Stands in for paho's MQTTMessageInfo."""

    def wait_for_publish(self, timeout=None):
        return True


class ReceivedMessage:
    """Stands in for paho's MQTTMessage."""

    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload.encode()


class TestDashAppActive(unittest.TestCase):
    """Control updates are only published to the Dash server while a Dash app is watching the device."""

    def setUp(self):
        self.devices = []
        self.connections = []

    def tearDown(self):
        for connection in self.connections:
            connection.running = False
        for device in self.devices:
            device.close()

    def make_connection(self, app_timeout=120):
        # Connect to localhost so the test doesn't contact the Dash server.
        connection = dashio.DashConnection("USERNAME", "PASSWORD", host="localhost", batch_delay=0, app_timeout=app_timeout)
        self.connections.append(connection)
        published = []

        def publish(topic, payload, qos=0):
            published.append((topic, payload))
            return SentMessage()

        connection._dash_c.publish = publish
        connection.connection_state = ConnectionState.CONNECTED
        return connection, published

    def make_device(self, connection, device_id="DEVICEID"):
        device = dashio.Device("DEVICETYPE", device_id, "DEVICENAME")
        self.devices.append(device)
        connection.add_device(device)
        time.sleep(0.8)  # Let the device and connection threads connect.
        return device

    def receive(self, connection, topic, payload):
        connection._on_message(None, None, ReceivedMessage(topic, payload))
        time.sleep(0.3)

    def dials(self, published):
        return [payload for topic, payload in published if "\tDIAL\t" in payload]

    def test_no_updates_without_an_app(self):
        connection, published = self.make_connection()
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        dial.dial_value = 1
        time.sleep(0.3)
        self.assertEqual(self.dials(published), [])
        self.assertFalse(connection.app_active("DEVICEID"))

    def test_connect_starts_updates(self):
        connection, published = self.make_connection()
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        self.receive(connection, "USERNAME/DEVICEID/control", "\tDEVICEID\tCONNECT\n")
        self.assertTrue(connection.app_active("DEVICEID"))
        dial.dial_value = 2
        time.sleep(0.3)
        self.assertEqual(self.dials(published), ["\tDEVICEID\tDIAL\tD1\t2\n"])

    def test_who_starts_updates(self):
        connection, published = self.make_connection()
        self.make_device(connection)
        self.receive(connection, "USERNAME/DEVICEID/control", "\tWHO\n")
        self.assertTrue(connection.app_active("DEVICEID"))

    def test_per_device(self):
        connection, published = self.make_connection()
        device1 = self.make_device(connection, "DEV1")
        device2 = self.make_device(connection, "DEV2")
        dial1 = dashio.Dial("D1")
        device1.add_control(dial1)
        dial2 = dashio.Dial("D2")
        device2.add_control(dial2)
        self.receive(connection, "USERNAME/DEV1/control", "\tDEV1\tCONNECT\n")
        dial1.dial_value = 1
        dial2.dial_value = 2
        time.sleep(0.3)
        self.assertEqual(self.dials(published), ["\tDEV1\tDIAL\tD1\t1\n"])

    def test_other_devices_data_doesnt_count(self):
        connection, published = self.make_connection()
        self.make_device(connection)
        self.receive(connection, "USERNAME/OTHER/data", "\tOTHER\tCONNECT\n")
        self.receive(connection, "USERNAME/DEVICEID/data", "\tDEVICEID\tCONNECT\n")
        self.assertFalse(connection.app_active("DEVICEID"))
        self.assertFalse(connection.app_active("OTHER"))

    def test_app_times_out(self):
        connection, published = self.make_connection(app_timeout=0.5)
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        self.receive(connection, "USERNAME/DEVICEID/control", "\tDEVICEID\tCONNECT\n")
        time.sleep(0.5)
        self.assertFalse(connection.app_active("DEVICEID"))
        self.assertEqual(connection._app_seen, {}, "Expired by the connection's thread")
        dial.dial_value = 3
        time.sleep(0.3)
        self.assertEqual(self.dials(published), [])

    def test_disconnect_resets(self):
        connection, published = self.make_connection()
        self.make_device(connection)
        self.receive(connection, "USERNAME/DEVICEID/control", "\tDEVICEID\tCONNECT\n")
        connection._on_disconnect(None, None, None, None, None)
        self.assertFalse(connection.app_active("DEVICEID"))

    def test_timeout_zero_always_publishes(self):
        connection, published = self.make_connection(app_timeout=0)
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        dial.dial_value = 4
        time.sleep(0.3)
        self.assertEqual(self.dials(published), ["\tDEVICEID\tDIAL\tD1\t4\n"])
        self.assertTrue(connection.app_active("DEVICEID"))

    def test_replies_alarms_and_time_graphs_still_published(self):
        connection, published = self.make_connection()
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        alarm = dashio.Alarm("ALM1")
        device.add_control(alarm)
        graph = dashio.TimeGraph("TG1")
        graph.add_line("L1", dashio.TimeGraphLine("Temp"))
        device.add_control(graph)
        self.receive(connection, "USERNAME/DEVICEID/control", "\tDEVICEID\tSTATUS\n")
        self.assertFalse(connection.app_active("DEVICEID"), "STATUS doesn't count as watching")
        self.assertTrue(any("\tPKG\t" in payload and "DIAL\\tD1" in payload for topic, payload in published), "The STATUS reply is published")
        alarm.send("Header", "Body")
        graph.line_dict["L1"].add_data_point(21.5)
        graph.send_data()
        time.sleep(0.3)
        self.assertIn(("USERNAME/DEVICEID/alarm", "\tDEVICEID\tALM\tALM1\tHeader\tBody\n"), published)
        self.assertTrue(any(topic.endswith("/data") and "\tTGRPH\tTG1\tL1\t" in payload for topic, payload in published))


if __name__ == '__main__':
    unittest.main()
