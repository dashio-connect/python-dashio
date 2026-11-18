import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from dashio.utilities import dashio_data_exporter as exporter


class TestEmptyTgrphReply(unittest.TestCase):
    """The store API's reply to a TGRPH request with no data is the header only (dash#79, dash#80)."""

    def setUp(self):
        patches = {
            "device_id": "dev1",
            "control_id": "tg1",
            "dashboard_id": "dash1",
            "out_to_file": True,
            "screen": True,
        }
        for name, value in patches.items():
            patcher = mock.patch.object(exporter, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        cwd = os.getcwd()
        os.chdir(self.tmpdir.name)
        self.addCleanup(os.chdir, cwd)

    def _parse(self, file_format):
        out = io.StringIO()
        with mock.patch.object(exporter, "file_format", file_format), contextlib.redirect_stdout(out):
            exporter.parse_line_data("user", "dev1", "dev1\tTGRPH\ttg1\tdash1")
        return out.getvalue()

    def test_csv_prints_no_data(self):
        self.assertIn("no data", self._parse("csv"))
        self.assertEqual(os.listdir(self.tmpdir.name), [])

    def test_raw_prints_no_data(self):
        self.assertIn("no data", self._parse("raw"))
        self.assertEqual(os.listdir(self.tmpdir.name), [])


if __name__ == '__main__':
    unittest.main()
