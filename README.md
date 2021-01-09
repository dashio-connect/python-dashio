# dashio

A python library to connect to the IotDashboard app.

## Getting Started

See <https://github.com/dashio-connect/python-dashio>

$ cd Examples
$ python3 iot_monitor.py -s dash.dashio.io -p 8883 -u user -w password -c`hostname`

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
This guide covers the dashio python library. For information on the IoTDashboard phone app please see .....[TBD]
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

This device is discoverable by the app and you will be able to manually add the control to any of your existing pages. It would be nice to have IoTDashboard automagically setup a new page and place your control on the new page. To do that we need to add a few more lines of code:

```python
import dashio
import random
import time

device = dashio.dashDevice("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.tcpConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial", control_position=dashio.ControlPosition(0.24, 0.36, 0.54, 0.26))
device.add_control(first_dial_control)

page_dial = dashio.Page("aPageID", "A Dial")
page_dial.add_control(first_dial_control)
device.add_control(page_dial)

while True:
    dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

First we altered the instantiation of a Dial by including a control_position. This allows us to place the control at a set location. The added lines instantiated a Page control, which we than added the dial control. Finally we added the page to the device.

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

page_dial = dashio.Page("aPageID", "A Dial")
page_dial.add_control(first_dial_control)
device.add_control(page_dial)

def knob_event_handler(msg):
    first_dial_control.dial_value = float(msg[3])

aknob = dashio.Knob("aKNB", control_position=dashio.ControlPosition(0.24, 0.14, 0.54, 0.26))
aknbb.message_rx_event = knob_event_handler
page_dial.add_control(aknob)

while True:
    time.sleep(5)
```




### Controls

### Connections

### Dash Server

### Advanced Architecture

