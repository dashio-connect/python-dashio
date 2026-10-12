import socket
import threading
import time
import unittest

from dashio import DashConnection
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


if __name__ == '__main__':
    unittest.main()
