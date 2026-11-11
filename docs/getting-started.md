# Getting started

From a dial on your phone, over your local network, to a device you can reach from anywhere through the Dash server.

## What you need

- Python 3.11 or later.
- The Dash app, on [iOS](https://apps.apple.com/us/app/dash-iot/id1574116689) or [Android](https://play.google.com/store/apps/details?id=com.dashio.dashiodashboard).
- Your computer and phone on the same network, for TCP.
- For the Dash server: an account, from [dashio.io](https://dashio.io/account-create/).

## 1. Install the library

```sh
pip3 install dashio
```

pip installs the other dependencies: paho-mqtt, pyzmq, python-dateutil, zeroconf, shortuuid and pyserial. For Bluetooth LE on Linux, install `dashio[ble]` instead; see [connections.md](connections.md#bleconnection).

## 2. A dial

The fewest lines that talk to the app ([Examples/ex01.py](../Examples/ex01.py)):

```python
# Examples/ex01.py
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("dial1")
device.add_control(first_dial_control)

while True:
    first_dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

- `Device("aDeviceType", "aDeviceID", "aDeviceName")`:
  - the **device type** is the same for every device running this code; the app uses it to find them.
  - the **device ID** identifies this device. Make it unique, e.g. a UUID.
  - the **name** is what the app shows. The user can change it from the app if you let them ([device.md](device.md#provisioning-from-the-dash-app)).
- `TCPConnection()` listens on your local network and advertises the device with mDNS (`_DashIO._tcp.`). Add each device to its connections.
- Setting `dial_value` sends the value to every connected app.

Run it, then add the device in the Dash app: it's found on the local network. The dial isn't on a screen yet, though. For that, the device needs a layout.

## 3. Put the dial on a screen

A **DeviceView** is a screen in the app. Give the dial a position, and add it to a DeviceView ([Examples/ex02.py](../Examples/ex02.py)):

```python
# Examples/ex02.py
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("dial1", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv_dial = dashio.DeviceView("aView", "A Dial")
dv_dial.add_control(first_dial_control)
device.add_control(dv_dial)

while True:
    first_dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

`ControlPosition(x, y, width, height)` is in fractions of the DeviceView: 0.0 is the top or left edge, 1.0 the bottom or right. With a position and a DeviceView, the library generates a layout from the controls, and the app shows the dial on its own screen.

## 4. Take input from the app

When the user changes a control, the control's callbacks are called with the message from the app. Here a knob sets the dial ([Examples/ex03.py](../Examples/ex03.py)):

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

The callback receives the message split on tabs: `msg[2]` is the control ID and `msg[3]` the value, here the knob's position as text. [controls.md](controls.md#summary) lists what each control sends.

## 5. Reach it from anywhere

A TCPConnection only works on your local network. A **DashConnection** connects the device to the Dash server with your Dash account's username and password, so the app reaches it from anywhere. The server also sends notifications, with an Alarm ([Examples/ex06.py](../Examples/ex06.py)):

```python
# Examples/ex06.py
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID3", "aDeviceName")
dash_con = dashio.DashConnection("your_dash_username", "your_dash_password")
dash_con.add_device(device)

first_dial_control = dashio.Dial("dial1", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)
dv = dashio.DeviceView("aView", "A Dial")
dv.add_control(first_dial_control)
device.add_control(dv)

alarm = dashio.Alarm("hiAlarm")
device.add_control(alarm)

high = False
while True:
    value = random.random() * 100
    first_dial_control.dial_value = value
    if value > 90 and not high:
        alarm.send("High value", f"The dial is at {value:.0f}")
    high = value > 90
    time.sleep(5)
```

The alarm is sent when the dial goes above 90. A device can use a TCPConnection and a DashConnection at the same time. See [connections.md](connections.md).

## 6. Design your own layout

The layout generated from the controls is a start. For a better one, arrange the controls in the Dash app, export the layout as a **CFG64** string, and load it into the device. For example, run ex03 above, rearrange its controls in the app and export the layout ([Examples/ex04.py](../Examples/ex04.py)):

```python
# Examples/ex04.py
import dashio
import time

cfg64 = "jVTbjtowEP0VlOeqImyXSn1LCLCIXFDiQqWqD97ESywSmzrOAl3x7+sxOAk3qW/jM+Pxseccf1jeLLZ+9H7/+dKzRpOpCj8sVpce"\
    "eacpWVKyqxRkq2SmkYTIeqsQy1JQ+raOyTvkj2o1DyMXOn1YKWdS8GLmQSGehy4U54SucxljSbmC+18HQwVKKguy4BVVKINqN0Io"\
    "CiyTAsjpzRl/BagiLItYcYhYTAqCK0hLUROVKils70NRzncBZQHeK+ANFxWkBcmWuKhhw/dntd5iQZg8E4RbQvuM4iLgmT50Evl+"\
    "tAJ0b+h1qH9T+I5mMm+xZ8A2iuiIF1xAi5hkpmuDucABSMrD6XJhFAeOD9Dh9hwbepb6Ina/f9Qj8ptpJb7XxM7SM2HgLEzoomkT"\
    "B+Pwp4nR+Bcyse/6JvSWy9V5gFK0nFc5laSXlHxzSd11ktlIy0BVu1xkRDzasxY0U7m6ZKCmwQA2XWjEjIAqOMSl7p/8rdWUrqTg"\
    "qddsztysWdZ5WpxuNMFcbTud1uoD6hG0cfn+dks3iwRmldZHejhLqklPFOmE/gMu9vCcUELrwAOoV/5pb2t32d5rfsMGXivm2nhP"\
    "Az11P5o2Hn2JUauAEYrbYaOwmeTM8U+T3AqS0upkrv71s4M0betE+JWIrg/98QRdTHsxG1uPjNNI9MKIW06Z7GjCaL9mVFbmC7n7"\
    "K1y7FXhOaFFcW+v/fg8jmUdGvmO8p+EDg99+Lno+aBovXvTjHz8B"


config_dict = dashio.decode_cfg64(cfg64)
device = dashio.Device("aDeviceType", "aDeviceID2", "aDeviceName1", cfg_dict=config_dict)
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)

aknob: dashio.Knob = device.get_control(dashio.ControlName.KNOB, "aKNB")
first_dial_control: dashio.Dial = device.get_control(dashio.ControlName.DIAL, "dial1")


def knob_event_handler(msg):
    aknob.knob_dial_value = float(msg[3])
    first_dial_control.dial_value = float(msg[3])


aknob.add_receive_message_callback(knob_event_handler)

while True:
    time.sleep(1)
```

`Device(..., cfg_dict=...)` creates the controls in the layout. Get them with `get_control()` to set their values and add callbacks.

**The app notices a changed layout by itself:** the device identifies its layout by a hash of it. A device with layouts for several column counts reports cfgRev instead, and then you increase it (`device.config_revision`) when you change a layout. [layouts.md](layouts.md) covers layouts for phones and tablets, and building them in code.

## Where next

- [Controls](controls.md): every control, its settings and its values.
- [The Device](device.md): provisioning from the app, reset, the clock.
- [Storing history](storage.md): time graph, event log and map history, on the device and the Dash server.
- [Examples/greenhouse](../Examples/greenhouse) and [Examples/server_monitor](../Examples/server_monitor): complete applications.

## When something's wrong

- **The app doesn't find the device on the local network:** check that the phone and the computer are on the same network, and that nothing blocks TCP port 5650 or mDNS.
- **The app shows an old layout:** update the Dash app, since versions from before the layout hash don't understand it (or use `Device(layout_hash=False)`). For a device that reports cfgRev, increase it. If that doesn't help, delete the device in the app and add it again.
- **A `ValueError` about a control ID:** IDs are at most 7 characters, in your code and in loaded layouts ([controls.md](controls.md#how-controls-work)).
- **Nothing from the Dash server:** check the username and password; the library logs failed logins. Control updates only go to the server while an app is watching ([connections.md](connections.md#dashconnection)).
