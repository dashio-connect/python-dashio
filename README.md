# python-dashio

[![PyPI](https://img.shields.io/pypi/v/dashio)](https://pypi.org/project/dashio/)
[![Python](https://img.shields.io/pypi/pyversions/dashio)](https://pypi.org/project/dashio/)
[![Tests](https://github.com/dashio-connect/python-dashio/actions/workflows/tests.yml/badge.svg)](https://github.com/dashio-connect/python-dashio/actions/workflows/tests.yml)
[![Discord](https://img.shields.io/discord/1313341785430429747?color=5865F2&logo=Discord&style=flat-square)](https://discord.gg/fqvhNV3GQB)

A Python library that connects your project to the **Dash** IoT app, over your local network (TCP), from anywhere through the Dash server (MQTT), or over Bluetooth LE on Linux. You create controls in Python (dials, knobs, sliders, buttons, text boxes, time graphs, maps, event logs...), give them values, and handle what the app sends back. Lay them out from your code, or design the layout in the app itself. There's no app or web code to write.

- TCP on your local network, the Dash server, and Bluetooth LE on Linux (experimental), separately or together.
- Layouts for phones, fold out phones and tablets, designed in the app or built in Python.
- Notifications to your phone, through the Dash server.
- Provisioning from the app: the device name, WiFi, Dash server login, and your own settings in the app's provisioning menu.
- History for time graphs, event logs and maps, kept in sqlite and uploaded to the Dash server, for devices that are only online now and then.

It's the Python counterpart of the Arduino DashIO libraries, and speaks the same protocol. It's also the quickest way to prototype a device and design its layout before writing firmware.

![A knob turned in the Dash app: the message goes through the TCPConnection and ZMQ to the Device thread and your callback, and the dial update goes back out over TCP and through the Dash server](https://raw.githubusercontent.com/dashio-connect/python-dashio/master/docs/images/how-it-works.gif)

## The Dash app

| Apple | Android |
| :---: | :---: |
| [<img src=https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/download-on-the-app-store.svg width=200>](https://apps.apple.com/us/app/dash-iot/id1574116689) | [<img src=https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Google_Play_Store_badge_EN.svg width=223>](https://play.google.com/store/apps/details?id=com.dashio.dashiodashboard) |

TCP and BLE are free. To reach your device from anywhere, create an account on [dashio.io](https://dashio.io/account-create/). More at [dashio.io](https://dashio.io), and on [Discord](https://discord.gg/fqvhNV3GQB).

<img src="https://dashio.io/wp-content/uploads/2020/11/IMG_4154.jpeg" width="150" alt="The Dash app on a phone"> <img src="https://dashio.io/wp-content/uploads/2020/12/IMG_4203.jpeg" width="450" alt="The Dash app on a tablet">

## Requirements

Python 3.11 or later.

```sh
pip3 install dashio
```

pip installs the other dependencies. For Bluetooth LE on Linux, `pip3 install dashio[ble]`. To work on the library, clone it and `pip3 install -e .`.

## Quick start

A knob that moves a dial, on your local network. This is [Examples/ex03.py](Examples/ex03.py):

```python
# Examples/ex03.py
import dashio
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("dial1", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv = dashio.DeviceView("aView", "A Dial")
dv.add_control(first_dial_control)
device.add_control(dv)


def knob_event_handler(msg):
    first_dial_control.dial_value = float(msg[3])


aknob = dashio.Knob("aKNB", control_position=dashio.ControlPosition(0.24, 0.14, 0.54, 0.26))
aknob.add_receive_message_callback(knob_event_handler)
dv.add_control(aknob)
device.add_control(aknob)

while True:
    time.sleep(1)
```

Run it, then add the device in the Dash app: it's found on the local network. Turn the knob, and the dial follows. [Getting started](docs/getting-started.md) goes on from here.

## How you develop with it

1. **Create the controls** in Python, with IDs of up to 7 characters, and run the device over TCP.
2. **Design the layout** in the Dash app, and export it. Or build it in Python with `generate_cfg64()`.
3. **Load the layout** into the device, with `cfg_dict` or `add_cfg64()`, and handle the app's messages in the controls' callbacks.
4. **Change the layout** later by raising its cfgRev, so the app fetches the new one.
5. **Connect to the Dash server** to reach the device from anywhere, send notifications and keep history.

The same layout works on Arduino firmware with controls of the same types and IDs. [docs/layouts.md](docs/layouts.md) covers each step.

## Documentation

| | |
|---|---|
| [Getting started](docs/getting-started.md) | From a dial on your phone to a device you can reach from anywhere |
| [Layouts](docs/layouts.md) | Designing, generating and loading layouts; Menus and the provisioning menu |
| [Controls](docs/controls.md) | Every control: its settings, its values, and what its callbacks receive |
| [The Device](docs/device.md) | Controls, provisioning from the app, reset, the clock |
| [Connections](docs/connections.md) | The Dash server, TCP, Bluetooth LE and ZMQ |
| [Storing history](docs/storage.md) | Time graph, event log and map history, on the device and the Dash server |
| [Exporting data](docs/data-exporter.md) | `dashio_data_exporter`: history from the Dash server, as text or CSV |
| [Examples](Examples) | `ex01`–`ex06` from the docs; [greenhouse](Examples/greenhouse), [server_monitor](Examples/server_monitor) and [intermittent_connection.py](Examples/intermittent_connection.py) are complete applications |

### Command line utilities

The library installs three commands. Run any of them with `-h` for its options.

| Command | |
|---|---|
| `c64_decode layout.c64` | Decodes a CFG64 layout, e.g. one exported from the Dash app, to JSON |
| `c64_encode layout.json` | Encodes a JSON layout to CFG64, optionally formatted for C or Python code with `-f` |
| `dashio_data_exporter -u USERNAME -p PASSWORD -d DEVICE_ID -c CONTROL_ID` | Exports time graph or event log history from the Dash server ([docs](docs/data-exporter.md)) |

### For Claude Code users

[skills/python-dashio](skills/python-dashio) is a Claude Code skill that teaches Claude how to use this library, and how to make layouts for Arduino and zephyr-dashio firmware: copy or link it into your project's `.claude/skills/` directory.

## Working on the library

[CLAUDE.md](CLAUDE.md) describes the code, and how to run the tests and lint.

## License

MIT, see [LICENSE](LICENSE).
