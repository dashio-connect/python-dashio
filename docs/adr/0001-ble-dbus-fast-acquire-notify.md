# BLE talks to BlueZ through dbus-fast, with an AcquireNotify socket per phone

BLEConnection is a BlueZ GATT server written directly on dbus-fast. It sends to each phone through that phone's AcquireNotify socket, not by emitting `PropertiesChanged`. Only a socket per phone gives us replies to the phone that asked, and the MTU for each phone; `PropertiesChanged` sends every notification to every subscribed phone. S1 security encrypts for one phone at a time, so it depends on this too.

## Considered Options

- **dbus-python and PyGObject** (the 2020 prototype): dbus-python is marked inactive and PyGObject 3.52+ won't `pip install` on Raspberry Pi OS Bookworm.
- **bless** is built on dbus-next, which is abandoned. **bluez-peripheral** is only at a 0.2 alpha. Neither supports AcquireNotify.
- **`PropertiesChanged` notifications**: simpler, but they broadcast to every phone.

## Consequences

- **No useful back-pressure** (measured on Fedora 44, BlueZ 5.87, October 2026). The notify socket accepted a 640 KB burst in 0.09 s. The kernel queued it and delivered all of it, in order, at about 27 KB/s. So the connection writes straight to the socket without rate limiting, and a large burst delays the messages behind it. A timeout on a blocked write stays as a safety net.
- **BlueZ before late 2026 can close the wrong phone's notify socket** when another phone disconnects ([bluez#1452](https://github.com/bluez/bluez/issues/1452)). It didn't happen on 5.87. The connection disconnects a phone whose socket dies while it's still connected, so the phone reconnects.
- **iPhones need `[GATT] Client = false`** in `/etc/bluetooth/main.conf`. Otherwise bluetoothd reads the iPhone's protected Device Information, pairing fails, and BlueZ disconnects the phone 2 s later. The library can't set this, so it warns when the setting is missing.
- **The oldest supported BlueZ is 5.66** (Raspberry Pi OS Bookworm).
