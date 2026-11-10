# The Device

A `Device` is your IoT device as the Dash app sees it: its controls, its layouts and its settings. It runs in its own thread, answers the app, and sends control values out through its connections ([connections.md](connections.md)).

## Starting

```python
device = dashio.Device("Greenhouse", "gh-7f3a", "Greenhouse", store=dashio.DashStore("greenhouse.db"))
tcp = dashio.TCPConnection()
tcp.add_device(device)
dash = dashio.DashConnection(username, password)
dash.add_device(device)

device.add_control(dial)
```

| Parameter | Default | |
|---|---|---|
| `device_type` | | The same for every device running this code, e.g. `"TempSensor"`. The app uses it to find devices and match layouts |
| `device_id` | | Unique to this device, e.g. a UUID or MAC address |
| `device_name` | | What the app shows. The user can change it if you let them ([below](#provisioning-from-the-dash-app)) |
| `cfg_dict` | None | Layouts to load: `{1: phone_cfg64, 3: tablet_cfg64}`, or one decoded layout. See [layouts.md](layouts.md#loading-layouts) |
| `context` | The shared `zmq.Context.instance()` | The ZMQ context the device and its connections talk over |
| `store` | None | A [DashStore](storage.md) for time graph, event log and map history |
| `certificates` | None | [DeviceCertificates](connections.md#device-certificates), to log in to the Dash server with the device's own certificate |

`device.close()` stops the device. It leaves the shared ZMQ context running, for other devices and connections.

## Controls

| Method | |
|---|---|
| `add_control(control)` | Adds a control. Controls in a loaded layout are added for you |
| `get_control(control_type, control_id)` | The device's control, e.g. `get_control(dashio.ControlName.KNOB, "aKNB")` |
| `remove_control(control)` | Removes a control |
| `is_control_loaded(control_type, control_id)` | Whether the device has the control |
| `storage_enable(control_type, control_id)` | Has the Dash server keep a TimeGraph's, EventLog's or Map's history. See [storage.md](storage.md) |

When an app connects, it asks for the state of every control. The device answers with its name, then the controls' values, packaged into a few `PKG` messages rather than one message each. Controls that are only in Menus and ButtonGroups are left out: their values are sent when the Menu or ButtonGroup is opened ([layouts.md](layouts.md#menus-buttongroups-and-the-provisioning-menu)).

## Provisioning from the Dash app

The app's provisioning menu lets the user change the device's settings: its name, WiFi, Dash server login, and your own settings in a [Menu in the provisioning menu](layouts.md#menus-buttongroups-and-the-provisioning-menu). Set a callback for each setting the device lets the user change. Setting one tells the app the device has it.

Each callback receives the message from the app, split on tabs, and returns whether it took the change (the name callback returns the new name). The device then confirms it to the app.

```python
def name_changed(msg):
    save_setting("name", msg[2])
    return msg[2]


def dash_login(msg):
    dash.set_connection(msg[2], msg[3])
    save_setting("dash", (msg[2], msg[3]))
    return True


device.set_name_callback(name_changed)
device.set_dashio_callback(dash_login)
```

| Method | The app sends | |
|---|---|---|
| `set_name_callback(callback)` | `msg[2]`: the name | Return the new name. The device answers requests for its name with or without one |
| `set_wifi_callback(callback)` | `msg[2]`: country code, `msg[3]`: SSID, `msg[4]`: password | Return True if it took them |
| `set_dashio_callback(callback)` | `msg[2]`: username, `msg[3]`: password | The Dash server login. Return True if it took them |
| `set_tcp_callback(callback)` | `msg[2]`: port | Return True if it took it |
| `set_mqtt_callback(callback)` | The MQTT settings | Return True if it took them |

Each has an `unset_..._callback()` that clears it, and stops offering the setting.

## Reset and factory reset

```python
def reset(msg):
    if len(msg) > 2 and msg[2] == "FRST":
        clear_saved_settings()  # A factory reset
    threading.Timer(1.0, restart).start()  # So the reply reaches the app first


device.set_reset_callback(reset)
```

`set_reset_callback(callback)` lets the user reset the device from the app. The device replies to the app, as the protocol requires, then calls the callback, which should reset the device, e.g. after a short delay so the reply gets out. `msg[2] == "FRST"` asks for a factory reset. `unset_reset_callback()` clears it.

## What the device offers the app

The layout's `deviceSetup` tells the app what the device supports: first its connections, added as you add the device to them (`BLE`, `TCP`, and `MQTT` for a DashConnection), then the settings it lets the user change, from the callbacks above (`NAME`, `WIFI`, `DASH`, `RST` and so on), e.g. `TCP,MQTT,NAME,DASH`. It's part of the layout, so work out cfgRev after adding the device's connections and callbacks ([layouts.md](layouts.md#keeping-cfgrev-up-to-date)).

`device.store_and_forward = True` adds `SAF`, which lets the user turn on the Dash server's store and forward for the device: the server keeps the app's messages until the device connects, and asks it for its values when it does. It's for devices that only connect now and then ([storage.md](storage.md#a-connection-thats-only-on-now-and-then)). With it on, the server also keeps a copy of the device's layout, so the app can show the device while it's offline: when the server doesn't have the current one, it asks the device for it when it connects, and the device sends it.

## Other settings

| Method or value | |
|---|---|
| `device_name` | The device's name. Setting it sends it to the app |
| `config_revision`, `inc_config_revision()` | cfgRev. See [layouts.md](layouts.md) |
| `number_of_device_views` | The number of DeviceViews in the layout generated from the controls |

## The Dash server

These need a [DashConnection](connections.md#dashconnection).

| Method | |
|---|---|
| `request_clock()` | Asks the Dash server for the time. The reply goes to `set_clock_callback(callback)`: `msg[3]` is the time in seconds since the epoch |
| `request_ota_build_number()` | Asks the server for the latest firmware build number. The reply goes to `set_ota_callback(callback)` |
| `request_ota(build_number, chunk_number)` | Asks the server for a block of firmware. The reply goes to the OTA callback |
| `set_store_sync_callback(callback)` | Called when each upload of the device's [DashStore](storage.md) to the server ends: True when the server has everything, False when it failed |
| `set_saf_end_callback(callback)` | With `store_and_forward`, called each time the device connects, once the messages the server kept for it have arrived (True), or when the server's SAF END doesn't come within `saf_end_timeout` seconds, 5 by default (False) ([storage.md](storage.md#a-connection-thats-only-on-now-and-then)) |

Each has an `unset_..._callback()`.
