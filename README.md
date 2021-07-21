# dashio

[Dashio](http://dashio.io) - a python library to connect and display widgets on the IotDashboard app.

## Getting Started

See <https://github.com/dashio-connect/python-dashio>

```bash
cd Examples
python3 iot_monitor.py -s dash.dashio.io -p 8883 -u user -w password -c`hostname`
```

Will create a graph of network traffic with a connection_id of your hostname. The control and data topics are hostname_data and hostname_control.

## Requirements

* python3
* paho-mqtt
* pyzmq
* python-dateutil
* zeroconf
* shortuuid

## Install

pip3 install dashio

## Guide

This guide covers the dashio python library. For information on the [IoTDashboard](https://dashio.io/dashboard) phone app please visit the website.

### Basics

So what is dashio? It is a quick effortless way to connect your IoT device to your phone. It allows easy setup of controls such as dials, text boxes, maps, graphs, notifications..., from your device. You can define the look and layout of the controls on your phone from your IoT device. There are three methods to connect to your phone tcp, mqtt, dash, and BLE. What's Dash then? Dash is a mqtt server with extra bits added in to allow you to send notifications, share your devices, and save your settings from your phone via the IoTDashboard app.

Show me some code!

```python
import dashio
import random
import time

device = dashio.dashDevice("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.tcpConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial")
device.add_control(first_dial_control)

while True:
    dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

This is about the fewest lines of code to get talking to the app. There is a lot happening under the hood to make this work. After the import we create a device with three attributes. These attributes describe the device to the app and allow you to distinguish one of your devices from another. The next two lines create a TCP connection and then add the device to the connection. The connection will be created with the default setting of port 5000 and will also advertise the service using zeroconf, also known as bonjour. This allows IoTDashboard to find your device. After that we create a dial add it to the device and then every five seconds send a randomly generated dial value to the IoTDashboard app.

This device is discoverable by the app. It would be nice to have IoTDashboard automagically setup a new DeviceView and place your control on the new DeviceView. To do that we need to add a few more lines of code:

```python
import dashio
import random
import time

device = dashio.dashDevice("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.tcpConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv_dial = dashio.DeviceView("aDeviceViewID", "A Dial")
dv_dial.add_control(first_dial_control)
device.add_control(dv_dial)

while True:
    dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

First we altered the instantiation of a Dial by including a control_position. This allows us to place the control at a set location. The added lines instantiated a DeviceView control, which we than added the dial control. Finally we added the dv to the device.

The next piece of the puzzle to consider is how do we get data from the IoTDashboard app? Lets add a Knob and connect it to the Dial:

```python
import dashio
import random
import time

device = dashio.dashDevice("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.tcpConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

dv_dial = dashio.DeviceView("aDeviceViewID", "A Dial")
dv_dial.add_control(first_dial_control)
device.add_control(dv_dial)

def knob_event_handler(msg):
    first_dial_control.dial_value = float(msg[3])

aknob = dashio.Knob("aKNB", control_position=dashio.ControlPosition(0.24, 0.14, 0.54, 0.26))
aknob.message_rx_event = knob_event_handler
dv_dial.add_control(aknob)
device.add_control(aknob)

while True:
    time.sleep(5)
```

First we added a function that sets the dial value. Next we added a Knob control and set our new function to be called when it receives data from the IoTDashboard app.
We also add it to the DeviceView and to the device. Now when the knob in IoTDashoard is moved the dial is set to the same value. 

### Controls

Controls are objects that represent actions and widgets in the IoTDashboard application. Controls that are displayed have a ```dashio.ControlPosition``` that is composed of four size and position variables: x_position_ratio, y_position_ratio, width_ratio, height_ratio. The first two are position ratios that place the top left corner of the widget on the DeviceView. The last two are ratios that govern the size of the widget. The ratios are propertional to the size of the screen with the full size of the screen representing 1.0.

#### Alarm

```python
alarm = dashio.Alarm("alarm1_ID", description="An alarming alarm", sound_name=SoundName.SHIPHORN)
alarm.send("Alarm Header", "Alarm Body")
```

An alarm sends a notification throught the dashio mqtt server to registered phones. The ability to send alarms to specific phones, and the notification sound can be configured through the IoTDasboard app. Alarms are only available if you have an account registered on the dashio server and you send the the alarm through a dash connection.

#### Button

<img src="https://dashio.io/wp-content/uploads/2020/12/Buttons.jpeg" width="200" />

#### Button Group

<img src="https://dashio.io/wp-content/uploads/2020/12/ButtonGroup.jpeg" width="200" />

#### Direction

<img src="https://dashio.io/wp-content/uploads/2020/12/Direction.jpeg" width="200" />

#### Dial

<img src="https://dashio.io/wp-content/uploads/2020/12/Dial.jpeg" width="200" />

#### Event Log

<img src="https://dashio.io/wp-content/uploads/2020/12/EventLog.jpeg" width="200" />

#### Graph

<img src="https://dashio.io/wp-content/uploads/2020/12/Graph.jpeg" width="200" />

#### Knob

<img src="https://dashio.io/wp-content/uploads/2020/12/Knobs.jpeg" width="200" />

#### Label

<img src="https://dashio.io/wp-content/uploads/2020/12/Label.jpeg" width="200" />

#### Map

<img src="https://dashio.io/wp-content/uploads/2020/12/Mao.jpeg" width="200" />

#### Menu

<img src="https://dashio.io/wp-content/uploads/2020/12/Menu.jpeg" width="200" />

#### Menu

<img src="https://dashio.io/wp-content/uploads/2020/12/Menu.jpeg" width="200" />

#### Selector

<img src="https://dashio.io/wp-content/uploads/2020/12/Selector.jpeg" width="200" />

#### Slider

<img src="https://dashio.io/wp-content/uploads/2020/12/Slider.jpeg" width="200" />

#### Text Box

<img src="https://dashio.io/wp-content/uploads/2020/12/TextBox.jpeg" width="200" />

#### Time Graph

<img src="https://dashio.io/wp-content/uploads/2020/12/ToimeGraph.jpeg" width="200" />

### Connections

#### TCPConnection

#### MQTTConnection

#### DashConnection

#### BLEConnection

The BLEConnection is only supported on Linux systems and requires bluez and dbus to be installed. It has been developed with the RaspberryPi Zero W in mind.
The steps to get a Pi Zero to become a Device Server

* Install bluez and bluetooth:

```bash
sudo apt-get install bluetooth bluez
```

* Edit:

```bash
sudo nano /lib/systemd/system/bluetooth.service
```

Replace:

```bash
ExecStart=/usr/lib/bluetooth/bluetoothd

```

With:

```bash
ExecStart=/usr/lib/bluetooth/bluetoothd ----noplugin=sap
```

* Edit:

```bash
sudo nano /lib/systemd/system/bthelper@.service
```

Replace the [Service] segment with:

```bash
[Service]
Type=simple
ExecStartPre=/bin/sleep 2
ExecStart=/usr/bin/bthelper %I
ExecStartPost=sudo /etc/init.d/bluetooth restart
```

To use the BLEConnection it has to be imported explicitly:

```python
from dashio.bleconnection import BLEConnection
```

### Dash Server

### Advanced Architecture
