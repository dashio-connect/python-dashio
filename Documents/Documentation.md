
# DashIO Library Documentation

## Device

A Device is a collection of [Controls](#controls) and [DeviceViews](#deviceview) that represent an IoT device. The Device provides attributes and methods to communicate to a **Dash** app.

When the **Dash** app connects, it asks the device for the current state of all its controls. The device replies with its name, then the states packaged into PKG messages, a few messages instead of one for each control. Controls that are inside a Menu or ButtonGroup everywhere they appear are left out: their values are sent when the Menu or ButtonGroup is tapped. A control that is on a DeviceView in any layout is always included.

### Device Attributes

* *device_type : str.* The type of device (e.g. TempSensor, GPS...). If you have lots of devices that do the same thing keep this constant across your devices.
* *device_id : str.* A unique identifier for this particular device.
* *device_name : str.* The name for this device (E.g. GlassHouse, MothersZimmerFrame...).
* *cfg_dict : dict, optional.* A layout decoded with decode_cfg64, loaded for 1 column, or a dict of column number to layout, each a CFG64 string or decoded dict, e.g. `{1: phone_cfg64, 3: tablet_cfg64}`. cfgRev is set from the layouts. See [Layouts](#layouts), and [Helper Functions](#helper-functions) for tools to use the CFG64 text exported from the **Dash** app. By default None.
* *context : zmq.Context, optional.* The ZMQ context, by default the shared zmq.Context.instance().

### Device Methods

* *add_control(iot_control).* Add a control to the device.
* *get_control(control_type: ControlName, control_id: str).* Returns the control loaded into the device, e.g. `device.get_control(dashio.ControlName.KNOB, "aKNB")`.
* *remove_control(iot_control).* Removes the control from the device.
* *is_control_loaded(control_type: str, control_id: str).* Returns True if the control is loaded in the device.
* *use_cfg64().* Generate a CFG64 formatted CFG message.
* *use_cfg().* Generate JSON formatted CFG messages.
* *close().* Close the device.
* *storage_enable(control_type: ControlName, control_id: str).* Turn on Dash server storage for a TimeGraph, EventLog or Map, so the Dash server stores its data and sends it to the **Dash** app. Requires a DashConnection.
* *config_revision : int.* The cfgRev sent to the **Dash** app. The app only fetches a new CFG when cfgRev changes, so increase it whenever the CFG changes.
* *inc_config_revision().* Increase cfgRev by 1.
* *device_name : str.* The device name. Setting it sends the new name to the **Dash** app.
* *number_of_device_views : int.* The number of DeviceViews in the layout generated from the controls.
* *request_clock().* Request the time from the Dash server. The reply is passed to the clock callback.
* *request_ota_build_number().* Request the latest firmware build number from the Dash server. The reply is passed to the OTA callback.
* *request_ota(build_number, chunk_number).* Request a block of firmware from the Dash server. The reply is passed to the OTA callback.
* *add_cfg64(cfg, column_no=1).* Load a layout, as a CFG64 string or a dict from decode_cfg64, for **Dash** apps that report column_no columns. Controls in the layout that the device doesn't have are added. See [Layouts](#layouts).
* *remove_cfg64(column_no).* Remove the layout loaded for column_no.
* *get_generated_cfg_dict().* Returns the layout generated from the device's controls as a dict. Encode it with encode_cfg64() to export it.
* *get_cfg_hash().* Returns a hash of the CFG the device sends to Dash apps of every column count, without cfgRev. The **Dash** app only fetches a new CFG when cfgRev changes, so increase cfgRev whenever the CFG changes. Code that builds its layouts when it starts can save the hash with cfgRev and increase cfgRev when the hash changes. See the greenhouse and server monitor examples.
* *add_all_c64_controls(c64_dict, column_no=1).* Same as add_cfg64.

### Layouts

The **Dash** app reports its screen size in columns when it asks for a CFG: 1 for phones, 2 for fold out phones and 3 for tablets. A device can hold one layout for each column count, loaded with add_cfg64() or with the cfg_dict parameter of Device, e.g. `Device(device_type, device_id, device_name, cfg_dict={1: phone_cfg64, 3: tablet_cfg64})`.

The app is sent the layout for its column count. If there isn't one it is sent the largest layout with fewer columns, otherwise the smallest layout. Each layout is sent whole, so layouts are never mixed.

A layout is usually exported from the **Dash** app. A layout can also be generated from the controls' parameters: get_generated_cfg_dict() returns it, and it is sent to the app when no layouts are loaded. Export a generated layout with encode_cfg64(device.get_generated_cfg_dict()) to load it later as a column layout.

To create the layouts in code, build each one with generate_cfg64() from controls created with that layout's positions. Controls for different layouts are separate instances that share control IDs. The device keeps the controls already added to it, and adds controls it doesn't have from the first layout that defines them. See [generate_cfg64](#generate_cfg64controls-cfg_rev-int--1---str) for more examples.

```python
view1 = dashio.DeviceView("view1", "Main")

phone_button = dashio.Button("btn1", "Pump", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.2))
view1.add_control(phone_button)
phone = dashio.generate_cfg64(view1, phone_button)

tablet_button = dashio.Button("btn1", "Pump", control_position=dashio.ControlPosition(0.0, 0.0, 0.3, 0.3))
view1.add_control(tablet_button)
tablet = dashio.generate_cfg64(view1, tablet_button)

device = dashio.Device("PumpController", "pump1", "Pump", cfg_dict={1: phone, 3: tablet})
```

### Device Callback Methods

These callbacks are used to setup and configure connections by the **Dash** app. Setting these callbacks advertises to the **Dash** app that the connection can be modified.

* *set_wifi_callback(callback):* Set a callback function that is called when the DashIO app provides wifi provisioning information. The callback must return a Boolean indicating success.
* *unset_wifi_callback():* Clears the wifi callback.
* *set_dashio_callback(callback):* Set a callback function that is called when the DashIO app provides Dash server provisioning information.
* *unset_dashio_callback():* Clears the set Dash callback.
* *set_name_callback(callback):* Set a callback function that is called when the DashIO app provides Name provisioning information. The callback must return the new name. The device answers requests for its current name itself, with or without a name callback.
* *unset_name_callback():* Clears the set Name callback.
* *set_tcp_callback(callback):* Set a callback function that is called when the DashIO app provides TCP provisioning information.
* *unset_tcp_callback():* Clears the set TCP callback.
* *set_mqtt_callback(callback):* Set a callback function that is called when the DashIO app provides MQTT provisioning information.
* *unset_mqtt_callback():* Clears the set MQTT callback.
* *set_clock_callback(callback):* Set a callback function that is called when the Dash server sends the time, after request_clock().
* *unset_clock_callback():* Clears the clock callback.
* *set_ota_callback(callback):* Set a callback function that is called when the Dash server sends firmware information or a firmware block.
* *unset_ota_callback():* Clears the OTA callback.
* *set_reset_callback(callback):* Set a callback function that is called when the DashIO app asks the device to reset. The device replies to the app before calling it, as the protocol requires, so the callback should reset the device, e.g. after a short delay so the reply reaches the app.
* *unset_reset_callback():* Clears the reset callback.

## Controls

Controls are objects that represent actions and widgets in the DashIO application. All controls have a ControlID, Title, and TitlePosition. The ControlID should be a string that can uniquely identify that control per device. A ControlID can be at most 7 characters, as the **Dash** app requires. A longer ControlID raises a ValueError. The control Title is text that is displayed on the **Dash** app with the Control. The TitlePosition can be `TitlePosition.TOP`, `TitlePosition.TOPLEFT`, `TitlePosition.BOTTOM` (the default), or `TitlePosition.NONE`. Controls that are displayed have a `dashio.ControlPosition` that is composed of four size and position variables: x_position_ratio, y_position_ratio, width_ratio, height_ratio. The first two are position ratios that place the top left corner of the widget on the DeviceView. The last two are ratios that govern the size of the widget. The ratios are proportional to the size of the screen with the full size of the screen representing 1.0. All controls have a callback that is used to return messages from the **Dash** app. Controls on the **Dash** app can have a graphical duplicate that may have a different set of *Config* attributes. This is achieved by adding another ControlConfig with add_config(ControlConfig).

Controls have two main types of attributes.

1) *Config Attributes*. These attributes define the look and placement of the control. They are used to generate the config information sent to the **Dash** app when it issues a CFG command to the device, these are set in *init*.

2) *Messaging Attributes*. Setting these attributes send messages to the **Dash** app controlling the visible appearance of the control.

When controls are instantiated they create a ControlConfig for the layout generated from the controls. A control can appear more than once in that layout, e.g. on two DeviceViews, by creating another ControlConfig for it and adding it with add_config(ControlConfig). Layouts for different screen sizes are held by the Device, see [Layouts](#layouts).

### DeviceView

A DeviceView provides a control that describes appearance and style of the group of controls that are displayed on this DeviceView by the **Dash** app.

#### DeviceView Attributes

All of these attributes are config attributes.

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device. Each control inherits the DeviceViews Control settings.
* *title : str.* The controls title.
* *style : DeviceViewStyle.* The style of the DeviceView.
* *icon : Icon.* The Icon representing the DeviceView.
* *color : Color.* The color of the DeviceView.
* *share_column : Boolean.* If there is space, another DeviceView can share the column, by default True.
* *num_columns : int.* How many columns wide the DeviceView is, from 1 to 3, by default 1.
* *control_title_box_color : Color.* Title box color for controls.
* *control_title_box_transparency : int.* Title box transparency for controls.
* *control_color : Color*, Set the control color, default is Color.WHITE_SMOKE.
* *control_border_color : Color.* Set the border color, default is Color.WHITE_SMOKE.
* *control_background_color: Color.* Set the background color, default is Color.BLACK.
* *control_title_font_size : int.* Size of the title font, default is 16.
* *control_max_font_size : int.* Set the maximum font size, default is 20.
* *control_background_transparency : int.* Background transparency of controls, default is 0.
* *num_grid_columns : int.* The num of grid columns on the edit view.
* *num_grid_rows : int.* The num of grid rows on the edit view.
* *user_tappable_color : Color.* The color of items in controls that the user can tap, e.g. the button on a TimeGraph or a Menu icon. If not set, the control color is used.

#### DeviceView Methods

* *add_control(Control) :* Add a control to the device view
* *from_cfg_dict(Dict) :* Instantiate a DeviceView as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

### Alarm

```python
alarm = dashio.Alarm("alarm1")
alarm.send("Alarm Header", "Alarm Body")
```

An alarm sends a notification through the dashio mqtt server to registered phones. The ability to send alarms to specific phones, and the notification sound can be configured through the **Dash** app. Alarms are only available if you have an account registered on the **Dash** server and you send the the alarm through a dash connection.

#### Alarm Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device

#### Alarm Methods

* *send(self, header: str, body: str).* Sends an alarm with *header* and *body*.

### Audio Visual Display

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/av_display.jpeg" width="200"/>

An Audio Visual display allows the IoT Device to send a URL to the DashIO app to play or display
the contents of the URL. The URL may be a video or audio stream or an image.

#### Audio Visual Display Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device
* *title : str, optional.* Title of the control, by default "A Audio visual display"
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM

#### Audio Visual Display Message Attributes

* *url : str.* The url of the media to play.

### Button

A Button allow the user to send a simple action, informing the IoT device that the button has been pressed. The button state (on or off color) is not changed by tapping the button. After the IoT device receives a message containing the action, it sends a message back to the control in the dashboard to set the button state.

A Button control behaves as both as a momentary push button for user input and as a status indicator to provide feedback from the IoT device.

The control can change the button icon and text of the control on the **Dash** app.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Buttons.jpeg" width="200"/>

```python
button1 = Button("button1", "Button Title")
button1.btn_state = ButtonState.ON
button1.send_button(ButtonState.ON, Icon.UP, "Going Up")
button1.send_button(ButtonState.OFF, Icon.DOWN, "Going Down")
```

#### Button Config Attributes

* *control_id : str*. A unique identity string. The identity string must be a unique string for each control per device.
* *title : str*. A short title for the button, by default "A Button".
* *title_position : TitlePosition*. Can be TitlePosition.BOTTOM, TitlePosition.TOP, TitlePosition.TOPLEFT or TitlePosition.NONE, by default TitlePosition.BOTTOM.
* *text : str*. The text that appears on the Button.
* *button_enabled : boolean*. True allows the app to send button events. False disables button pushes.
* *style : ButtonStyle*. Can be ButtonStyle.BASIC, ButtonStyle.HIGHLIGHT.
* *icon_name : Icon*. Set the icon for the button, by default Icon.NONE.
* *off_color : Color*. Set the off color.
* *on_color : Color*. Set the on color.
* *control_position : ControlPosition*. Set the size and position of the button on a DeviceView.

#### Button Messaging Attributes

When these attributes are set the button control will transmit the new value to connected **Dash** apps.

* *text : str*. The text that appears on the Button.
* *icon_name : Icon*. Set the icon for the button.
* *btn_state : ButtonState.* Set the state of the button.

#### Button Methods

* *send_button(btn_state: ButtonState, btn_icon: Icon, text: str) :* Updates the button state, button icon and text
* *from_cfg_dict(cfg_dict: dict):*  Instantiate a Button as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Button Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Button Group

A ButtonGroup control is used to present a popup grid or table of Button controls. The Button Group does not receive or send messages directly, but presents Button controls that send and receive messages.

When the user taps the ButtonGroup, the **Dash** app asks the device for the current values of its buttons. The device replies automatically, with the state of each control whose parent is the ButtonGroup, packaged into one PKG message (several for a large ButtonGroup). Receive callbacks added to the ButtonGroup are still called.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/ButtonGroup.jpeg" width="200"/>

#### Button Group Config Attributes

* *control_id : str.* A unique identity string. The identity string must be a unique string for each ButtonGroup per device
* *title: str.* A short title for the button group
* *style : ButtonGroupStyle*. Can be ButtonGroupStyle.BASIC, ButtonGroupStyle.HIGHLIGHT.
* *text : str.* The text that appears on the ButtonGroup
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM
* *icon : Icon*. Set the icon for the button.
* *grid_view : Bool*. Defaults to True.


#### Button Group Methods

* *add_button(Button):* Add a button to the ButtonGroup
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a ButtonGroup as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

### Color Picker

A ColorPicker control is used to select a color to send to the IoT device. The Color Picker may
be shown as either a spectrum or as a color wheel and brightness slider.

#### Color Picker Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Color Picker".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM
* *style : ColorPickerStyle, optional.* The style of color picker to use, by default ColorPickerStyle.WHEEL.
* *send_only_on_release: Boolean.* Send only on release, by default True

#### Color Picker Message Attributes

* *color_value : str.* Send the color. The color_value must be in #rrggbb format.

#### Color Picker Methods

* *send_color_rgb(red: int, green: int, blue: int).* Format the red, green, blue values as #RRGGBB and send to any connected **Dash** apps.
* *color_to_rgb(color_value: str).* Return a tuple of RED, GREEN, BLUE integers from the given string in #RRGGBB format.
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a ColorPicker as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Color Picker Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Direction

A Direction display is used to graphically present a decimal direction value from 0 to 360 degrees. The Direction display receives messages from the IoT device to set the direction indicator position.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Direction.jpeg" width="200" />

#### Direction Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Control".
* *control_position : ControlPosition, optional* The position of the control on a DeviceView, by default None
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *style : DirectionStyle, optional.* The Direction style to display, by default DirectionStyle.DEG.
* *pointer_color : Color, optional.* Color of the pointer, by default Color.GREEN.
* *units : str, optional.* Units to be displayed with the value, by default "".
* *precision : [type], optional.* Precision of the value displayed, by default Precision.OFF
* *calibration_angle : int, optional* Calibration angle offset, by default 0.


#### Direction Message Attributes

* *direction_value : float.* The direction to send to the **Dash** app.
* *direction_text : str.* Text to be displayed on the direction control.

#### Direction Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Direction as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Direction Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Dial

A Dial display is used to present a numerical value in a graphical circular dial. The Dial display receives messages from the IoT device to set the dial position.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Dial.jpeg" width="200" />

#### Dial Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Dial".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *dial_min : float, optional.* Minimum dial position, by default 0.0.
* *dial_max : float, optional.* Maximum dial position, by default 100.0.
* *red_value : float, optional.* Position for red part of dial, by default 75.0.
* *dial_fill_color : Color, optional.* Dial fill color, by default Color.RED.
* *pointer_color : Color, optional.* Pointer color, by default Color.BLUE.
* *number_position : DialNumberPosition, optional.* Position of the number on the dial, by default DialNumberPosition.LEFT.
* *show_min_max : bool, optional.* True to show min max, by default False.
* *style : DialStyle, optional.* Dial style, by default DialStyle.PIE.
* *precision : Precision, optional.* Precision of the displayed number, by default Precision.OFF.
* *units : str, optional.* Units of the dial position, by default "".


#### Dial Message Attributes

* *dial_value : float.* The value to display on a dial.

#### Dial Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Dial as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Dial Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Event Log

An Event Log display is used to present time stamped events or alarms from  IoT devices. The most recent event is shown on the control and a scrollable list of events is presented when the Event Log is tapped by the user.

Each event contains the time of the event, the color to display the event and the text to display.

Multiple IoT devices can be shown on a single Event Log control.

The **Dash** app asks for the events since the last one it has. They can be kept by the device, in the EventLog's ring buffer, or stored on the Dash server by calling `device.storage_enable(dashio.ControlName.LOG, control_id)`.

#### Event Data

An EventData object is a single event used by the EventLog.

##### Attributes

* *lines : str.* Max 25 lines long. Each line is separated by '\n'
* *color : Color, optional.* The color to display this data point on the **Dash** app, by default Color.WHITE

#### Event Log Config Attributes

* *control_id : str.* A unique identifier for this control
* *title : str, optional.*  The title for this control will be displayed on the **Dash** app, by default "An Event Log".
* *title_position : TitlePosition, optional.* The position of the title, by default TitlePosition.BOTTOM
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None
* *max_log_entries : int, optional.* The EventLog uses a ring buffer for data entries this defines the number entries before over writing older entires, by default 100.

#### Event Log Methods

* *add_event_data(self, data: EventData):.* Add a data point to the log and send it to any connected **Dash** app.
* *send_latest_data().* Send the latest log entry to any connected **Dash** app.
* *send_event(event: EventData).* Send an event without adding it to the log.
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate an EventLog as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

### Chart

A Chart display is used to present graphical data on the DashIO Dashboard, where the data is a series of vertical (Y) axis data. The data is evenly spaced on the horizontal (X) axis. The IoT device sends a message for each line in the Chart. The data may be shown as lines, bars or peak values.

Each line can be independently added, deleted or changed by the IoT device. Multiple IoT devices can add lines to a single Chart control.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Chart.jpeg" width="200" />

```python
import dashio
chart = dashio.Chart("chart1", "Chart")
cl_line = dashio.ChartLine("Random Data", dashio.ChartLineType.LINE, color=dashio.Color.BLUE)
data = np.random.normal(0, 20, 100)
cl_line.data = data.tolist()
chart.add_line("line_1", cl_line)
```

#### Chart Line

A ChartLine object represents a line for a Chart.

##### Chart Line Attributes

* *name : str.* The name of the line.
* *line_type : ChartLineType. optional.* The format of the line: LINE, BAR, SEGBAR, PEAKBAR, DELETE. Sending ChartLineType.DELETE removes the line from the chart. Default ChartLineType.LINE.
* *color : Color, optional.* The color of the ChartLine. Default Color.BLACK.
* *right_axis : bool, optional.* If True use the right axis of graph. Default False
* *data. : list.* The list containing data values to display on the Chart.

#### Chart Config Attributes

* *control_id : str.* A unique identifier for this control.
* *title : str, optional.* The title for this control will be displayed on the **Dash** app, by default "A Chart".
* *title_position : TitlePosition, optional.* The position of the title, by default TitlePosition.BOTTOM.
* *x_axis_label : str, optional.* The label for the X axis, by default "".
* *x_axis_min : float, optional.* Min value for the X axis, by default 0.0.
* *x_axis_max : float, optional.* Max value for the X axis, by default 100.0.
* *x_axis_num_bars : int, optional.* Number of bars on the X axis, by default 5.
* *x_axis_labels_style : ChartXAxisLabelsStyle, optional.* The style for the X axis, by default ChartXAxisLabelsStyle.ON.
* *y_axis_label : str, optional.* The label for the Y axis,, by default "".
* *y_axis_min : float, optional.* Min value for the Y axis, by default 0.0.
* *y_axis_max : float, optional.* Max value for the Y axis, by default 1000.0.
* *y_axis_num_bars : int, optional.* Number of bars on the Y axis, by default 5.
* *y_axis_label_rt : str, optional.* Label for the Y axis right side, by default ''.
* *y_axis_min_rt. : float, optional.*  Min value for the right Y axis, by default 0.0.
* *y_axis_max_rt : float, optional.* Max value for the right Y axis, by default 1000.0.
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.

#### Chart Methods

* *add_line(self, line_id: str, cline: ChartLine).* Add a line to the Chart.
  * *line_id: str.* An unique identifier for this Chart.
  * *cline: ChartLine.* The Line to add to the Chart.
* *send_chart().* Sends the Chart data to IoT dashboard.
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Chart as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

### Knob

A Knob allow the user to send numerical values to the IoT device when the user drags the knob to a new position. A Knob control contains a user adjustable knob surrounded by a simple dial indicator. The dial can be controlled independently of the knob or can be used to provide feedback to the user from the IoT Device.

The IoT device may send messages to update both the dial and knob positions.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Knobs.jpeg" width="200"/>

#### Knob Config Attributes

* *control_id : str.* A unique identifier for this control.
* *title : str, optional.* The title for this control will be displayed on the **Dash** app, by default "A Knob".
* *title_position : TitlePosition, optional.* The position of the title, by default TitlePosition.BOTTOM.
* *knob_style : KnobStyle, optional.* The Knob style, by default KnobStyle.NORMAL.
* *dial_min : float, optional.* Minimum dial value, by default 0.0.
* *dial_max : float, optional.* Maximum dial value, by default 100.0.
* *red_value : float, optional.* The value where the red starts, by default 75.0.
* *show_min_max : bool, optional.* Whether to show the min amd max values, by default False.
* *send_only_on_release : bool, optional.* Have the **Dash** app send values either on release or during movement, by default True.
* *dial_mode : DialMode, optional.* DialMode.FOLLOW has the **Dash** app set the dial to match the knob value. DialMode.MSG makes the dial controlled by messages. By default DialMode.FOLLOW.
* *dial_color : Color, optional.* Color of the Dial, by default Color.BLUE.
* *knob_color : Color, optional.* Color of the Knob, by default Color.RED.
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.

#### Knob Message Attributes

* *knob_value : float.* Sends the value of the knob.
* *knob_dial_value : float.* Sends the value for the dial on the knob.

#### Knob Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Knob as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Knob Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Label

A Label is a simple control to add structure to your layout on the dashboard. Labels do not transfer information with IoT devices.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Label.jpeg" width="200"/>

#### Label Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.*  Title of the control, by default "A Label".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *color : Color, optional.* Color of the label, by default Color.WHITE.
* *style : LabelStyle, optional.* Style of label to be displayed, by default LabelStyle.BASIC

#### Label Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Label as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

### Map

A Map display is used to plot positions on a map. The Map display receives messages from the IoT Device that contain latitude and longitude to mark the position. Additional data, such as speed and altitude may also be included and shown on the Map display.

Multiple IoT devices can be shown on a single Map.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Map.jpeg" width="200"/>

#### Map Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.*  Title of the control, by default "A Map".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.

#### Map Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Map as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.
* *add_location_to_track(self, location: MapLocation, track_id: str)* Adds a location to a track and sends it.
* *send_location(self, location: MapLocation, track_id: str = "")* Sends a location.

### Menu

A Menu control is used to present a popup table of user adjustable controls and is ideal for presenting a list of IoT device setup parameters. The Menu does not receive messages directly, but presents a list of other controls (sub-controls) that send and receive messages of their own.

Controls that can be included in a Menu control are Text Boxes, Sliders, Selectors and Buttons. The **Dash** app sorts the controls in a menu by their control IDs: numbers, then uppercase, then lowercase.

When the user taps the Menu, the **Dash** app asks the device for the current values of its controls. The device replies automatically, with the state of each control whose parent is the Menu, packaged into one PKG message (several for a large Menu). Receive callbacks added to the Menu are still called.

A Menu whose parent is `"PROV"` appears in the **Dash** app's device provisioning menu instead of on a DeviceView, which suits settings that are changed less often:

```python
settings = dashio.Menu("setup", "Settings", control_position=dashio.ControlPosition(0.25, 0.25, 0.15, 0.1))
settings.parent_id = "PROV"
```

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Menu.jpeg" width="200"/>

#### Menu Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Menu"
* *style : MenuStyle*. Can be MenuStyle.BASIC, MenuStyle.HIGHLIGHT.
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *text : str, optional.* Menu text, by default "A Menu with Text".
* *icon_name : Icon, optional.* Menu icon, by default Icon.MENU.

#### Menu Methods

* *add_control(control).* Add a control to the menu.
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Menu as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

### Selector

A Selector control is used to present a popup list of options that the user can select from. When a Selector is tapped, the DashIO Dashboard presents the list of text options to the user to make their selection from. The user can tap on an option to select is and the index of the selected option will be sent to the IoT device.

Feedback to the user of the dashboard is achieved when the IoT device responds to the selection message. The dashboard updates the Selector control check box with this value.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Selector.jpeg" width="200"/>

#### Selector Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Selector".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *selection : list.* Optional. The selection list.

#### Selector Message Attributes

* *position : int.* Sends the position index of the selected Text.

#### Selector Methods

* *add_selection(text: str):.* Add the text to the selection list.
* *set_selected(selected_text: str).* Set the selector to the selected text.
* *send_selection(position: int).* Send the selection list. position is optional.
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Selector as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Selector Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Slider

A Sliders allow the user to send a numerical values to the IoT device when the user drags the slider to a new position. The slider also includes bar graph that can be set by the IoT device. The bar graphs can be controlled independently of the slider or can be used to provide feedback to the user from the IoT Device.

The IoT device may send messages to update both the bar graph and the slider knob positions. The bar graph may set to have two bars.

The knob of the slider may be disabled so that the slider becomes a simple bar graph indicator.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/Slider.jpeg" width="200"/>

#### Slider Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Single Slider".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *bar_min : float, optional.* The min bar value, by default 0.0.
* *bar_max : float, optional.* The max bar vale, by default 1000.0
* *red_value : int, optional.* Bar red value, by default 750
* *show_min_max : bool, optional.* show min max, by default False.
* *slider_enabled : bool, optional.* Enable slider, by default True.
* *send_only_on_release : bool, optional.* Send only on release, by default True.
* *bar_mode : BarMode, optional.* BarMode.FOLLOW has the bar follow the slider. BarMode.MSG makes the bar controlled by messages. By default BarMode.FOLLOW.
* *bar_color : Color, optional.* The bar color, by default Color.BLUE.
* *knob_color : Color, optional.* The knob color, by default Color.RED.
* *bar_style : SliderBarStyle, optional.* The bar style, SliderBarStyle.SEG or SliderBarStyle.SOLID, by default SliderBarStyle.SEG.

#### Slider Message Attributes

* *bar1_value : float.* Sends the value of bar1.
* *bar2_value : float.* Sends the value of bar2. If this value is not set then only one bar is shown on the **Dash** app.
* *slider_value : float.* Sends the slider value.

#### Slider Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Slider as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Slider Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Table

The table control displays rows and columns of data with an optional header row.

#### Table Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Table Box".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *precision : Precision, optional.* precision, by default Precision.OFF
* *font_size : int, by default 12* The size of the font.
* *label_width_percent : int.* Label width as a percent.
* *columns : int.* Number of table columns including the label.
* column_headings : List, The headings for the table columns.

#### Table Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a Table as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.
* *add_table_row(table_row: TableRow)* Add row to the table and send it.
* *update_table_row(table_row: TableRow, row_number: int) -> int:* Update the row at row_number. If it doesn't exist then append it. Returns the index of the updated row.
* *clear_row(self, row_number: int):* Clears the row at row_number.
* *clear_table(self):* Clears the table.

### Text Box

A Text Box control receives simple line text messages from the IoT device to display on the DashIO Dashboard. The text may optionally be plain text, reformatted as a number or, when the text is ISO8601 date/time, it may be formatted to a date/time that is easy to read.

The Text Box may also allow the user to input text. Touching the control will present the user with a keyboard where the user can enter text. When the Send button on the keyboard is pressed, the message will be sent to the IoT device.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/TextBox.jpeg" width="200"/>

#### Text Box Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A Text Box".
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *text : str, optional.* Text for the textbox, by default "".
* *text_align : TextAlignment, optional.* Text alignment, by default TextAlignment.LEFT.
* *text_format : TextFormat, optional.* Format of the text, by default TextFormat.NONE.
* *units : str, optional.* Units, by default "".
* *precision : Precision, optional.* precision, by default Precision.OFF
* *keyboard_type : Keyboard, optional.* Keyboard type for the textbox, by default Keyboard.ALL.
* *close_keyboard_on_send : bool, optional.* Set to True to close keyboard on close, by default True.
* *replace : dict, optional.* Text substitutions, for TextFormat.SUBS: each key in the text is replaced with its value, e.g. `{"0": "OK", "1": "Fault"}`. By default None.
* *caption_mode : CaptionMode, optional.* default CaptionMode.MSG. CaptionMode.MSG is for when the caption receives messages to be displayed.
CaptionMode.SENT is when the caption shows the last message the user has entered.

#### Text Box Message Attributes

* *text : str.* Sends text to the **Dash** app.
* *color : Color.* The text color, by default Color.WHITE.
* *caption : str.* Sends the caption text to the **Dash** app.
* *caption_color : Color.* The caption color, by default Color.WHITE

#### Text Box Methods

* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a TextBox as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

#### Text Box Callbacks

* *add_receive_message_callback(callback):* Add callback to handle the message from the **Dash** app. The callback receives a list formed by splitting the message from the **Dash** app on the tab character.

### Time Graph

A Time Graph display is used to present time-series graphical data on the DashIO Dashboard, where the data is a series of points containing the time on the horizontal axis and other data on the vertical axis. The IoT device sends messages for each line in the graph. Each message contains one or more data points and the DashIO Dashboard appends the incoming data to create a data series that can be presented, panned and zoomed by the user. The data may be shown as lines, bars or blocked areas.

Each line can be independently added, deleted or changed by the IoT device. Multiple IoT devices can add lines to a single Time Graph control.

The **Dash** app asks for the data since the last point it has. The data can be kept by the device, in each TimeGraphLine's ring buffer, or stored on the Dash server by calling `device.storage_enable(dashio.ControlName.TGRPH, control_id)`.

<img src="https://raw.githubusercontent.com/dashio-connect/python-dashio/master/Documents/TimeGraph.jpeg" width="200"/>

#### Data Point

A DataPoint is a time stamped data point for a Time Graph Line.

##### Data Point Attributes

* *data.* A data point can be an int, float, or boolean, or string representing a number. The time that the DataPoint is made is recorded with the data point.

#### Time Graph Line

A TimeGraphLine for a TimeGraph control.

##### Time Graph Line Attributes

* *name : str | list[str], optional.* The name of the line, by default "". For a line of arrays, a list with a name for each value in the array, e.g. ["Temperature", "Target"].
* *line_type : TimeGraphLineType, optional.* Which line type to use, by default TimeGraphLineType.LINE.
* *color : Color | None, optional.* The color of the line, by default Color.BLACK. None lets the **Dash** app choose, e.g. for a line of arrays.
* *max_data_points : int, optional.* The data is stored in a ring buffer this sets the ring buffer size, by default 60
* *break_data : bool, optional.* If true draws the line with breaks between missing data, by default False
* *right_axis : bool, optional.* If true use the right axis, by default False.

##### Time Graph Line Methods

* *add_data_point(data_point):.* Adds a data point to the TimeGraphLine: an int, float, str, DataPoint, or DataPointArray. A list is added as a DataPointArray, e.g. [21.3, 20.0] for a line of arrays.

#### Time Graph Config Attributes

* *control_id : str.* An unique control identity string. The control identity string must be a unique string for each control per device.
* *title : str, optional.* Title of the control, by default "A TimeGraph"
* *control_position : ControlPosition, optional.* The position of the control on a DeviceView, by default None.
* *title_position : TitlePosition, optional.* Position of the title when displayed on the **Dash** app, by default TitlePosition.BOTTOM.
* *y_axis_label : str, optional.* Label for the Y axis, by default "Y axis".
* *y_axis_min. : float , optional.* Min value for the Y axis, by default 0.0.
* *y_axis_max : float, optional.* Max value for the Y axis, by default 1000.0.
* *y_axis_num_bars : int, optional.* The number of bars to display on the graph, by default 5.
* *y_axis_label_rt : str, optional.* Label for the Y axis right side, by default ''.
* *y_axis_min_rt. : float, optional.*  Min value for the right Y axis, by default 0.0.
* *y_axis_max_rt : float, optional.* Max value for the right Y axis, by default 1000.0.

#### Time Graph Methods

* *add_line(line_id: str, gline: TimeGraphLine).* Adds a TimeGraphLine to the TimeGraph.
  * line_id : str. A unique to the graph line id
  * gline : TimeGraphLine. The line to add
* *send_data():.* Sends the latest data to the **Dash** app.
* *from_cfg_dict(cls, cfg_dict: dict):*  Instantiate a TimeGraph as defined from the dictionary. [See Helper Functions](#helper-functions) for tools to use the CFG64 txt generated by exporting a layout from the **Dash** app.

## Connections

To enable a device to communicate to the **Dash** app a connection is required. A device can have multiple connections and a connection can have multiple devices.

### DashConnection

The DashConnection sets up a connection to the **Dash** app via the **Dash** mqtt server. The **Dash** server has support for:

1. sending notifications
2. data storage for TimeGraphs, EventLogs, and Maps.
3. Sharing devices with other users.

The connection tells the **Dash** app when its devices go online and offline, so the app can reconnect sooner:

* When the connection is made, it sends ONLINE for each device, and for a device added later when it is added.
* close() sends OFFLINE for each device before disconnecting.
* If the connection is lost, e.g. the program stops unexpectedly, the Dash server publishes OFFLINE for the first device on the connection after offline_delay seconds, unless the connection is restored first. This is the connection's MQTT Last Will and Testament. An MQTT connection has a single will, so it only covers the first device, and it is set when the connection is made, so it doesn't cover devices added later.

The connection connects a moment after it is created, so add the devices straight after creating it.

#### DashConnection Attributes

* *username : str* username for the dash server connection.
* *password : str* password for the dash server connection.
* *host : str, optional.* The server name of the dash server host. Optional defaults to "dash.dashio.io"
* *port :int, optional.* Port number to connect to. Defaults to 8883,
* *use_ssl : bool, optional.* Whether to use ssl for the connection or not. default: True.
* *context : zmq.Context, optional.* The ZMQ context, by default the shared zmq.Context.instance().
* *offline_delay : int, optional.* If the connection is lost, the Dash server publishes OFFLINE for the first device after this many seconds, unless the connection is restored first. 0 publishes it straight away. Defaults to 10.
* *batch_delay : float, optional.* Messages for the same topic sent within this many seconds are published together, so a device updating several controls makes one publish to the Dash server instead of one for each. Alarms are published straight away. 0 publishes each message straight away. Defaults to 0.05.

#### DashConnection Methods

* *add_device(device: Device).* Adds a device to the connection.
* *close().* Sends OFFLINE for each device, then closes the connection.
* *set_connection(username: str, password)* Changes the connection to the DashIO server.
  * *username : str.* username for the server.
  * *password : str.* password for the server.

### TCPConnection

The TCPConnection sets up a connection to the **Dash** app within a local area network.

#### TCPConnection Attributes

* *ip_address : str, optional.* IP Address to use. Defaults to "\*". Only set this if you know which IP address to connect to on the local machine. The "\*" option will use all available addresses.
* *port : int, optional.* Port to use. Defaults to 5650.
* *use_zero_conf : bool, optional.* Use mDNS to advertise the connection. Defaults to True. This allows the **Dash** app to find the connection on the network.
* *context : zmq.Context, optional.* The ZMQ context, by default the shared zmq.Context.instance().

#### TCPConnection Methods

* *add_device(device: Device).* Adds a device to the connection.
* *close().* Closes the connection.

### BLEConnection

The BLEConnection is only supported on Linux systems and requires bluez and dbus to be installed. It has been developed with the RaspberryPi Zero W in mind.

#### BLEConnection Attributes

* *ble_uuid : str, optional.* The UUID used by the BLE connection, if None a UUID is generated.
* *context : zmq.Context, optional.* The ZMQ context, by default the shared zmq.Context.instance().

#### BLEConnection Methods

* *add_device(device: Device).* Adds a device to the connection.
* *close().* Closes the connection.

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
from dashio.ble_connection import BLEConnection
```

## Helper Functions

### **decode_cfg64(cfg: str) -> dict:**

Decodes and unzips a CFG64 text string generated by the **Dash** app when it exports a layout. Returns a dictionary.

### **encode_cfg64(cfg: dict) -> str:**

Encodes cfg dictionary into C64 string.

### **generate_cfg64(\*controls, cfg_rev: int = 1) -> str:**

Generates a CFG64 layout from controls, without needing a Device. Use it to build layouts in code, e.g. a layout for each screen size, and load each into a device with add_cfg64(cfg64, column_no). See [Layouts](#layouts).

* *\*controls.* Every control in the layout, including its DeviceViews and the controls in its Menus and ButtonGroups. Put each control on its DeviceView with `view.add_control(control)`, which sets the control's parent. Alarms are skipped, as they aren't part of a layout.
* *cfg_rev : int, optional.* The layout's cfgRev, by default 1. It is only used when the layout is passed to Device with cfg_dict, which sets the device's cfgRev from its layouts.

Returns the layout as a CFG64 string.

The layout holds each control's settings when generate_cfg64() is called, e.g. its position and colors. To change the layout, change the controls, or create new ones, and generate it again.

#### Example: save a layout to a file

```python
view = dashio.DeviceView("main", "Main")
dial = dashio.Dial("temp", "Temperature", dial_max=40.0, units="°C", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.3))
view.add_control(dial)

with open("layout.c64", "w", encoding="utf-8") as c64_file:
    c64_file.write(dashio.generate_cfg64(view, dial))
```

The file can be loaded with `add_cfg64(open("layout.c64").read(), 1)`, or decoded to JSON to inspect it with `c64_decode layout.c64`.

#### Example: a layout for each screen size

Create the controls once for each layout, with that layout's positions, using the same control IDs. The device uses one set of controls, so add those to the device before loading the layouts. That way the controls you attach callbacks to are the ones the device uses.

```python
def make_controls(num_columns, dial_position, knob_position):
    view = dashio.DeviceView("main", "Thermostat", num_columns=num_columns)
    dial = dashio.Dial("temp", "Temperature", dial_max=40.0, control_position=dashio.ControlPosition(*dial_position))
    knob = dashio.Knob("target", "Target", dial_max=40.0, control_position=dashio.ControlPosition(*knob_position))
    view.add_control(dial)
    view.add_control(knob)
    return view, dial, knob


phone = make_controls(1, (0.0, 0.0, 1.0, 0.4), (0.2, 0.45, 0.6, 0.4))
tablet = make_controls(3, (0.0, 0.0, 0.3, 0.6), (0.35, 0.0, 0.3, 0.6))

device = dashio.Device("Thermostat", "thermostat1", "Thermostat")
for control in phone:
    device.add_control(control)
device.add_cfg64(dashio.generate_cfg64(*phone), 1)  # Phones and fold out phones.
device.add_cfg64(dashio.generate_cfg64(*tablet), 3)  # Tablets.

view, dial, knob = phone
knob.add_receive_message_callback(lambda msg: print("Target:", msg[3]))
```

A Menu works the same way: pass the Menu and the controls added to it. A Menu whose parent is `"PROV"` appears in the **Dash** app's device provisioning menu, see [Menu](#menu).

#### Example: keep cfgRev up to date

The **Dash** app only fetches a new layout when the device's cfgRev changes. Layouts built in code are rebuilt each time the program starts, so save the CFG's hash with cfgRev and increase cfgRev when the hash changes:

```python
cfg_hash = device.get_cfg_hash()
if cfg_hash != saved_cfg_hash:
    saved_cfg_rev += 1
    saved_cfg_hash = cfg_hash
    # Save saved_cfg_rev and saved_cfg_hash, e.g. in a settings file.
device.config_revision = saved_cfg_rev
```

The [greenhouse](../Examples/greenhouse) and [server monitor](../Examples/server_monitor) examples use generate_cfg64() for each screen size, with a Menu in the provisioning menu, and keep cfgRev up to date.

### **get_control_from_config(control_type: str, control_id: str, cfg_dict: dict):**

Returns a control object instantiated from cfg_dict with the given control_type and control_id.

### **get_control_dict_from_config(control_type: str, control_id: str, cfg_dict: dict) -> dict:**

Returns a control config dictionary from cfg_dict with the given control_type and control_id.

### **load_all_controls_from_config(device, cfg_dict)**

Loads all the controls in cfg_dict into the given device, as a layout for 1 column. Same as device.add_cfg64(cfg_dict).
