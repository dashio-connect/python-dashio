import ast
import json
import pathlib
import unittest

from dashio import (Alarm, Button, ControlName, ControlPosition, Device, DeviceView, Dial, TextBox, decode_cfg64,
                    encode_cfg64, generate_cfg64)


def make_layout(*controls, cfg_rev=1):
    """A layout dict in the form exported by the Dash app, built from controls."""
    layout = {"CFG": {"deviceSetup": "", "cfgRev": cfg_rev, "numDeviceViews": 0}}
    for control in controls:
        layout.setdefault(control.ctrl_type, []).extend(control.get_cfg64([]))
    return layout


def phone_layout():
    button = Button("b1", "Phone Button", control_position=ControlPosition(0.0, 0.0, 1.0, 0.2))
    button.parent_id = "v1"
    dial = Dial("d1", "Phone Dial", control_position=ControlPosition(0.0, 0.2, 1.0, 0.2))
    dial.parent_id = "v1"
    return make_layout(DeviceView("v1", "View 1"), button, dial)


def tablet_layout(cfg_rev=1):
    button = Button("b1", "Tablet Button", control_position=ControlPosition(0.5, 0.5, 0.5, 0.5))
    button.parent_id = "v2"
    text = TextBox("t1", "Tablet Text", control_position=ControlPosition(0.0, 0.0, 0.5, 0.5))
    text.parent_id = "v2"
    return make_layout(DeviceView("v1", "View 1"), DeviceView("v2", "View 2"), button, text, cfg_rev=cfg_rev)


class FakeSetupControl:
    """Stands in for a non layout control, such as a connection setup control."""
    ctrl_type = "SETUP"
    control_id = "s1"

    def get_cfg64(self, data):
        return [{"controlID": "s1", "setting": "on"}]


class TestDeviceLayouts(unittest.TestCase):
    def setUp(self):
        self.devices = []

    def tearDown(self):
        for device in self.devices:
            device.close()

    def make_device(self, **kwargs):
        device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME", **kwargs)
        self.devices.append(device)
        return device

    def request_cfg(self, device, num_columns):
        reply = device._make_cfg64(["", "DEVICEID", "DASHID", str(num_columns)])
        return decode_cfg64(reply.rstrip("\n").rpartition("\t")[2])

    def titles(self, cfg, ctrl_type):
        return [entry["title"] for entry in cfg.get(ctrl_type, [])]

    def test_generated_layout_without_loaded_layouts(self):
        device = self.make_device()
        device.add_control(Button("b1", "Generated", control_position=ControlPosition(0.0, 0.0, 1.0, 1.0)))
        for num_columns in (1, 2, 3):
            self.assertEqual(self.titles(self.request_cfg(device, num_columns), "BTTN"), ["Generated"])

    def test_loaded_layout_replaces_generated_layout(self):
        device = self.make_device()
        device.add_control(Button("b1", "Generated", control_position=ControlPosition(0.0, 0.0, 1.0, 1.0)))
        device.add_cfg64(phone_layout(), 1)
        self.assertEqual(self.titles(self.request_cfg(device, 1), "BTTN"), ["Phone Button"])

    def test_layout_selection_prefers_nearest_smaller(self):
        device = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        self.assertEqual(self.titles(self.request_cfg(device, 1), "BTTN"), ["Phone Button"])
        self.assertEqual(self.titles(self.request_cfg(device, 2), "BTTN"), ["Phone Button"])
        self.assertEqual(self.titles(self.request_cfg(device, 3), "BTTN"), ["Tablet Button"])

    def test_layout_selection_falls_back_to_smallest_larger(self):
        device = self.make_device(cfg_dict={3: tablet_layout()})
        self.assertEqual(self.titles(self.request_cfg(device, 1), "BTTN"), ["Tablet Button"])

    def test_layouts_do_not_mix(self):
        device = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        phone = self.request_cfg(device, 1)
        tablet = self.request_cfg(device, 3)
        self.assertNotIn("TEXT", phone, "A control only in the tablet layout should not be in the phone layout")
        self.assertNotIn("DIAL", tablet, "A control only in the phone layout should not be in the tablet layout")

    def test_num_device_views_per_layout(self):
        device = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        self.assertEqual(self.request_cfg(device, 1)["CFG"]["numDeviceViews"], 1)
        self.assertEqual(self.request_cfg(device, 3)["CFG"]["numDeviceViews"], 2)

    def test_loading_column_layout_adds_new_controls(self):
        device = self.make_device()
        device.add_cfg64(tablet_layout(), 3)
        self.assertTrue(device.is_control_loaded("TEXT", "t1"), "Controls in a column 3 layout should be added")
        self.assertEqual(device.get_control(ControlName.TEXT, "t1").parent_id, "v2")

    def test_add_cfg64_accepts_cfg64_string(self):
        device = self.make_device()
        device.add_cfg64(encode_cfg64(tablet_layout()), 2)
        self.assertEqual(self.titles(self.request_cfg(device, 2), "BTTN"), ["Tablet Button"])

    def test_add_cfg64_rejects_bad_column(self):
        device = self.make_device()
        with self.assertRaises(ValueError):
            device.add_cfg64(phone_layout(), 4)

    def test_remove_cfg64(self):
        device = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        device.remove_cfg64(3)
        self.assertEqual(self.titles(self.request_cfg(device, 3), "BTTN"), ["Phone Button"])

    def test_control_owned_values_apply_to_loaded_layouts(self):
        device = self.make_device()
        device.add_control(Dial("d1", "Code Dial", dial_min=-10.0, dial_max=50.0))
        device.add_cfg64(phone_layout(), 1)
        dial_cfg = self.request_cfg(device, 1)["DIAL"][0]
        self.assertEqual((dial_cfg["min"], dial_cfg["max"]), (-10.0, 50.0))
        self.assertEqual(dial_cfg["title"], "Phone Dial", "Layout values should come from the loaded layout")

    def test_non_layout_controls_added_to_loaded_layouts(self):
        device = self.make_device()
        device.add_control(FakeSetupControl())
        device.add_cfg64(phone_layout(), 1)
        self.assertEqual(self.request_cfg(device, 1)["SETUP"], [{"controlID": "s1", "setting": "on"}])

    def test_name_setup_from_layout_ignores_case(self):
        layout = phone_layout()
        layout["CFG"]["deviceSetup"] = "BLE,TCP,NAME,WIFI"
        device = self.make_device()
        device.add_cfg64(layout, 1)
        self.assertEqual(device._cfg["deviceSetup"], "NAME", "NAME in an app layout should turn on renaming")

    def test_cfg_hash_same_for_same_cfg(self):
        first = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        second = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        self.assertEqual(first.get_cfg_hash(), second.get_cfg_hash())

    def test_cfg_hash_ignores_cfg_rev(self):
        device = self.make_device(cfg_dict=phone_layout())
        cfg_hash = device.get_cfg_hash()
        device.config_revision = 7
        self.assertEqual(device.get_cfg_hash(), cfg_hash)

    def test_cfg_hash_changes_with_cfg(self):
        device = self.make_device(cfg_dict=phone_layout())
        cfg_hash = device.get_cfg_hash()
        device.add_cfg64(tablet_layout(), 3)
        self.assertNotEqual(device.get_cfg_hash(), cfg_hash, "Adding a column layout should change the hash")
        cfg_hash = device.get_cfg_hash()
        moved = tablet_layout()
        moved["BTTN"][0]["xPositionRatio"] = 0.25
        device.add_cfg64(moved, 3)
        self.assertNotEqual(device.get_cfg_hash(), cfg_hash, "Moving a control should change the hash")
        cfg_hash = device.get_cfg_hash()
        device.set_name_callback(lambda msg: msg[2])
        self.assertNotEqual(device.get_cfg_hash(), cfg_hash, "Changing deviceSetup should change the hash")

    def test_cfg_rev_from_layouts(self):
        device = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout(cfg_rev=4)})
        self.assertEqual(device.config_revision, 4)

    def test_single_layout_cfg_dict_loads_column_1(self):
        device = self.make_device(cfg_dict=phone_layout())
        self.assertEqual(self.titles(self.request_cfg(device, 3), "BTTN"), ["Phone Button"])

    def test_json_cfg_uses_same_layout_selection(self):
        device = self.make_device(cfg_dict={1: phone_layout(), 3: tablet_layout()})
        device.use_cfg()
        reply = device._make_cfg(["", "DEVICEID", "DASHID", "3"])
        buttons = [json.loads(line.rpartition("\t")[2]) for line in reply.splitlines() if "\tBTTN\t" in line]
        self.assertEqual([button["title"] for button in buttons], ["Tablet Button"])
        dvce = json.loads(reply.splitlines()[0].rpartition("\t")[2])
        self.assertEqual(dvce["numDeviceViews"], 2)

    def test_generated_cfg_dict_round_trip(self):
        source = self.make_device()
        source.add_control(DeviceView("v1", "View 1"))
        button = Button("b1", "Exported", control_position=ControlPosition(0.0, 0.0, 1.0, 1.0))
        button.parent_id = "v1"
        source.add_control(button)
        exported = encode_cfg64(source.get_generated_cfg_dict())
        device = self.make_device()
        device.add_cfg64(exported, 2)
        self.assertEqual(self.titles(self.request_cfg(device, 2), "BTTN"), ["Exported"])

    def test_app_exported_cfg64_loads_as_any_column(self):
        source = pathlib.Path(__file__).parent.parent / "Examples" / "ex04.py"
        tree = ast.parse(source.read_text())
        cfg64 = next(
            ast.literal_eval(node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and any(getattr(target, "id", "") == "cfg64" for target in node.targets)
        )
        device = self.make_device()
        device.add_cfg64(cfg64, 2)
        self.assertTrue(device.is_control_loaded("DIAL", "dial1"))
        self.assertEqual(len(self.request_cfg(device, 2)["DIAL"]), 1)


class TestGenerateCfg64(unittest.TestCase):
    def setUp(self):
        self.devices = []

    def tearDown(self):
        for device in self.devices:
            device.close()

    def make_device(self, **kwargs):
        device = Device("DEVICETYPE", "DEVICEID", "DEVICENAME", **kwargs)
        self.devices.append(device)
        return device

    def request_cfg(self, device, num_columns):
        reply = device._make_cfg64(["", "DEVICEID", "DASHID", str(num_columns)])
        return decode_cfg64(reply.rstrip("\n").rpartition("\t")[2])

    def button(self, title, control_position, parent_id):
        button = Button("b1", title, control_position=control_position)
        button.parent_id = parent_id
        return button

    def test_generate_cfg64_layout(self):
        cfg = decode_cfg64(generate_cfg64(
            DeviceView("v1", "View 1"),
            DeviceView("v2", "View 2"),
            self.button("Button", ControlPosition(0.0, 0.0, 1.0, 0.2), "v1"),
            cfg_rev=3
        ))
        self.assertEqual(cfg["CFG"], {"deviceSetup": "", "cfgRev": 3, "numDeviceViews": 2})
        self.assertEqual([view["controlID"] for view in cfg["DVVW"]], ["v1", "v2"])
        self.assertEqual(cfg["BTTN"][0]["parentID"], "v1")

    def test_generate_cfg64_skips_alarms(self):
        cfg = decode_cfg64(generate_cfg64(DeviceView("v1", "View 1"), Alarm("a1")))
        self.assertNotIn("ALM", cfg)

    def test_generated_column_layouts(self):
        view1 = DeviceView("v1", "View 1")
        phone = generate_cfg64(view1, self.button("Phone", ControlPosition(0.0, 0.0, 1.0, 0.2), "v1"))
        tablet = generate_cfg64(
            view1,
            DeviceView("v2", "View 2"),
            self.button("Tablet", ControlPosition(0.5, 0.5, 0.5, 0.5), "v2")
        )
        device = self.make_device(cfg_dict={1: phone, 3: tablet})
        phone_cfg = self.request_cfg(device, 2)
        tablet_cfg = self.request_cfg(device, 3)
        self.assertEqual(phone_cfg["BTTN"][0]["title"], "Phone")
        self.assertEqual(phone_cfg["CFG"]["numDeviceViews"], 1)
        self.assertEqual(tablet_cfg["BTTN"][0]["title"], "Tablet")
        self.assertEqual(tablet_cfg["BTTN"][0]["xPositionRatio"], 0.5)
        self.assertEqual(tablet_cfg["CFG"]["numDeviceViews"], 2)
        self.assertEqual(sorted(device.controls_dict), ["BTTN\tb1", "DVVW\tv1", "DVVW\tv2"])

    def test_device_keeps_its_own_controls(self):
        device = self.make_device()
        button = Button("b1", "Device Button")
        device.add_control(button)
        device.add_cfg64(generate_cfg64(
            DeviceView("v1", "View 1"),
            self.button("Layout Button", ControlPosition(0.0, 0.0, 1.0, 0.2), "v1")
        ), 1)
        self.assertIs(device.get_control(ControlName.BTTN, "b1"), button, "Loading a layout should not replace a control")
        self.assertEqual(self.request_cfg(device, 1)["BTTN"][0]["title"], "Layout Button")


if __name__ == '__main__':
    unittest.main()
