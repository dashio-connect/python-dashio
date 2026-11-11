"""WHO identifies the layout by the FNV-1a hash of its C64 (dashio-connect/dash#35)."""
import unittest
from unittest import mock

import dashio
from dashio.dash_store import fnv1a_64


def _who_layout_field(device: dashio.Device) -> str:
    return device._who_message().rstrip("\n").split("\t")[5]


def _cfg_reply_c64(device: dashio.Device, num_columns: int = 1) -> str:
    reply = device._make_cfg64([device.device_id, "CFG", "dash1", str(num_columns)])
    return reply.rstrip("\n").split("\t")[5]


def _layout(title: str) -> str:
    """A one control layout."""
    view = dashio.DeviceView("dv", title)
    dial = dashio.Dial("D1", title, control_position=dashio.ControlPosition(0.1, 0.1, 0.5, 0.5))
    view.add_control(dial)
    return dashio.generate_cfg64(view, dial)


class TestLayoutHash(unittest.TestCase):
    def setUp(self):
        self.device = dashio.Device("T", "hashdev", "Hash")
        self.dial = dashio.Dial("D1", "Dial", control_position=dashio.ControlPosition(0.1, 0.1, 0.5, 0.5))
        self.device.add_control(self.dial)

    def tearDown(self):
        self.device.close()

    def test_who_sends_the_hash_of_the_c64_the_app_downloads(self):
        field = _who_layout_field(self.device)
        self.assertRegex(field, r"^#[0-9a-f]{16}$")
        self.assertEqual(field, f"#{fnv1a_64(_cfg_reply_c64(self.device).encode()):016x}")

    def test_same_hash_for_every_column_count(self):
        field = _who_layout_field(self.device)
        for num_columns in (2, 3):
            self.assertEqual(field, f"#{fnv1a_64(_cfg_reply_c64(self.device, num_columns).encode()):016x}")

    def test_hash_follows_the_layout_without_cfg_rev(self):
        before = _who_layout_field(self.device)
        self.device.add_control(dashio.TextBox("T1", "Text", control_position=dashio.ControlPosition(0.1, 0.7, 0.5, 0.2)))
        self.assertNotEqual(_who_layout_field(self.device), before)
        self.assertEqual(self.device.config_revision, 1)

    def test_hash_is_stable(self):
        self.assertEqual(_who_layout_field(self.device), _who_layout_field(self.device))

    def test_control_values_dont_change_the_hash(self):
        before = _who_layout_field(self.device)
        self.dial.dial_value = 42
        self.assertEqual(_who_layout_field(self.device), before)

    def test_one_loaded_layout_is_hashed(self):
        self.device.add_cfg64(_layout("Phone"), 1)
        field = _who_layout_field(self.device)
        self.assertTrue(field.startswith("#"))
        self.assertEqual(field, f"#{fnv1a_64(_cfg_reply_c64(self.device, 3).encode()):016x}")

    def test_layouts_for_several_column_counts_send_cfg_rev(self):
        self.device.add_cfg64(_layout("Phone"), 1)
        self.device.add_cfg64(_layout("Tablet"), 3)
        self.assertEqual(_who_layout_field(self.device), str(self.device.config_revision))

    def test_layout_hash_off_sends_cfg_rev(self):
        device = dashio.Device("T", "revdev", "Rev", layout_hash=False)
        try:
            device.config_revision = 7
            self.assertEqual(_who_layout_field(device), "7")
        finally:
            device.close()

    def test_json_cfg_sends_cfg_rev(self):
        self.device.use_cfg()
        self.assertEqual(_who_layout_field(self.device), str(self.device.config_revision))

    def test_server_cfg_request_matches_the_hash(self):
        """The Dash server checks the C64 of its CFG DASH request against the WHO hash (dash#52)."""
        with mock.patch.object(self.device.tx_zmq_pub, "send_multipart") as send:
            self.device._send_layout_to_dash_server([self.device.device_id, "CFG", "DASH", "1"])
        c64 = send.call_args[0][0][1].decode().rstrip("\n").split("\t")[5]
        self.assertEqual(_who_layout_field(self.device), f"#{fnv1a_64(c64.encode()):016x}")


if __name__ == '__main__':
    unittest.main()
