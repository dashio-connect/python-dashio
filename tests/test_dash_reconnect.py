import socket
import threading
import time
import unittest

from dashio import ControlName, DashConnection, Device, Dial, TimeGraph
from dashio.iotcontrol.enums import ConnectionState


class RefusingServer(threading.Thread):
    """A fake MQTT v5 server that refuses every login with "Bad user name or password"."""

    def __init__(self):
        super().__init__(daemon=True)
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen()
        self.server.settimeout(0.2)
        self.port = self.server.getsockname()[1]
        self.attempts = []
        self.running = True
        self.start()

    def run(self):
        while self.running:
            try:
                client, _ = self.server.accept()
            except socket.timeout:
                continue
            self.attempts.append(time.monotonic())
            client.settimeout(1)
            try:
                client.recv(1024)  # CONNECT
                client.sendall(bytes([0x20, 0x03, 0x00, 0x86, 0x00]))  # CONNACK, reason 0x86
            except OSError:
                pass
            client.close()

    def stop(self):
        self.running = False
        self.join()
        self.server.close()


class TestDashReconnect(unittest.TestCase):
    def setUp(self):
        self.server = RefusingServer()
        self.connections = []

    def tearDown(self):
        for connection in self.connections:
            connection.close()
            connection.join(timeout=5)
        self.server.stop()

    def make_connection(self, username, password):
        connection = DashConnection(username, password, host="127.0.0.1", port=self.server.port, use_ssl=False)
        connection._dash_c.reconnect_delay_set(0.2, 10)
        self.connections.append(connection)
        return connection

    def test_backs_off_after_refused_logins(self):
        self.make_connection("USERNAME", "PASSWORD")
        time.sleep(4)
        attempts = self.server.attempts
        self.assertGreaterEqual(len(attempts), 3)
        waits = [later - earlier for earlier, later in zip(attempts, attempts[1:])]
        for earlier, later in zip(waits, waits[1:]):
            self.assertGreater(later, earlier * 1.5, f"Each wait should be about twice the last: {waits}")

    def test_no_connection_without_credentials(self):
        connection = self.make_connection("", "")
        time.sleep(1.5)
        self.assertEqual(self.server.attempts, [])
        self.assertEqual(connection.connection_state, ConnectionState.DISCONNECTED)

    def test_set_connection_connects(self):
        connection = self.make_connection("", "")
        time.sleep(1.2)
        connection.set_connection("USERNAME", "PASSWORD")
        time.sleep(0.5)
        self.assertTrue(self.server.attempts, "Connects once the credentials are set")


class TestPlannedDisconnect(unittest.TestCase):
    """auto_connect=False, connect() and disconnect(), for devices that only connect now and then."""

    def setUp(self):
        self.server = RefusingServer()
        self.connection = DashConnection("USERNAME", "PASSWORD", host="127.0.0.1", port=self.server.port, use_ssl=False, auto_connect=False)
        self.connection._dash_c.reconnect_delay_set(0.2, 10)

    def tearDown(self):
        self.connection.close()
        self.connection.join(timeout=5)
        self.server.stop()

    def test_connects_only_when_asked(self):
        time.sleep(1.5)
        self.assertEqual(self.server.attempts, [], "auto_connect=False waits for connect()")
        self.connection.connect()
        time.sleep(0.5)
        self.assertTrue(self.server.attempts)
        self.connection.disconnect()
        attempts = len(self.server.attempts)
        time.sleep(1.5)
        self.assertEqual(len(self.server.attempts), attempts, "No attempts after disconnect()")
        self.assertEqual(self.connection.connection_state, ConnectionState.DISCONNECTED)

    def test_messages_dropped_while_disconnected(self):
        published = []
        self.connection._dash_c.publish = lambda topic, payload, qos=0, **kwargs: published.append(payload)
        device = Device("TestType", "DEV1", "Test")
        dial = Dial("D1")
        device.add_control(dial)
        self.connection.add_device(device)
        time.sleep(0.8)  # Let the device and connection threads connect.
        try:
            dial.dial_value = 5
            time.sleep(0.3)
            # As if connected: a backlog from while disconnected would be published now.
            self.connection._planned_disconnect = False
            self.connection.connection_state = ConnectionState.CONNECTED
            time.sleep(0.3)
            self.assertEqual([payload for payload in published if "DIAL" in payload], [])
            dial.dial_value = 6
            time.sleep(0.3)
            self.assertEqual([payload for payload in published if "DIAL" in payload], ["\tDEV1\tDIAL\tD1\t6\n"])
        finally:
            self.connection.connection_state = ConnectionState.DISCONNECTED
            device.close()

    def test_requests_to_the_server_kept_while_disconnected(self):
        published = []
        self.connection._dash_c.publish = lambda topic, payload, qos=0, **kwargs: published.append((topic, payload))
        device = Device("TestType", "DEV1", "Test")
        graph = TimeGraph("TG1")
        device.add_control(graph)
        self.connection.add_device(device)
        time.sleep(0.8)  # Let the device and connection threads connect.
        try:
            device.storage_enable(ControlName.TGRPH, "TG1")
            time.sleep(0.3)
            self.connection._planned_disconnect = False
            self.connection.connection_state = ConnectionState.CONNECTED
            time.sleep(0.3)
            self.assertEqual(published, [("USERNAME/DEV1/announce", "\tDEV1\tSTE\tTGRPH\tTG1\n")], "STE is sent once connected")
        finally:
            self.connection.connection_state = ConnectionState.DISCONNECTED
            device.close()


if __name__ == '__main__':
    unittest.main()
