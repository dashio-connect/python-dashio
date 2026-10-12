import json
import unittest

import dashio
from dashio.package import make_packages


def unpack(reply: str) -> list[list[str]]:
    """The messages in each PKG message of a reply."""
    packages = []
    for line in reply.split("\n"):
        if not line:
            continue
        _, device_id, pkg, encoding, payload = line.split("\t")
        assert (device_id, pkg, encoding) == ("DEVICEID", "PKG", "JAOS"), line
        packages.append(json.loads(payload))
    return packages


class TestMakePackages(unittest.TestCase):
    def test_package_format(self):
        messages = "\tDEVICEID\tTEXT\tT01\t23.45\n\tDEVICEID\tBTTN\tB01\tON\n"
        reply = make_packages("DEVICEID", messages)
        self.assertEqual(reply, '\tDEVICEID\tPKG\tJAOS\t["TEXT\\tT01\\t23.45","BTTN\\tB01\\tON"]\n')
        self.assertEqual(reply.count("\t"), 4, "The tabs inside the messages are escaped in the JSON")

    def test_no_messages(self):
        self.assertEqual(make_packages("DEVICEID", ""), "")

    def test_skips_empty_messages(self):
        self.assertEqual(unpack(make_packages("DEVICEID", "\n\tDEVICEID\tTEXT\tT01\tA\n\n")), [["TEXT\tT01\tA"]])

    def test_size_limit_starts_new_package(self):
        messages = "".join(f"\tDEVICEID\tTEXT\tT{i:02d}\t{'x' * 300}\n" for i in range(5))
        packages = unpack(make_packages("DEVICEID", messages))
        self.assertEqual([len(package) for package in packages], [4, 1], "A package is sent once its messages pass 1000 characters")
        self.assertEqual(sum(packages, []), [f"TEXT\tT{i:02d}\t{'x' * 300}" for i in range(5)], "No message is lost or reordered")

    def test_non_ascii_is_utf8(self):
        self.assertIn("°C", make_packages("DEVICEID", "\tDEVICEID\tTEXT\tT01\t21°C\n"))


class TestMenuUpdates(unittest.TestCase):
    def setUp(self):
        self.device = dashio.Device("DEVICETYPE", "DEVICEID", "DEVICENAME")

    def tearDown(self):
        self.device.close()

    def tap(self, ctrl_type: str, control_id: str) -> str:
        return self.device._on_message(f"\tDEVICEID\t{ctrl_type}\t{control_id}\n".encode())

    def test_menu_tap_sends_its_controls(self):
        menu = dashio.Menu("M1", "Settings")
        text = dashio.TextBox("T1", "Name", text="Pump")
        slider = dashio.Slider("S1", "Level")
        slider.slider_value = 40
        selector = dashio.Selector("SR1", "Mode", selection=["Auto", "Manual"])
        outside = dashio.TextBox("T2", "Not in the menu", text="x")
        for control in (text, slider, selector):
            menu.add_control(control)
        for control in (menu, text, slider, selector, outside):
            self.device.add_control(control)
        messages = sum(unpack(self.tap("MENU", "M1")), [])
        self.assertIn("TEXT\tT1\tPump", messages)
        self.assertTrue(any(m.startswith("SLDR\tS1\t40") for m in messages), messages)
        self.assertTrue(any(m.startswith("BAR\tS1\t") for m in messages), "A Slider's two messages are separate items")
        self.assertTrue(any(m.startswith("SLCTR\tSR1\t") for m in messages), messages)
        self.assertFalse(any("\tT2\t" in m for m in messages), "Controls outside the menu aren't sent")

    def test_button_group_tap_sends_its_buttons(self):
        group = dashio.ButtonGroup("BG1", "Lights")
        buttons = [dashio.Button(f"B{i}", f"Light {i}") for i in (1, 2)]
        buttons[0].btn_state = dashio.ButtonState.ON
        for button in buttons:
            group.add_button(button)
            self.device.add_control(button)
        self.device.add_control(group)
        messages = sum(unpack(self.tap("BTGP", "BG1")), [])
        self.assertEqual(sorted(m.split("\t")[:3] for m in messages), [["BTTN", "B1", "ON"], ["BTTN", "B2", "OFF"]])

    def test_menu_controls_from_a_layout(self):
        view = dashio.DeviceView("DV1", "View")
        menu = dashio.Menu("M1", "Settings", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.1))
        view.add_control(menu)
        text = dashio.TextBox("T1", "Name", text="Pump", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.1))
        menu.add_control(text)
        self.device.add_cfg64(dashio.generate_cfg64(view, menu, text), 1)  # The device creates the controls.
        self.device.get_control(dashio.ControlName.TEXT, "T1").text = "Pump 2"
        self.assertEqual(sum(unpack(self.tap("MENU", "M1")), []), ["TEXT\tT1\tPump 2"])

    def test_menu_callback_still_called(self):
        menu = dashio.Menu("M1", "Settings")
        calls = []
        menu.add_receive_message_callback(calls.append)
        self.device.add_control(menu)
        self.assertEqual(self.tap("MENU", "M1"), "", "A menu without controls has nothing to send")
        self.assertEqual(len(calls), 1, "The Menu's receive callbacks are still called")

    def test_status_reply_is_packaged(self):
        text = dashio.TextBox("T1", "Name", text="Pump")
        dial = dashio.Dial("D1", "Level")
        dial.dial_value = 12
        self.device.add_control(text)
        self.device.add_control(dial)
        reply = self.device._on_message(b"\tDEVICEID\tSTATUS\n")
        name_line, packages = reply.split("\n", 1)
        self.assertEqual(name_line, "\tDEVICEID\tNAME\tDEVICENAME", "NAME stays a normal message, before the packages")
        self.assertEqual(sorted(sum(unpack(packages), [])), ["DIAL\tD1\t12", "TEXT\tT1\tPump"])

    def test_device_id_only_message(self):
        self.assertEqual(self.device._on_message(b"\tDEVICEID\n"), "")


class TestStatusLeavesOutMenus(unittest.TestCase):
    def setUp(self):
        self.device = dashio.Device("DEVICETYPE", "DEVICEID", "DEVICENAME")

    def tearDown(self):
        self.device.close()

    def status_ids(self) -> set:
        packages = self.device._on_message(b"\tDEVICEID\tSTATUS\n").split("\n", 1)[1]
        return {message.split("\t")[1] for message in sum(unpack(packages), [])}

    def test_menu_only_control_left_out_of_status(self):
        menu = dashio.Menu("M1", "Settings")
        in_menu = dashio.TextBox("T1", "In the menu", text="a")
        on_view = dashio.TextBox("T2", "On a view", text="b")
        view = dashio.DeviceView("DV1", "View")
        menu.add_control(in_menu)
        view.add_control(on_view)
        view.add_control(menu)
        for control in (view, menu, in_menu, on_view):
            self.device.add_control(control)
        self.assertIn("T2", self.status_ids())
        self.assertNotIn("T1", self.status_ids(), "A control only in a Menu is sent when the Menu is tapped")
        menu_reply = self.device._on_message(b"\tDEVICEID\tMENU\tM1\n")
        self.assertEqual(sum(unpack(menu_reply), []), ["TEXT\tT1\ta"])

    def test_button_group_buttons_left_out_of_status(self):
        group = dashio.ButtonGroup("BG1", "Lights")
        button = dashio.Button("B1", "Light")
        group.add_button(button)
        self.device.add_control(group)
        self.device.add_control(button)
        self.assertNotIn("B1", self.status_ids())

    def test_layout_menu_controls_left_out_of_status(self):
        view = dashio.DeviceView("DV1", "View")
        menu = dashio.Menu("M1", "Settings", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.1))
        view.add_control(menu)
        text = dashio.TextBox("T1", "Name", text="Pump", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.1))
        menu.add_control(text)
        self.device.add_cfg64(dashio.generate_cfg64(view, menu, text), 1)
        self.assertNotIn("T1", self.status_ids())

    def test_control_on_a_view_in_any_layout_stays_in_status(self):
        def layout(text_in_menu: bool):
            view = dashio.DeviceView("DV1", "View")
            menu = dashio.Menu("M1", "Settings", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.1))
            text = dashio.TextBox("T1", "Level", text="5", control_position=dashio.ControlPosition(0.0, 0.2, 1.0, 0.1))
            view.add_control(menu)
            (menu if text_in_menu else view).add_control(text)
            return view, menu, text
        phone = layout(text_in_menu=True)
        tablet = layout(text_in_menu=False)
        for control in phone:
            self.device.add_control(control)
        self.device.add_cfg64(dashio.generate_cfg64(*phone), 1)
        self.device.add_cfg64(dashio.generate_cfg64(*tablet), 3)
        self.assertIn("T1", self.status_ids(), "On a view in the tablet layout, so it must stay in STATUS")

    def test_control_without_parent_stays_in_status(self):
        self.device.add_control(dashio.TextBox("T1", "Loose", text="x"))
        self.assertIn("T1", self.status_ids())


if __name__ == '__main__':
    unittest.main()
