# python-dashio

[![PyPI](https://img.shields.io/pypi/v/dashio)](https://pypi.org/project/dashio/)
[![Python](https://img.shields.io/pypi/pyversions/dashio)](https://pypi.org/project/dashio/)
[![Tests](https://github.com/dashio-connect/python-dashio/actions/workflows/tests.yml/badge.svg)](https://github.com/dashio-connect/python-dashio/actions/workflows/tests.yml)
[![Discord](https://img.shields.io/discord/1313341785430429747?color=5865F2&logo=Discord&style=flat-square)](https://discord.gg/fqvhNV3GQB)

**[python-dashio](https://github.com/dashio-connect/python-dashio)** - Create beautiful mobile dashboards for your python project. The python-dashio library allows easy setup of controls such as Dials, Text Boxes, Charts, Graphs, and Notifications. You can define the look and layout of the controls on your phone from your python code. Connect to your phone over TCP on your local network, or from anywhere through the Dash server (dash.dashio.io), which also sends notifications, stores data and lets you share your devices. Bluetooth Low Energy (BLE) is available on Linux, and is experimental.

## Getting Started

* For the big picture on **DashIO**, take a look at our website: [dashio.io](https://dashio.io)

* Create an account on [dash.dashio.io](https://dashio.io/account-create/)

* Get the App:

Apple              | Android
:-----------------:|:------------------:
[<img src=https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/download-on-the-app-store.svg width=200>](<https://apps.apple.com/us/app/dash-iot/id1574116689>) | [<img src=https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Google_Play_Store_badge_EN.svg width=223>](<https://play.google.com/store/apps/details?id=com.dashio.dashiodashboard>)

## Discord Community

Be a part of the DashIO community by joining our [Discord Server](https://discord.gg/fqvhNV3GQB)

## Documentation

For all documentation and software guides: [dashio.io/documents](https://dashio.io/documents)

For the **DashIO** Python guide: [dashio.io/guide-python](https://dashio.io/guide-python)

For the **DashIO** Python library: [dashio.io/python-library](https://dashio.io/python-library/)

The library reference is in [Documents/Documentation.md](Documents/Documentation.md).

## Examples

There are plenty of examples in the github repository under the Examples directory. For complete applications, see [Examples/greenhouse](Examples/greenhouse) and [Examples/server_monitor](Examples/server_monitor).

## Dash IoT Application

The **Dash** app is free and available for both Apple and Android devices. Use it to create beautiful and powerful user interfaces to your IoT devices.

Dashio Phone               |  Dashio Tablet
:-------------------------:|:-------------------------:
<img src="https://dashio.io/wp-content/uploads/2020/11/IMG_4154.jpeg" width="150" /> | <img src="https://dashio.io/wp-content/uploads/2020/12/IMG_4203.jpeg" width="450" />

## Requirements

Python 3.11 or later. pip installs the other dependencies: paho-mqtt, pyzmq, python-dateutil, zeroconf, shortuuid and pyserial.

## Install

### From PyPI (Recommended)

```sh
pip3 install dashio
```

### From Source

For development (editable install):

```sh
git clone https://github.com/dashio-connect/python-dashio.git
cd python-dashio
pip3 install -e .
```

For regular installation:

```sh
git clone https://github.com/dashio-connect/python-dashio.git
cd python-dashio
pip3 install .
```

## A Quick Guide

This guide covers the **DashIO** python library. For information on the [***Dash***](https://dashio.io/dashboard) phone app please visit the website.

### Basics

So what is **DashIO**? It is a quick, effortless way to connect your IoT device to your phone, with controls such as Dials, Text Boxes, Maps, Graphs and Notifications set up from your device. What's Dash then? Dash is an MQTT server with extra features: it sends notifications, stores time graph, event log and map data, lets you share your devices, and saves your settings from the **Dash** app.

Show me some code.

```python
# Examples/ex01.py
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial")
device.add_control(first_dial_control)

while True:
    first_dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

This is about the fewest lines of code to get talking to the app. There is a lot happening under the hood to make this work. After the import we create a device with three attributes:

* "aDeviceType": a common name device_type for all IoT devices using this code which is used for device discovery
* "aDeviceID": a device_ID to uniquely identify this device, preferably a UUID.
* "aDeviceName": The name of this device, which can be changed at any time.

These attributes describe the device to the app and allow you to distinguish one of your devices from another.

The next two lines create a TCP connection and then add the device to the connection. This device is discoverable by the Dash app. You can also discover your IoT device using a third party Bonjour/Zeroconf discovery tool. The mDNS service will be "_DashIO._tcp."

Though this device is discoverable by the app it would be nice to have the DashIO app automatically setup a new DeviceView and place your control on the new DeviceView. To do that we need to add a few more lines of code:

```python
# Examples/ex02.py
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv_dial = dashio.DeviceView("aDeviceViewID", "A Dial")
dv_dial.add_control(first_dial_control)
device.add_control(dv_dial)

while True:
    first_dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

First we altered the instantiation of a Dial by including a control_position. This allows us to place the control at a set location. The added lines instantiated a DeviceView control, to which we then added the dial control. Finally we added the DeviceView to the device.

The next piece of the puzzle to consider is how do we get data from the DashIO app? Let's add a Knob and connect it to the Dial:

```python
# Examples/ex03.py
import dashio
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv = dashio.DeviceView("aDeviceViewID", "A Dial")
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

First we added a function that sets the dial value. Next we added a Knob control and added our new function to be called when it receives data from the DashIO app. We also add it to the DeviceView and to the device. Now when the knob in the DashIO app is moved the dial is set to the same value.

### Connecting From Anywhere

A TCPConnection only works on your local network. To reach your device from anywhere, connect it through the Dash server with a DashConnection, using your Dash account username and password. The Dash server can also send notifications to your phone, with an Alarm:

```python
# Examples/ex06.py
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID3", "aDeviceName")
dash_con = dashio.DashConnection("your_dash_username", "your_dash_password")
dash_con.add_device(device)

first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)
dv = dashio.DeviceView("aDeviceViewID", "A Dial")
dv.add_control(first_dial_control)
device.add_control(dv)

alarm = dashio.Alarm("HighAlarm")
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

The alarm is sent when the dial goes above 90. A device can use a TCPConnection and a DashConnection at the same time. The Dash server can also store the data of time graphs, event logs and maps, with *device.storage_enable()*. See the [Documentation](Documents/Documentation.md#dashconnection).

### Using the Config64

The **Dash** app can generate a CFG64 text string that defines the controls, the controls layout, and device parameters for the Device. For example, run ex03 above, arrange its controls in the **Dash** app, and export the layout. The layout can then set up the device and its controls:

```python
# Examples/ex04.py
import dashio
import time

cfg64 ="jVTbjpswEP2VlZ9RlWS7qcQbhJCNwiUCN6lU9YEFb7ACdmrMJukq/94xhpCbqr4NZ8bj4zlz+ETOPELmz18GmrgzZH4iVpcO+aAp"\
    "WVGyr5A5NFDWfMdE1jtkImSg9H0TkQ/InQy0CEIbGnyilDMpeDF3oCZZBDbU5YRuchklknJkDr6MxgaSVBZkySsKGINKO8Q49FGb"\
    "AMB6WjD+BkBFWBay4hiyiBQkqSApRU0MVFI4OICCnO99yvzkgMz3pKggJUi2SooaSr+9GGiXCMKkJtS/Cb7hSTQpfJ6pC93Q88I1"\
    "YIeOVk/4q4H2NJP5GXkBZAv8JrzgAg5HJGu7dYitrgdy8tg8Jwgj3/IAON51H0KvUpEfDgYnJYDXKhF7ThtZK0cHvrXUgY1nbeRP"\
    "g+86wtMfWEee7enAWa3WWhUpztTWOZXkKS759pKhbcXziRIVKm0uMiIe128EzSBTlwy2YjQyrgW/mS+FZJCUqn/8uwYdrhR2YF7d"\
    "jdsNy/rZJelWUcvhhL6rE13VYtXA5ofb8sscFgmrGuHTY7Ml56QLdGP6BxgMxxqGzenBEdTC7p9fOLzgd9/0hoGaTcSVXZ5HSkov"\
    "nLWmeo1wJ+oER52GOGhlmlteI9NOkJRWjSUG15N1qahkOzDg90bEhXu8qYsvpFzOp+ifa9+tW2+iHadM9pK321szKivt9QcevnaZ"\
    "Wn6XFuct05b4D5+3j3psu3u7PI8fmfHuJ6DGj2fR8lVN+PQX"

config_dict = dashio.decode_cfg64(cfg64)
device = dashio.Device("aDeviceType", "aDeviceID2", "aDeviceName1", cfg_dict=config_dict)
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)

aknob: dashio.Knob = device.get_control(dashio.ControlName.KNOB, "aKNB")
first_dial_control: dashio.Dial = device.get_control(dashio.ControlName.DIAL, "FirstDial")

def knob_event_handler(msg):
    aknob.knob_dial_value = float(msg[3])
    first_dial_control.dial_value = float(msg[3])

aknob.add_receive_message_callback(knob_event_handler)

while True:
    time.sleep(1)
```

We've added the cfg64 string. Then decoded it with *dashio.decode_cfg64(cfg64)*. This function returns a dictionary that we can pass into Device so that it can instantiate and add the controls.

The **Dash** app reports its screen size in columns: 1 for phones, 2 for fold out phones and 3 for tablets. A device can hold a layout for each, e.g. `cfg_dict={1: phone_cfg64, 3: tablet_cfg64}`, and layouts can also be built in code with *dashio.generate_cfg64()*. See [Layouts](Documents/Documentation.md#layouts).

The **Dash** app only fetches a new layout when the device's cfgRev changes, so increase *device.config_revision* whenever the layout changes. *device.get_cfg_hash()* helps tell when it has changed.

### Command Line Utilities

The library installs three command line utilities. Run any of them with `-h` for its options.

| Command | What it does |
|---------|--------------|
| `c64_decode layout.c64` | Decode a CFG64 layout, e.g. one exported from the **Dash** app, to JSON. |
| `c64_encode layout.json` | Encode a JSON layout to CFG64, optionally formatted for C or Python code with `-f`. |
| `dashio_data_exporter -u USERNAME -p PASSWORD -d DEVICE_ID -c CONTROL_ID` | Export time graph or event log data stored on the Dash server. See [the data exporter guide](Documents/dashio_data_exporter.md). |

## License

MIT, see [LICENSE](LICENSE).
