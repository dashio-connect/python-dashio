---
name: python-dashio
description: Write Python device code with the dashio library (python-dashio) for the Dash IoT app, and generate, decode or edit CFG64 layouts with it for other device firmware such as Arduino DashIO libraries and zephyr-dashio. Use when adding controls, callbacks, layouts or connections (TCP, Dash server MQTT) to a Python device, when making config_N.c64 or a configC64Str layout, when using c64_encode, c64_decode or generate_cfg64, or when the Dash app shows the wrong or an old layout.
---

# Using python-dashio

`dashio` (`pip install dashio`, Python 3.11+) does two jobs:

- **A device in Python**: controls, their values and callbacks, and connections to the Dash app (TCP on the local network, the Dash server over MQTT).
- **The layout tool for every DashIO platform**: a layout is CFG64 (JSON, deflated, base64), and the same CFG64 works on python-dashio, Arduino and zephyr-dashio, as long as the control types and IDs match the device code.

The reference is [Documentation.md](https://github.com/dashio-connect/python-dashio/blob/master/Documents/Documentation.md); working examples are in [Examples/](https://github.com/dashio-connect/python-dashio/tree/master/Examples) (`ex01`–`ex06`, then `greenhouse/` and `server_monitor/` for full applications). Read the control's section of the reference before using an unfamiliar control.

## Rules for every layout

- **Control IDs are at most 7 characters**, case sensitive. `Control.__init__` raises `ValueError` for longer ones. zephyr-dashio allows 8, but keep to 7 so the same IDs work in a Python prototype.
- **A control is `(type, ID)`.** The layout, the device code and every handler must agree exactly: `Knob("KNB")` in Python is `dashio_send_knob("KNB", ...)` in Zephyr. A control that does nothing in the app is a mismatch first.
- **Give each control its position when you create it**, with `control_position=dashio.ControlPosition(x, y, width, height)` (ratios of the view, 0 to 1). Assigning `control.control_position` afterwards does nothing, and the app draws unpositioned controls on top of each other.
- **Raise `cfgRev` whenever the layout changes.** The app fetches the layout again only when the device reports a different cfgRev, otherwise it keeps showing the old one.
- **`deviceSetup`** (in the `CFG` object) lists the device's connections and the settings the app may change, upper case: `BLE,TCP,MQTT,NAME,WIFI,DASH,RST,FRST,SAF,BBE,APN,GNSS,OTA,CLK,FLMD`. List only what the device code implements; without `WIFI` or `DASH` the app won't offer those settings.
- **Menus and ButtonGroups:** `menu.add_control(c)` takes TextBox, Button, Slider or Selector only; `button_group.add_button(b)`. A Menu with `menu.parent_id = "PROV"` goes in the app's provisioning menu (the device's settings screen). It still needs a `control_position`, and the app only shows the provisioning menu when `deviceSetup` offers `NAME`, `WIFI` or `DASH`.
- **Column counts:** the app reports 1 column for phones, 2 for fold out phones, 3 for tablets. It gets the layout for its count, else the nearest smaller, else the smallest, so a single 1 column layout works everywhere. For more, create the controls again with that layout's positions and the same IDs, and generate a layout from each set.

## Layouts for Arduino and zephyr-dashio firmware

Keep the layout as code in a `layout.py` beside the firmware, built from controls with the firmware's types and IDs. zephyr-dashio's `samples/*/layout.py` follow this pattern:

```python
#!/usr/bin/env python3
"""Generate config_1.c64. Raise LAYOUT_REVISION after every change. --serve runs the same controls over TCP."""
import sys
import time

import dashio

LAYOUT_REVISION = 1
DEVICE_SETUP = "BLE,NAME"  # What the firmware implements, and nothing else


def make_controls():
    view = dashio.DeviceView("main", "Main")
    knob = dashio.Knob("KNB", "Knob", control_position=dashio.ControlPosition(0.2, 0.1, 0.6, 0.3))
    dial = dashio.Dial("DIAL", "Dial", control_position=dashio.ControlPosition(0.2, 0.5, 0.6, 0.3))
    view.add_control(knob)
    view.add_control(dial)
    return [view, knob, dial]  # Every control: DeviceViews, Menus, and the controls inside Menus


def write_layout():
    cfg = dashio.decode_cfg64(dashio.generate_cfg64(*make_controls(), cfg_rev=LAYOUT_REVISION))
    cfg["CFG"]["deviceSetup"] = DEVICE_SETUP  # generate_cfg64 leaves it empty
    with open("config_1.c64", "w", encoding="utf-8") as f:
        f.write('"' + dashio.encode_cfg64(cfg) + '"\n')


def serve():
    device = dashio.Device("Proto", "proto1", "Prototype")
    dashio.TCPConnection().add_device(device)
    for control in make_controls():
        device.add_control(control)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    serve() if "--serve" in sys.argv else write_layout()
```

- **`generate_cfg64(*controls, cfg_rev=N)` needs every control in the layout**: the DeviceViews, the Menus and ButtonGroups, and the controls inside them. A control left out is missing from the layout. Alarms are skipped; they have no layout entry.
- **Designing by eye:** `python layout.py --serve`, add the device in the Dash app (it appears over TCP on the local network), arrange and style the controls, and export the layout from the app. Save the exported CFG64 to a file, `c64_decode` it, raise `cfgRev`, set `deviceSetup`, and `c64_encode` it back. Once a layout has been hand-arranged in the app, the exported file is the source of truth: edit its JSON from then on, rather than regenerating it from `layout.py`.

### zephyr-dashio

- Files are `config_1.c64`, `config_2.c64`, `config_3.c64` next to `prj.conf`, each holding the CFG64 as a C string literal (the form above, or `c64_encode -f C`). Columns 2 and 3 need `CONFIG_DASHIO_CFG_FILE_COLUMN_2/3=y`.
- The build reads cfgRev, and which controls are in Menus, ButtonGroups and PROV, from the layout files. Nothing else to update.
- `deviceSetup` must match Kconfig: the module's `docs/layouts.md` has the table (`NAME` is `CONFIG_DASHIO_APP_SET_NAME`, `WIFI` is `CONFIG_DASHIO_APP_SET_WIFI`, and so on). Keep `C64DU` if an exported layout has it.

### Arduino

- The layout is a `PROGMEM` string in the sketch, passed to the device with its revision:

  ```cpp
  const char configC64Str[] PROGMEM =
  "dZJdb4IwFIb/ium1WRTdR3YnqItRYEGHF8suOluhsbSuFD9m/O/rKSjOuRtC"
  "...";

  DashDevice dashDevice(DEVICE_TYPE, configC64Str, 2);  // 2 must equal the layout's cfgRev
  ```

- **The constructor's third argument is what WHO reports**, not the cfgRev inside the layout. Raise both together, or the app keeps the old layout.
- Write it with `c64_encode layout.json -f C -o layout.c64` and paste the lines between `=` and `;`.
- `deviceSetup` lists only the settings the sketch handles (e.g. `NAME`, `WIFI`, `DASH` when it uses the provisioning library). Check the Arduino library's provisioning code when unsure.

## The command line utilities

| Command | Does |
|---|---|
| `c64_decode config_1.c64 -p` | Prints the layout as JSON, and writes `config_1.json` (`-o` names it, `-c` drops empty keys, `-i` sets the indent) |
| `c64_encode config_1.json -f C -o config_1.c64` | Encodes JSON as CFG64: `-f C` a quoted C string over several lines, `-f Python` a Python string, default plain; `-w` sets the line width |
| `dashio_data_exporter` | Exports TimeGraph and EventLog history stored on the Dash server; `-h` for its options |

`c64_decode` strips quotes, newlines, spaces, backslashes and semicolons, so it reads a plain, C or Python formatted CFG64. It doesn't strip a C declaration: from an Arduino sketch, copy only the string literals into the file.

The same in Python: `dashio.decode_cfg64(s) -> dict` and `dashio.encode_cfg64(d) -> str`.

## A device in Python

```python
import time
import dashio

device = dashio.Device("PumpCtl", "pump1", "Pump")  # Device type (same for every unit), unique ID, name
dashio.TCPConnection().add_device(device)
# Or the Dash server: dashio.DashConnection(username, password).add_device(device)

view = dashio.DeviceView("main", "Pump")
speed = dashio.Knob("SPEED", "Speed", control_position=dashio.ControlPosition(0.1, 0.1, 0.8, 0.4))
flow = dashio.Dial("FLOW", "Flow", control_position=dashio.ControlPosition(0.1, 0.55, 0.8, 0.4))
for control in (view, speed, flow):
    device.add_control(control)
view.add_control(speed)
view.add_control(flow)


def speed_rx(msg):  # msg is the message split on tabs: [device_id, type, ID, value, ...]
    speed.knob_value = float(msg[3])  # Echo the new state back, so every connected app shows it
    flow.dial_value = float(msg[3]) * 2


speed.add_receive_message_callback(speed_rx)

while True:
    time.sleep(1)
```

- **Add every control to the device** (`device.add_control`) and each visible one to its DeviceView. Setting a value attribute (`dial_value`, `knob_value`, `text`, ...) sends it to every connection.
- **Settings callbacks add their `deviceSetup` options**: `set_name_callback()` adds `NAME`, `set_wifi_callback()` `WIFI`, `set_dashio_callback()` `DASH`, `set_reset_callback()` `RST`. Connections add `TCP` and `MQTT`. With a Python prototype for firmware, set up the same callbacks as the firmware so the exported `deviceSetup` is right.
- **cfgRev for a device that builds its layout at startup**: save `device.get_cfg_hash()` with cfgRev (e.g. in an ini file), and when the hash differs, increase cfgRev and set `device.config_revision`. `Examples/greenhouse/greenhouse.py` does this. Work it out after adding connections and callbacks, since they change `deviceSetup`.
- **Loading layouts:** `device.add_cfg64(cfg64, column_no)`, or `Device(..., cfg_dict={1: phone_cfg64, 3: tablet_cfg64})`. Add the device's own controls first: loading a layout creates controls for IDs the device doesn't have. With no layout loaded, the device sends one generated from its controls (`device.get_generated_cfg_dict()`).
- **Receive callbacks can reply:** a callback's returned string is sent back to the app.
- **Through the Dash server**, control updates are only published while a Dash app is watching the device (`app_timeout`, 120 s by default); replies, alarms and history always go. A device that seems silent with the app closed is working as designed.
- History for TimeGraph, EventLog and Map: `Device(..., store=dashio.DashStore(path))` keeps it in sqlite and answers the app's history requests. See the Local Storage section of the reference.

## When the app doesn't show what you expect

Check, in order: cfgRev went up (and on Arduino, the constructor's revision too); every control type and ID matches the device code; every control was passed to `generate_cfg64()` and created with a position; `deviceSetup` lists what the device implements. If the app still shows the old layout, delete the device in the app and add it again.
