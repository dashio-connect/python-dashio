import enum
import inspect
import unittest

import dashio
from dashio.iotcontrol import enums


class TestExports(unittest.TestCase):
    def test_all_enums_exported(self):
        for name, value in inspect.getmembers(enums, inspect.isclass):
            if issubclass(value, enum.Enum) and value.__module__ == enums.__name__:
                self.assertIs(getattr(dashio, name, None), value, f"dashio.{name}")
                self.assertIn(name, dashio.__all__)

    def test_all_names_exist(self):
        for name in dashio.__all__:
            self.assertTrue(hasattr(dashio, name), f"dashio.{name}")

    def test_textbox_and_device_view_enums(self):
        textbox = dashio.TextBox("T1", caption_mode=dashio.CaptionMode.SENT)
        self.assertEqual(textbox._configs[0].cfg["captionMode"], dashio.CaptionMode.SENT.value)
        device_view = dashio.DeviceView("DV1", style=dashio.DeviceViewStyle.BASIC)
        self.assertEqual(device_view._configs[0].cfg["style"], dashio.DeviceViewStyle.BASIC.value)


if __name__ == '__main__':
    unittest.main()
