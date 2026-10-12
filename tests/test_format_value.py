import math
import unittest

import dashio
from dashio.iotcontrol.control import format_value


class TestFormatValue(unittest.TestCase):
    def test_floats_to_5_significant_digits(self):
        self.assertEqual(format_value(19.123456), "19.123")
        self.assertEqual(format_value(100.0), "100")
        self.assertEqual(format_value(0.000123456), "0.00012346")
        self.assertEqual(format_value(1234567.0), "1.2346e+06")

    def test_tiny_values_are_zero(self):
        self.assertEqual(format_value(1e-12), "0")
        self.assertEqual(format_value(-1e-12), "0")

    def test_nan(self):
        self.assertEqual(format_value(math.nan), "nan")

    def test_none_is_not_available(self):
        self.assertEqual(format_value(None), "NA")

    def test_integers_booleans_and_text_unchanged(self):
        self.assertEqual(format_value(1234567), "1234567")
        self.assertEqual(format_value(True), "True")
        self.assertEqual(format_value("b"), "b")

    def test_dial_not_available(self):
        dial = dashio.Dial("D1")
        sent = []
        dial._message_tx_event += sent.append
        dial.dial_value = None
        self.assertEqual(sent, ["\t{device_id}\tDIAL\tD1\tNA\n"])

    def test_digits(self):
        self.assertEqual(format_value(19.123456, 6), "19.1235")
        self.assertEqual(format_value(123456789.0, 6), "1.23457e+08", "Long numbers are sent in exponent notation")

    def test_dial_sends_6_digits_whatever_the_precision(self):
        for precision in (dashio.Precision.OFF, dashio.Precision.ONE, dashio.Precision.SIX):
            dial = dashio.Dial("D1", precision=precision)
            dial.dial_value = 19.123456
            self.assertEqual(dial.get_state(), "\t{device_id}\tDIAL\tD1\t19.1235\n", "The app applies the precision")

    def test_table_sends_6_digits(self):
        table = dashio.Table("TBL1", columns=2, precision=dashio.Precision.TWO)
        sent = []
        table._message_tx_event += sent.append
        table.add_table_row(dashio.TableRow("Temp", [21.456789]))
        self.assertEqual(sent, ["\t{device_id}\tTBL\tTBL1\t0\t21.4568\tTemp\n"])

    def test_slider_double_bar_formatted(self):
        slider = dashio.Slider("S1")
        slider.bar2_value = 40.0
        slider.bar1_value = 12.345678
        self.assertIn("\t{device_id}\tBAR\tS1\t12.346\t40\n", slider.get_state())


if __name__ == '__main__':
    unittest.main()
