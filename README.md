# python-dashio

![Tests](https://github.com/dashio-connect/python-dashio/actions/workflows/tests.yml/badge.svg)

**[python-dashio](https://github.com/dashio-connect/python-dashio)** - Create beautiful mobile dashboards for your python project. The python-dashio library allows easy setup of controls such as Dials, Text Boxes, Charts, Graphs, and Notifications. You can define the look and layout of the controls on your phone from your python code. There are three methods to connect to your phone; Bluetooth Low Energy (BLE - on supported platforms), TCP, and MQTT via the dash.dashio.io server.

## Getting Started

* For the big picture on **DashIO**, take a look at our website: [dashio.io](https://dashio.io")

* Create an account on [dash.dashio.io](https://dashio.io/account-create/)

* Get the App:

Apple              | Android
:-----------------:|:------------------:
[<img src=https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/download-on-the-app-store.svg width=200>](<https://apps.apple.com/us/app/dash-iot/id1574116689>) | [<img src=https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Google_Play_Store_badge_EN.svg width=223>](<https://play.google.com/store/apps/details?id=com.dashio.dashiodashboard>)

## Documentation

For all documentation and software guides: [dashio.io/documents](https://dashio.io/documents)

For the **DashIO** Python guide: [dashio.io/guide-python](https://dashio.io/guide-python)

For the **DashIO** Python library: [dashio.io/python-library]("https://dashio.io/python-library/)

## Examples

There are plenty of examples in the github repository under the Examples directory.

## Dash IoT Application

The **Dash** app is free and available for both Apple and Android devices. Use it to create beautiful and powerful user interfaces to you IoT devices.

Dashio Phone               |  Dashio Tablet
:-------------------------:|:-------------------------:
<img src="https://dashio.io/wp-content/uploads/2020/11/IMG_4154.jpeg" width="150" /> | <img src="https://dashio.io/wp-content/uploads/2020/12/IMG_4203.jpeg" width="450" />

## Requirements

* python3.6 and above
* paho-mqtt
* pyzmq
* python-dateutil
* zeroconf
* shortuuid

## Install

`pip3 install dashio`

Or

```sh
git clone https://github.com/dashio-connect/python-dashio.git
cd python-dashio
pip3 install .
```

## A Quick Guide

This guide covers the **DashIO** python library. For information on the [***Dash***](https://dashio.io/dashboard) phone app please visit the website.

### Basics

So what is **DashIO**? It is a quick effortless way to connect your IoT device to your phone. It allows easy setup of controls such as Dials, Text Boxes, Maps, Graphs, Notifications..., from your Device. You can define the look and layout of the controls on your phone from your IoT device. There are three methods to connect to your phone tcp, mqtt, dash, and BLE. What's Dash then? Dash is a mqtt server with extra bits added in to allow you to send notifications, share your devices, and save your settings from your phone via the **Dash** app.

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

The next two lines create a TCP connection and then add the device to the connection. This device is discoverable by the Dash app. You can also discover your IoT device using a third party Bonjour/Zeroconf discovery tool. The mDNS service will be "DashIO.tcp."

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

First we altered the instantiation of a Dial by including a control_position. This allows us to place the control at a set location. The added lines instantiated a DeviceView control, which we than added the dial control. Finally we added the DeviceView to the device.

The next piece of the puzzle to consider is how do we get data from the DashIO app? Lets add a Knob and connect it to the Dial:

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
aknob.add_receive_message_callback += knob_event_handler
dv.add_control(aknob)
device.add_control(aknob)

while True:
    time.sleep(1)
```

First we added a function that sets the dial value. Next we added a Knob control and added our new function to be called when it receives data from the DashIO app. We also add it to the DeviceView and to the device. Now when the knob in the DashIO app is moved the dial is set to the same value.

### Using the Config64

The **Dash** app can generate a CFG64 text string that defines the controls, the controls layout, and device parameters for the Device. The CFG64 string can be used in a number of ways. If we run the example above and using the **Dash** app to export a layout we can use the layout to setup the device and controls.

```python
# Examples/ex04.py
import dashio
import time

cfg64 = "pVNdr5pAEP0rN/tMjHCrbXnjQ60RxQD1Nmn6wIVVN8IuXZar1vjfOwuLeNWmTfo2OztzZnLmnBPybA+Z339oaLbwbYhOqBTHDCMT"\
"LfxgbnlIQwmjgrNs6kIyni1sSJWYpj7Njj4NcIbjEuoFr7CG8viATL3f11ARc0xF0+TiN5LgFcF7eGuI43QVZxU0fRxoSBBRz7Oe"\
"ZpS9wvcWk81WBLEgDJn9njFUNUtWEshRqLX9KPLncpEt288Jncux6zgrYYVjW3dB0D9oaAfYDssYh+4Ap9Cakjgbsyxj+7Ie3PbL"\
"fFtpyy01tCep2F7gBgB3uBtiQDYnsFz/DGyGnhs0vEajb5GKnCUyT6hgXCBzMBwASaSw0pTjsoRZ+mejpw8/9fSebvTRWUPuVEHM"\
"rWUTeP5EZUaLr000CZZfmshauU0Qek6kOh1PBe5q9fLuurYVTh15XMEzYG8MNw7JL/gxYK0NJylQUOUUFjMMSTNcs8m0l6ZVfinR"\
"b0Ryc285w2Y8xbzl9WVLBH4Kc7bD7f9uQ9OO9jjZqY+/tEQ8pmWtteQI3MtF3mN08nLhsKo1kkmbHR4NbP/ukCUrAagFmc/GVWlH"\
"nQ5KJUDEIs7lxPBnBd1IysGdWl5Nf8FxQspaxIDYHmM5Hd34bEx4KdTC/+UphfHAU7X+SXYhuHHFH512b6tnACkYoaK7q/ILaOMV"\
"8ysUbzSOHrv1X61VUSKkS9C1y6JO/XYULdpoouzijCfScGnNVIhFVQAAheNoe7ImmkiKZteOSqXl9SbAbxCez78B"

config_dict = dashio.decode_cfg64(cfg64)
device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName", cfg_dict=config_dict)
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

We've added the cfg64 string. Then decoded it with *dashio.decode_cfg64(cfg64)*. This function returns a dictionary that we can pass into Device so that it can to instantiate and add the controls.

Included in the library are two commandline utilities to encode and decode cfg64 files.

```sh
$ c64_decode -h
usage: c64_decode [-h] [-p] [-o OUT_FILE] [-i INDENT] file

positional arguments:
  file                  Input file name.

options:
  -h, --help            show this help message and exit
  -p, --print           Print output.
  -o OUT_FILE, --out OUT_FILE
                        output filename.
  -i INDENT, --indent INDENT
                        Indent depth (Default 4).
```

And

```sh
$ c64_encode -h
usage: c64_encode [-h] [-f FORMAT] [-o OUT_FILE] [-w WIDTH] file

positional arguments:
  file                  Input file name.

options:
  -h, --help            show this help message and exit
  -f FORMAT, --format FORMAT
                        Format output. Options: 'None', 'C', 'Python'.
  -o OUT_FILE, --out OUT_FILE
                        output filename.
  -w WIDTH, --width WIDTH
                        Width of formatted output (Default 80).
```
