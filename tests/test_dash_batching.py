import time
import unittest

import dashio
from dashio.iotcontrol.enums import ConnectionState


class SentMessage:
    """Stands in for paho's MQTTMessageInfo."""

    def wait_for_publish(self, timeout=None):
        return True


class TestDashBatching(unittest.TestCase):
    def setUp(self):
        self.devices = []
        self.connections = []

    def tearDown(self):
        for connection in self.connections:
            connection.running = False
        for device in self.devices:
            device.close()

    def make_connection(self, batch_delay):
        # Connect to localhost so the test doesn't contact the Dash server.
        connection = dashio.DashConnection("USERNAME", "PASSWORD", host="localhost", batch_delay=batch_delay, app_timeout=0)
        self.connections.append(connection)
        published = []

        def publish(topic, payload, qos=0):
            published.append((topic, payload, qos))
            return SentMessage()

        connection._dash_c.publish = publish
        connection.connection_state = ConnectionState.CONNECTED
        return connection, published

    def make_device(self, connection):
        device = dashio.Device("DEVICETYPE", "DEVICEID", "DEVICENAME")
        self.devices.append(device)
        connection.add_device(device)
        time.sleep(0.8)  # Let the device and connection threads connect.
        return device

    def data_publishes(self, published):
        return [(topic, payload) for topic, payload, qos in published if topic.endswith("/data") and "ONLINE" not in payload]

    def test_updates_published_together(self):
        connection, published = self.make_connection(batch_delay=0.2)
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        for value in (1, 2, 3):
            dial.dial_value = value
        time.sleep(0.5)
        data = self.data_publishes(published)
        self.assertEqual(len(data), 1, "Updates within batch_delay are published together")
        self.assertEqual(data[0][1].count("\tDIAL\tD1\t"), 3)

    def test_without_batching(self):
        connection, published = self.make_connection(batch_delay=0)
        device = self.make_device(connection)
        dial = dashio.Dial("D1")
        device.add_control(dial)
        for value in (1, 2, 3):
            dial.dial_value = value
        time.sleep(0.5)
        self.assertEqual(len(self.data_publishes(published)), 3)

    def test_alarm_published_straight_away(self):
        connection, published = self.make_connection(batch_delay=5)
        device = self.make_device(connection)
        alarm = dashio.Alarm("ALM1")
        device.add_control(alarm)
        alarm.send("Header", "Body")
        time.sleep(0.3)
        alarms = [payload for topic, payload, qos in published if topic.endswith("/alarm")]
        self.assertEqual(alarms, ["\tDEVICEID\tALM\tALM1\tHeader\tBody\n"], "Alarms aren't held back by batching")

    def test_batch_size_limit(self):
        connection, published = self.make_connection(batch_delay=5)
        line = "\tDEVICEID\tTEXT\tT1\t" + "x" * 1500 + "\n"
        for _ in range(3):
            connection._queue_publish("USERNAME/DEVICEID/data", line, 0)
        self.assertEqual(len(published), 1, "A batch is published before it would pass the size limit")
        self.assertEqual(published[0][1], line * 2)

    def test_close_publishes_pending_messages_first(self):
        connection, published = self.make_connection(batch_delay=5)
        connection._device_id_list.append("DEVICEID")
        connection._queue_publish("USERNAME/DEVICEID/data", "\tDEVICEID\tDIAL\tD1\t5\n", 0)
        connection.close()
        self.assertEqual([payload for _, payload, _ in published], ["\tDEVICEID\tDIAL\tD1\t5\n", "\tDEVICEID\tOFFLINE\n"])


if __name__ == '__main__':
    unittest.main()
