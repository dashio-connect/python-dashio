import asyncio
import datetime
import os
import socket
import sys
import tempfile
import time
import unittest
from unittest import mock

import shortuuid

import dashio
from dashio import ble_connection
from dashio.ble_connection import BLEConnection, BLEError, BlueZBackend, advertised_name, gatt_client_disabled


class FakeBlueZ(BlueZBackend):
    """Stands in for BlueZ, recording what the connection asks of it."""

    def __init__(self, connected_unpaired=None, register_error=None):
        self.connection = None
        self.adapter = "unset"
        self.registered = []
        self.unregistered = 0
        self.disconnected = []
        self.closed = False
        self._connected_unpaired = connected_unpaired or []
        self._register_error = register_error

    async def start(self, connection, adapter):
        self.connection = connection
        self.adapter = adapter

    async def register(self, local_name):
        if self._register_error:
            raise BLEError(self._register_error)
        self.registered.append(local_name)

    async def unregister(self):
        self.unregistered += 1

    async def disconnect(self, phone):
        self.disconnected.append(phone)

    async def connected_unpaired(self):
        return self._connected_unpaired

    async def close(self):
        self.closed = True


class FakePhone:
    """A phone, as BlueZ shows it to the connection: an AcquireNotify socket, and writes to the characteristic."""

    def __init__(self, connection: BLEConnection, name: str = "dev_AA_BB", mtu: int = 23, subscribe: bool = True):
        self.connection = connection
        self.path = "/org/bluez/hci0/" + name
        self.mtu = mtu
        theirs, ours = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.socket = theirs
        self.socket.settimeout(2)
        if subscribe:
            self._on_loop(connection._phone_subscribed, self.path, ours, mtu)
        else:
            ours.close()

    def _on_loop(self, function, *args):
        async def call():
            function(*args)
        asyncio.run_coroutine_threadsafe(call(), self.connection._loop).result(2)

    def write(self, data: bytes):
        self._on_loop(self.connection._phone_wrote, self.path, data)

    def receive(self, until: bytes = b"\n", timeout: float = 2) -> tuple[bytes, list[bytes]]:
        """Notifications until one ends with until: the joined data, and the notifications."""
        chunks = []
        deadline = time.monotonic() + timeout
        while not chunks or not chunks[-1].endswith(until):
            self.socket.settimeout(max(deadline - time.monotonic(), 0.01))
            try:
                chunks.append(self.socket.recv(1024))
            except socket.timeout:
                break
        return b"".join(chunks), chunks

    def receive_message(self, starting: bytes, timeout: float = 2) -> bytes:
        """The first whole message starting with starting, skipping others."""
        buffer = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while b"\n" in buffer:
                message, buffer = buffer.split(b"\n", 1)
                if message.startswith(starting):
                    return message + b"\n"
            self.socket.settimeout(max(deadline - time.monotonic(), 0.01))
            try:
                buffer += self.socket.recv(1024)
            except socket.timeout:
                break
        return b""


class TestAdvertisedName(unittest.TestCase):
    def test_name(self):
        self.assertEqual(advertised_name("PumpController"), "DashIO_PumpController")

    def test_long_name_cut_short(self):
        with self.assertLogs("dashio.ble_connection", "WARNING"):
            name = advertised_name("A" * 30)
        self.assertEqual(name, "DashIO_" + "A" * 22, "The name must fit the 31-byte scan response")

    def test_cut_on_a_character(self):
        with self.assertLogs("dashio.ble_connection", "WARNING"):
            name = advertised_name("A" * 21 + "é")
        self.assertEqual(name, "DashIO_" + "A" * 21, "A multi-byte character that doesn't fit is left out")


class TestGattClientSetting(unittest.TestCase):
    def conf(self, text: str) -> str:
        handle, path = tempfile.mkstemp()
        with os.fdopen(handle, "w") as conf_file:
            conf_file.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_disabled(self):
        self.assertTrue(gatt_client_disabled(self.conf("[General]\nName = pi\n\n[GATT]\nClient = false\n")))

    def test_default(self):
        self.assertFalse(gatt_client_disabled(self.conf("[GATT]\n#Client = true\n")))

    def test_enabled(self):
        self.assertFalse(gatt_client_disabled(self.conf("[GATT]\nClient = true # comment\n")))

    def test_missing_file(self):
        self.assertFalse(gatt_client_disabled("/nonexistent/main.conf"))


@unittest.skipUnless(sys.platform == "linux", "BlueZ's AcquireNotify sockets are Linux SOCK_SEQPACKET socket pairs")
class TestBLEConnection(unittest.TestCase):
    def setUp(self):
        conf = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False)
        conf.write("[GATT]\nClient = false\n")
        conf.close()
        self.addCleanup(os.remove, conf.name)
        patcher = mock.patch.object(ble_connection, "BLUEZ_MAIN_CONF", conf.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.devices = []
        self.connections = []
        self.phones = []

    def phone(self, connection, **kwargs):
        phone = FakePhone(connection, **kwargs)
        self.phones.append(phone)
        return phone

    def tearDown(self):
        for phone in self.phones:
            phone.socket.close()
        for connection in self.connections:
            connection.close()
        for device in self.devices:
            device.close()

    def make(self, backend=None, adapter=None, device_name="DEVICENAME"):
        backend = backend or FakeBlueZ()
        connection = BLEConnection(adapter=adapter, backend=backend)
        self.connections.append(connection)
        device = dashio.Device("DEVICETYPE", "DEVICEID", device_name)
        self.devices.append(device)
        connection.add_device(device)
        time.sleep(0.3)  # Let the device and connection threads connect their sockets.
        return connection, device, backend

    def test_registers_with_bluez(self):
        connection, _, backend = self.make(adapter="hci1")
        self.assertEqual(backend.adapter, "hci1")
        self.assertEqual(backend.registered, ["DashIO_DEVICETYPE"], "Registered once, advertising the device type")

    def test_one_device(self):
        connection, _, _ = self.make()
        other = dashio.Device("DEVICETYPE", "OTHERID", "OTHER")
        self.devices.append(other)
        with self.assertRaises(ValueError):
            connection.add_device(other)

    def test_device_setup_includes_ble(self):
        _, device, _ = self.make()
        self.assertIn("BLE", device._cfg["deviceSetup"].split(","))

    def test_who(self):
        connection, _, _ = self.make()
        phone = self.phone(connection)
        phone.write(b"\tWHO\n")
        data, chunks = phone.receive()
        self.assertEqual(data, b"\tDEVICEID\tWHO\tDEVICETYPE\tDEVICENAME\t1\n")
        self.assertTrue(all(len(chunk) <= 20 for chunk in chunks), "Notifications are at most MTU - 3 bytes")

    def test_writes_joined_at_newline(self):
        connection, _, _ = self.make()
        phone = self.phone(connection)
        phone.write(b"\tDEVIC")
        phone.write(b"EID\tCONNECT\n\tWH")
        self.assertEqual(phone.receive()[0], b"\tDEVICEID\tCONNECT\n")
        phone.write(b"O\n")
        self.assertEqual(phone.receive()[0], b"\tDEVICEID\tWHO\tDEVICETYPE\tDEVICENAME\t1\n")

    def test_multibyte_text(self):
        # The name starts 25 bytes into the WHO, so the 40-byte chunk boundary falls inside its 8th character.
        connection, _, _ = self.make(device_name="éééééééééé")
        phone = self.phone(connection)
        phone.write(b"\tWHO\n")
        data, chunks = phone.receive()
        self.assertTrue(all(len(chunk) <= 20 for chunk in chunks))
        self.assertEqual(data.decode(), "\tDEVICEID\tWHO\tDEVICETYPE\téééééééééé\t1\n")
        with self.assertRaises(UnicodeDecodeError, msg="Chunks may split a character, as in the firmware"):
            for chunk in chunks:
                chunk.decode()

    def test_large_mtu(self):
        connection, device, _ = self.make()
        for number in range(40):
            device.add_control(dashio.TextBox(f"T{number}", shortuuid.uuid()))  # Random titles, so it doesn't compress.
        phone = self.phone(connection, mtu=517)
        phone.write(b"\tDEVICEID\tCFG\tDASHID\t1\n")
        data, chunks = phone.receive(timeout=3)
        self.assertGreater(len(chunks), 2)
        self.assertEqual(max(len(chunk) for chunk in chunks), 512, "BlueZ reads at most 512 bytes for each notification")
        self.assertTrue(data.startswith(b"\tDEVICEID\tCFG\tDASHID\tC64\t") and data.endswith(b"\n"))
        cfg = dashio.decode_cfg64(data.split(b"\t")[5].strip().decode())
        self.assertEqual(len(cfg["TEXT"]), 40)

    def test_control_update(self):
        connection, device, _ = self.make()
        dial = dashio.Dial("D1")
        device.add_control(dial)
        phone = self.phone(connection)
        dial.dial_value = 42
        self.assertEqual(phone.receive_message(b"\tDEVICEID\tDIAL\tD1"), b"\tDEVICEID\tDIAL\tD1\t42\n")

    def test_name_callback(self):
        connection, device, _ = self.make()
        names = []
        device.set_name_callback(lambda msg: names.append(msg[2]) or msg[2])
        phone = self.phone(connection)
        phone.write(b"\tDEVICEID\tNAME\tGreenhouse\n")
        self.assertEqual(phone.receive()[0], b"\tDEVICEID\tNAME\tGreenhouse\n")
        self.assertEqual(names, ["Greenhouse"], "Provisioning messages reach the device's callbacks")

    def history_request(self, phone):
        since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()
        phone.write(f"\tDEVICEID\tTGRPH\tTG1\tDASHID\t{since}\n".encode())
        return phone.receive_message(b"\tDEVICEID\tTGRPH\tTG1", timeout=1)

    def test_history_request(self):
        connection, device, _ = self.make()
        graph = dashio.TimeGraph("TG1")
        graph.add_line("L1", dashio.TimeGraphLine("Line 1"))
        device.add_control(graph)
        graph.line_dict["L1"].add_data_point(1.5)
        phone = self.phone(connection, mtu=517)
        self.assertIn(b",1.5", self.history_request(phone))

    def test_history_request_with_server_storage(self):
        connection, device, _ = self.make()
        graph = dashio.TimeGraph("TG1")
        graph.add_line("L1", dashio.TimeGraphLine("Line 1"))
        device.add_control(graph)
        graph.line_dict["L1"].add_data_point(1.5)
        device.storage_enable(dashio.ControlName.TGRPH, "TG1")
        phone = self.phone(connection, mtu=517)
        self.assertEqual(self.history_request(phone), b"", "BLE is a local connection: the app gets the history from the Dash server")

    def test_phone_disconnects(self):
        connection, device, _ = self.make()
        dial = dashio.Dial("D1")
        device.add_control(dial)
        phone = self.phone(connection)
        phone.socket.close()
        time.sleep(0.2)
        self.assertEqual(connection._phones, {})
        dial.dial_value = 1  # Nothing to send it to.
        time.sleep(0.2)
        self.assertTrue(connection.is_alive())

    def test_writing_without_notifications(self):
        connection, _, backend = self.make()
        phone = self.phone(connection, subscribe=False)
        phone.write(b"\tWHO\n")
        time.sleep(0.5)
        phone.write(b"\tWHO\n")
        time.sleep(0.8)
        self.assertEqual(backend.disconnected, [phone.path], "Disconnected once, so it reconnects and subscribes again (bluez#1452)")

    def test_subscribing_in_time(self):
        connection, _, backend = self.make()
        phone = self.phone(connection, subscribe=False)
        phone.write(b"\tWHO\n")
        ours = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.addCleanup(ours[0].close)
        phone._on_loop(connection._phone_subscribed, phone.path, ours[1], 23)
        time.sleep(1.3)
        self.assertEqual(backend.disconnected, [])

    def test_close(self):
        connection, _, backend = self.make()
        phone = self.phone(connection)
        connection.close()
        self.assertEqual(backend.disconnected, [phone.path], "Phones are disconnected, so they subscribe again to the next run")
        self.assertEqual(backend.unregistered, 1)
        self.assertTrue(backend.closed)
        self.assertFalse(connection.is_alive())

    def test_close_disconnects_phones_without_notifications(self):
        backend = FakeBlueZ()
        connection, _, _ = self.make(backend)
        phone = self.phone(connection)
        backend._connected_unpaired = [phone.path, "/org/bluez/hci0/dev_NO_SOCKET"]
        connection.close()
        self.assertEqual(sorted(backend.disconnected), sorted([phone.path, "/org/bluez/hci0/dev_NO_SOCKET"]))

    def test_disconnects_phones_left_connected(self):
        backend = FakeBlueZ(connected_unpaired=["/org/bluez/hci0/dev_OLD"])
        self.make(backend)
        self.assertEqual(backend.disconnected, ["/org/bluez/hci0/dev_OLD"])

    def test_registration_failure_logged(self):
        with self.assertLogs("dashio.ble_connection", "ERROR"):
            self.make(FakeBlueZ(register_error="org.bluez.Error.Failed"))

    def test_warns_without_gatt_client_false(self):
        with mock.patch.object(ble_connection, "BLUEZ_MAIN_CONF", "/nonexistent/main.conf"):
            with self.assertLogs("dashio.ble_connection", "WARNING") as logs:
                self.make()
        self.assertTrue(any("Client = false" in line for line in logs.output))


if __name__ == '__main__':
    unittest.main()
