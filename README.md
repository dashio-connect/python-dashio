# DashIO

[**DashIO**](http://dashio.io) - a python library to connect and display widgets on the **DashIO** app.

**Beta Testers**

We are currently looking for beta testers for our products. If you are interested in using and testing our app and a free DashIO account, please contact us at info@dashio.io


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

`pip3 install dashio`

## Guide

This guide covers the **DashIO** python library. For information on the [***DashIO***](https://dashio.io/dashboard) phone app please visit the website.

### Basics

So what is **DashIO**? It is a quick effortless way to connect your IoT device to your phone. It allows easy setup of controls such as Dials, Text Boxes, Maps, Graphs, Notifications..., from your Device. You can define the look and layout of the controls on your phone from your IoT device. There are three methods to connect to your phone tcp, mqtt, dash, and BLE. What's Dash then? Dash is a mqtt server with extra bits added in to allow you to send notifications, share your devices, and save your settings from your phone via the **DashIO** app.

Show me some code!

```python
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
tcp_con = dashio.tcpConnection()
tcp_con.add_device(device)
first_dial_control = dashio.Dial("FirstDial")
device.add_control(first_dial_control)

while True:
    dial_control.dial_value = random.random() * 100
    time.sleep(5)
```

This is about the fewest lines of code to get talking to the app. There is a lot happening under the hood to make this work. After the import we create a device with three attributes. These attributes describe the device to the app and allow you to distinguish one of your devices from another. The next two lines create a TCP connection and then add the device to the connection. The connection will be created with the default setting of port 5000 and will also advertise the service using zeroconf, also known as bonjour. This allows the **DashIO** app to find your device. After that we create a dial add it to the device and then every five seconds send a randomly generated dial value to the DashIO app.

This device is discoverable by the app. It would be nice to have the DashIO app automagically setup a new DeviceView and place your control on the new DeviceView. To do that we need to add a few more lines of code:

```python
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
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

The next piece of the puzzle to consider is how do we get data from the DashIO app? Lets add a Knob and connect it to the Dial:

```python
import dashio
import random
import time

device = dashio.Device("aDeviceType", "aDeviceID", "aDeviceName")
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

First we added a function that sets the dial value. Next we added a Knob control and set our new function to be called when it receives data from the DashIO app.
We also add it to the DeviceView and to the device. Now when the knob in the DashIO app is moved the dial is set to the same value.

### Controls

Controls are objects that represent actions and widgets in the DashIO application. All controls have a ControlID, Title, and TitlePosition. The ControlID should be a string that can uniquely identifiy that control per device. The control Title is text that is displayed on **DashIO** with the Contol. The TitlePosition can be either `TitlePosition.TOP`, `TitlePosition.BOTTOM`, or `TitlePosition.NONE`. Controls that are displayed have a `dashio.ControlPosition` that is composed of four size and position variables: x_position_ratio, y_position_ratio, width_ratio, height_ratio. The first two are position ratios that place the top left corner of the widget on the DeviceView. The last two are ratios that govern the size of the widget. The ratios are propertional to the size of the screen with the full size of the screen representing 1.0. All controls have a `message_rx_event` callback that is used to return messages from the **DashIO** app.

#### Alarm

```python
alarm = dashio.Alarm("alarm1_ID", description="An alarming alarm", sound_name=SoundName.SHIPHORN)
alarm.send("Alarm Header", "Alarm Body")
```

An alarm sends a notification throught the dashio mqtt server to registered phones. The ability to send alarms to specific phones, and the notification sound can be configured through the **DashIO** app. Alarms are only available if you have an account registered on the **DashIO** server and you send the the alarm through a dash connection.

#### Audio Visual Display

An Audio Visual display allows the IoT Device to send a URL to the DashIO app to play or display 
the contents of the URL. The URL may be a video or audio stream or an image

#### Button

A Button allow the user to send a simple action, informing the IoT device that the button has been pressed. The button state (on or off color) is not changed by tapping the button. After the IoT device receives a message containing the action, it sends a message back to the control in the dashboard to set the button state.

A Button control behaves as both as a momentary push button for user input and as a status indicator to provide feedback from the IoT device.

The IoT device may also change the button icon and text of the control.

<img src="https://dashio.io/wp-content/uploads/2020/12/Buttons.jpeg" width="200" />

```python
button1 = Button("button1_id", "Button Title")
button1.state = ButtonState.ON
button1.send_button(ButtonState.ON, Icon.UP, "Going Up")
button1.send_button(ButtonState.OFF, Icon.DOWN, "Going Down")
```

<ins>Attributes</ins>

* control_id : str
    a unique identity string. The identity string must be a unique string for each ButtonGroup per device
* title : str
    A short title for the button group
* text : str
    The text that appears on the ButtonGroup
* title_position : TitlePosition
    Can be TitlePosition.BOTTOM, TitlePosition.TOP, TitlePosition.OFF
* button_enabled : boolean
    True allows the app to send button events. False disables button pushes
* icon_name : Icon
    Set the icon for the button
* off_color : Color
    Set the off color
* on_color : Color
    Set the on color
* control_position : ControlPosition
    Set the size and position of the button on a DeviceView

<ins>Methods</ins>

* toggle_btn () :
    Toggles the button state
* send_button(btn_state, btn_icon, text) :
    Updates the button state, button icon and text

<ins>Callbacks</ins>

* message_rx_event(msg) : Returns msg from **DashIO** app

#### Button Group

A Button Group control is used to present a popup grid or table of Button controls. The Button Group does not receive messages directly, but presents Button controls that send and receive messages.

<img src="https://dashio.io/wp-content/uploads/2020/12/ButtonGroup.jpeg" width="200" />

<ins>Attributes</ins>

* control_id : str
    a unique identity string. The identity string must be a unique string for each ButtonGroup per device
* title: str
    A short title for the button group
* text : str
    The text that appears on the ButtonGroup

<ins>Methods</ins>

* add_button(Button)
    Add a button to the ButtonGroup

#### Color Picker

A Color Picker control is used to select a colour to send to the IoT device. The Colour Picker may 
be shown as either a spectrum or as a colour wheel and brightness slider.

#### Direction

A Direction display is used to graphically present a decimal direction value from 0 to 360 degrees. The Direction display receives messages from the IoT device to set the direction indicator position.

<img src="https://dashio.io/wp-content/uploads/2020/12/Direction.jpeg" width="200" />

#### Dial

A Dial display is used to present a numerical value in a graphical circular dial. The Dial display receives messages from the IoT device to set the dial position.

<img src="https://dashio.io/wp-content/uploads/2020/12/Dial.jpeg" width="200" />

#### Event Log

An Event Log display is used to present time stamped events or alarms from  IoT devices. The most recent event is shown on the control and a scrollable list of events is presented when the Event Log is tapped by the user.

Each event contains the time of the event, the color to display the event and the text to display.

Multiple IoT devices can be shown on a single Event Log control.

<img src="https://dashio.io/wp-content/uploads/2020/12/EventLog.jpeg" width="200" />

#### Graph

A Graph display is used to present graphical data on the DashIO Dashboard, where the data is a series of vertical (Y) axis data. The data is evenly spaced on the horizontal (X) axis. The IoT device sends a message for each line in the graph. The data may be shown as lines, bars or peak values.

Each line can be independently added, deleted or changed by the IoT device. Multiple IoT devices can add lines to a single Graph control.

<img src="https://dashio.io/wp-content/uploads/2020/12/Graph.jpeg" width="200" />

#### Knob

A Knob allow the user to send numerical values to the IoT device when the user drags the knob to a new position. A Knob control contains a user adjustable knob surrounded by a simple dial indicator. The dial can be controlled independently of the knob or can be used to provide feedback to the user from the IoT Device.

The IoT device may send messages to update both the dial and knob positions.

<img src="https://dashio.io/wp-content/uploads/2020/12/Knobs.jpeg" width="200" />

#### Label

A Label is a simple control to add structure to your layout on the dashboard. They do not transfer information with IoT devices.

<img src="https://dashio.io/wp-content/uploads/2020/12/Label.jpeg" width="200" />

#### Map

A Map display is used to plot positions on a map. The Map display receives messages from the IoT Device that contain latitude and longitude to mark the position. Additional data, such as speed and altitude may also be included and shown on the Map display.

Multiple IoT devices can be shown on a single Map.

<img src="https://dashio.io/wp-content/uploads/2020/12/Mao.jpeg" width="200" />

#### Menu

A Menu control is used to present a popup table of user adjustable controls and is ideal for presenting a list of IoT device setup parameters. The Menu does not receive messages directly, but presents a list of other controls (sub-controls) that send and receive messages of their own.

Controls that can be included in a Menu control are Text Boxes, Sliders, Selectors and Buttons.

<img src="https://dashio.io/wp-content/uploads/2020/12/Menu.jpeg" width="200" />

#### Selector

A Selector control is used to present a popup list of options that the user can select from. When a Selector is tapped, the DashIO Dashboard presents the list of text options to the user to make their selection from. The user can tap on an option to select is and the index of the selected option will be sent to the IoT device.

Feedback to the user of the dashboard is achieved when the IoT device responds to the  selection message. The dashboard updates the Selector control check box with this value.

<img src="https://dashio.io/wp-content/uploads/2020/12/Selector.jpeg" width="200" />

#### Slider

A Sliders allow the user to send a numerical values to the IoT device when the user drags the slider to a new position. The slider also includes bar graph that can be set by the IoT device. The bar graphs can be controlled independently of the slider or can be used to provide feedback to the user from the IoT Device.

The IoT device may send messages to update both the bar graph and the slider knob positions. The bar graph may set to have two bars.

The knob of the slider may be disabled so that the slider becomes a simple bar graph indicator.

<img src="https://dashio.io/wp-content/uploads/2020/12/Slider.jpeg" width="200" />

#### Text Box

A Text Box control receives simple line text messages from the IoT device to display on the DashIO Dashboard. The text may optionally be plain text, reformatted as a number or, when the text is ISO8601 date/time, it may be formatted to a date/time that is easy to read.

The Text Box may also allow the user to input text. Touching the control will present the user with a keyboard where the user can enter text. When the Send button on the keyboard is pressed, the message will be sent to the IoT device.

<img src="https://dashio.io/wp-content/uploads/2020/12/TextBox.jpeg" width="200" />

#### Time Graph

A Time Graph display is used to present time-series graphical data on the DashIO Dashboard, where the data is a series of points containing the time on the horizontal axis and other data on the vertical axis. The IoT device sends messages for each line in the graph. Each message contains one or more data points and the DashIO Dashboard appends the incoming data to create a data series that can be presented, panned and zoomed by the user. The data may be shown as lines, bars or blocked areas.

Each line can be independently added, deleted or changed by the IoT device. Multiple IoT devices can add lines to a single Time Graph control.

Graph data is stored in the dashboard.

<img src="https://dashio.io/wp-content/uploads/2020/12/ToimeGraph.jpeg" width="200" />

### Connections

#### TCPConnection

#### MQTTConnection

#### DashConnection

#### BLEConnection

The BLEConnection is only supported on Linux systems and requires bluez and dbus to be installed. It has been developed with the RaspberryPi Zero W in mind.
The steps to get a Pi Zero to become a Device Server

Install bluez and bluetooth:

```bash
sudo apt-get install bluetooth bluez
```

Edit:

```bash
sudo nano /lib/systemd/system/bluetooth.service
```

Replace:

```bash
ExecStart=/usr/lib/bluetooth/bluetoothd

```

With:

```bash
ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap
```

Edit:

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

Edit:

```bash
sudo nano /etc/bluetooth/input.conf 
```

Set:

```bash
LEAutoSecurity=false
```

To use the BLEConnection it has to be imported explicitly:

```python
from dashio.bleconnection import BLEConnection
```

### Dash Server

### Advanced Architecture
