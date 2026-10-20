# DashIO

DashIO is the protocol between IoT devices, the **Dash** app and the Dash server. python-dashio implements the device side.

## Parties

**Dash app**:
The phone and tablet app that shows and controls devices.
_Avoid_: client

**Dash server**:
dashio.io's MQTT server, with its history storage and push notifications.
_Avoid_: broker, cloud

## Devices

**Device**:
A thing that talks DashIO and is shown in the Dash app. One program can run several devices.

**Device ID**:
The unique, fixed name of a device, used in every message and topic.
_Avoid_: serial, serial number

**Device type**:
The kind of product a device is, the same for every unit of it.
_Avoid_: model

**Device name**:
The user-editable name the Dash app shows for a device.
_Avoid_: label, title

**Device setup**:
The list in a CFG of the settings and connections a device lets the Dash app change, such as `NAME`, `WIFI` and `SAF`.
_Avoid_: capabilities, features

**Provisioning**:
The Dash app giving a device what it needs to join a network and the Dash server: Wi-Fi details, Dash server credentials, its device name. Usually over BLE, before the device has any other connection.
_Avoid_: onboarding, commissioning

**Intermittent device**:
A device that connects to the Dash server only now and then, e.g. on LTE to save power.
_Avoid_: sleepy device, LTE device

## Controls

**Control**:
One item a device shows in the Dash app, such as a Dial, TimeGraph or Menu.
_Avoid_: widget, element

**Control ID**:
A control's short name on its device, at most 7 characters.

**Control type**:
The protocol keyword for a kind of control, such as `DIAL` or `TGRPH`.

**Nested control**:
A control that appears only inside a Menu or ButtonGroup, its **parent**, and on no device view. Its state is sent when its parent is tapped, not in STATUS.
_Avoid_: menu-only control, child control

**Alarm**:
A notification from a device that the Dash server pushes to the user's phone.
_Avoid_: notification, push, alert

## Layouts

**CFG**:
The message a device sends to describe itself to a Dash app: its settings and one layout.
_Avoid_: config, configuration

**Layout**:
The arrangement of controls and device views for one column count. A device holds at most one layout per column count.
_Avoid_: CFG (for one layout), screen

**cfgRev**:
The number a device reports with its WHO so the Dash app knows when to fetch a new CFG.
_Avoid_: CFG version, config version

**Device view**:
A page of controls in the Dash app.
_Avoid_: view, page, screen

**Provisioning menu**:
The Dash app's menu for setting a device up, where Menus whose parent is `PROV` appear.
_Avoid_: settings menu, PROV menu

**Column count**:
How many columns the Dash app shows: 1 on a phone, 2 on a fold-out phone, 3 on a tablet.
_Avoid_: column number, columns

**C64**:
The compressed text encoding a CFG is shared in.
_Avoid_: cfg64 (as a concept)

## Connections

**Dash server connection**:
A device's MQTT connection to the Dash server.

**Local connection**:
Any connection to a Dash app that doesn't go through the Dash server: TCP, BLE or ZMQ.
_Avoid_: direct connection

**Control topic**:
The MQTT topic carrying messages to a device.
_Avoid_: inbound topic

**Data topic**:
The MQTT topic carrying messages from a device to the Dash app.
_Avoid_: outbound topic

**Announce topic**:
The MQTT topic carrying a device's messages to the Dash server itself, such as WHO, storage requests and history uploads.

**Watched**:
A device is watched while a Dash app has sent it CONNECT or WHO recently. Control updates go to the Dash server only while it is watched.
_Avoid_: app connected

**Offline**:
A device being unreachable for now, announced with `OFFLINE`.

**Device removal**:
Deleting a device from the Dash server, which is what `DISCONNECT` does.
_Avoid_: disconnect

**Planned disconnect**:
A device closing its own Dash server connection on purpose, e.g. an intermittent device after a history upload.

**STATUS**:
A device's reply giving the current state of every control that isn't a nested control.

**Package**:
One message bundling several others, `PKG` in the protocol.
_Avoid_: batch

## History

**Server storage**:
The Dash server keeping a TimeGraph, EventLog or Map's history, turned on with `STE`. The server is then the source of truth for that history.
_Avoid_: storage enable, SAF

**History request**:
The Dash app asking a TimeGraph, EventLog or Map for its past data.

**History upload**:
A device sending the Dash server the TimeGraph, EventLog and Map history it is missing, after reconnecting. SDU in the protocol.
_Avoid_: store and forward

**Store and forward**:
The Dash server keeping the latest message for each control, in both directions between the Dash app and an intermittent device, and passing it on when the other end connects. SAF in the protocol.
_Avoid_: message queue
