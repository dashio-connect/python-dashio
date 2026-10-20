# CLAUDE.md

Notes for working on python-dashio, the Python library for the DashIO protocol and the **Dash** IoT app. It's published on PyPI as `dashio` and requires Python 3.11 or later.

## Repository

- `dashio/`: the library.
  - `device.py`: Device, layouts and CFG replies.
  - `dash_connection.py`: Dash server MQTT connection.
  - `dash_store.py`: `DashStore` (sqlite storage for TimeGraph, EventLog and Map data) and `SDUSession` (history upload to the Dash server).
  - `tcp_connection.py`, `zmq_connection.py`: the other connections.
  - `load_config.py`: `decode_cfg64`, `encode_cfg64`, `generate_cfg64`.
  - `iotcontrol/`: controls.
  - `utilities/`: the `c64_encode`, `c64_decode` and `dashio_data_exporter` commands.
- `tests/`: unittest/pytest tests.
- `Examples/`:
  - `ex01`–`ex06`: shown in the README. Keep the README snippets identical to these files.
  - `greenhouse/` and `server_monitor/`: full applications.
- `Documents/Documentation.md`: the library reference. Keep it in step with the code.
- `Documents/DashIO-Controls-V2.pdf` and `DashIO-Protocol-Definition-V5.pdf`: the authoritative protocol and controls references. They're git-ignored (`*.pdf`). Read them with `pypdf`; poppler isn't installed.

## Running tests and lint

- **The venv has a non-editable `dashio` installed, so add `PYTHONPATH=.`** or you test the installed copy:
  `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -q`
- **flake8 isn't in the venv, but CI runs it,** as `flake8 dashio tests` with max line length 260. Run it before every commit. Inserting tests in front of `if __name__ == '__main__':` has caused E303 blank line errors more than once.
- **tox** has `py311`–`py314` and `flake8` environments, and uses tox-uv. For example: `uvx --with tox-uv tox -e py313`.
- **Tests must not contact `dash.dashio.io`.** Create a `DashConnection` with `host="localhost"`.

## CI and releases

- **`.github/workflows/tests.yml`** runs one job per Python version, 3.11 to 3.14, plus a flake8 job.
- **`publish-to-pypi.yml`** builds on every push, but only uploads to PyPI when a tag is pushed.
- **Release steps:**
  1. Bump `version` in `pyproject.toml`.
  2. Run the tox matrix.
  3. Commit "Bump version to X.Y.Z".
  4. Create a lightweight tag `X.Y.Z`, with no `v`.
  5. Push `master`, then the tag.
  6. Check that PyPI has the version.
  7. Run `gh release create X.Y.Z --notes-file ...`. Use absolute links to the tag in the notes, because relative links don't work in a release body.
- **Version numbers:** breaking changes have gone in minor versions, e.g. 3.6.0 and 3.7.0.

## Protocol and library rules

- **Control IDs are at most 7 characters.** `Control.__init__` raises `ValueError` for longer IDs (`MAX_CONTROL_ID_LENGTH` in `constants.py`). The greenhouse and server monitor examples use longer descriptive names for their controls as dict keys, but the IDs sent to the app are short. Layouts the app exports already use short IDs.
- **cfgRev must change whenever the CFG changes.** The Dash app only fetches a new CFG when the device reports a different cfgRev. Code that builds its layouts at startup should save `device.get_cfg_hash()` with cfgRev and increase cfgRev when the hash changes, as the examples do.
- **Enum and style values written into a CFG are UPPER CASE by convention.** The app ignores case. Many enums still emit mixed or lower case values; only ColorPicker's `pickerStyle` was converted.
- **Layouts:**
  - The Device holds a layout for each column count the app reports: 1 for phones, 2 for fold out phones, 3 for tablets. They're loaded with `add_cfg64(cfg, column_no)` or `Device(cfg_dict={1: ..., 3: ...})`.
  - A layout is sent whole: the one for the app's column count, otherwise the nearest smaller, otherwise the smallest. The layout generated from the controls is only sent when none are loaded.
  - Each control has one list of config entries (`Control._configs`); there's no `column_no`.
  - Values a control owns, such as Dial and Knob min/max/redValue and Direction calAngle, come from `Control._cfg_overrides()` and are applied to every layout.
- **`generate_cfg64(*controls)`:**
  - Pass every control in the layout, including its DeviceViews and the controls in its Menus.
  - Add the device's own controls before loading layouts. Layouts passed to `Device(cfg_dict=...)` create new controls.
- **Menus:** a Menu whose `parent_id` is `"PROV"` appears in the app's device provisioning menu. It still needs a nominal position.
- **Receive callbacks can reply:** `Event.fire()` returns the handlers' string replies joined together, and the device sends them. This is how TimeGraph, EventLog and Map history requests are answered, and how custom callbacks reply.
- **DashConnection:**
  - It uses MQTT v5, and connects from its thread about a second after it's created, so add devices straight away.
  - It sends ONLINE for each device when connected, and for devices added later.
  - `close()` sends OFFLINE for each device.
  - Its Last Will is OFFLINE for the first device only, because an MQTT connection has a single will, with `offline_delay` (WillDelayInterval plus SessionExpiryInterval).
  - Control updates (messages to `ALL`) are only published while a Dash app is watching the device: a CONNECT or WHO on its control topic within `app_timeout` (default 120 s, twice the app's CONNECT interval; 0 = always), kept per device and cleared on disconnect. Replies, alarms, announce, and TGRPH/LOG/MAP are always published. Tests that expect broadcast publishes need `app_timeout=0` or a CONNECT through `_on_message()`.
  - Messages for the same topic are batched for `batch_delay` (default 0.05 seconds) into one publish, up to 4096 characters, as the firmware's LTE code does. Alarms aren't batched.
  - Reconnecting is left to paho's network thread (`connect_async` and `loop_start`), whose wait doubles after each failed attempt, up to `RECONNECT_MAX_DELAY`, and only resets after a successful login. The run loop only makes the first connection, and doesn't connect without a username and password. `set_connection()` stops paho's thread and connects again.
  - Announce messages are sent at QoS 1. LWT is best effort; the Dash server also has its own last-connected check.
- **`Device.close()` doesn't terminate the ZMQ context,** which is shared by default.
- **What the Dash server does with announce topic messages:**
  - `WHO`: registers or updates the device.
  - `DISCONNECT`: **removes the device** from the server. Never send it for going offline; that's `OFFLINE` on the data topic.
  - `STE`: turns on storage for a LOG, MAP or TGRPH control, only if it isn't on already.
  - `CLK`: replies `\t<device_id>\tCLK\tsrv_clk\t<epoch seconds>\n` on the control topic, which reaches `set_clock_callback()`.
  - `SEC`: `\t<device_id>\tSEC\tKEY\t<key>`, stores a device key (BLE security).
  - `DATA`: `OTA` and `SDU` only.
- **The Dash server is the source of truth for history.** For a control with `storage_enable()` (`Device._server_stored`), history requests are only answered when they come from a Dash server connection (`msg_from` starting `DASH:`), never over TCP, BLE or other local connections. Otherwise an app connected locally takes the device's history as complete and doesn't fetch the older history from the server. Live updates still go to every connection.
- **`DashStore` and history upload (SDU):** a port of the firmware's DashIO Storage Manager (`../zephyr-dashio-tally/port.md`, ESP-IDF port in `../dashesp/components/dashio_dsm`), using sqlite instead of a flash ring buffer.
  - `Device(..., store=DashStore(path))` gives every TimeGraph, EventLog and Map on the device the store (`control._store`). They record into it as well as their ring buffers, and answer the app's history requests from it.
  - The wire format must match the firmware byte for byte, as the Dash server is shared with it: the timestamp request, `controlInfo` order (lines, then tracks, then logs), `%.6f` floats, `T`/`F` booleans, unquoted LOG and MAP objects, and the FNV-1a hash (`%016x`) over the JSON. The golden vectors are in `tests/test_dash_store.py`.
  - The timestamp request goes to the announce topic when the device's control topic subscription succeeds (`send_store_request` command, after `send_announce`). The server's `DATA SDU REQUEST/ACK/NACK` arrive as normal device messages (`Device._data_rx`). All SDU messages from the device, the timestamp request and the UPDATE packets, go to the **announce** topic (the `ANNOUNCE` zmq topic, which only Dash server connections receive), because that's where the server handles `DATA` messages.
  - Unlike the firmware, a session sends from the server's timestamps for each line, track and log, not from the last ACK. Lines missing from the server's request aren't sent. TimeGraph breaks aren't stored.
  - The session runs on the device thread: the 10 second ACK timeout is checked by `SDUSession.poll()` in `Device.run()`, because zmq sockets aren't thread safe.
  - **The main use is devices that connect now and then,** e.g. on LTE to save power: `DashConnection(auto_connect=False)`, `connect()` on a schedule, and `disconnect()` from `device.set_store_sync_callback()`. The callback (`SDUSession.on_finished`) is called on every path that ends a sync, like the firmware's `finished_handler`, including no SDU REQUEST within `SDU_REQUEST_TIMEOUT` of the timestamp request. A new timestamp request abandons a session left from an earlier connection.
  - During a planned disconnect (after `disconnect()`, or before `connect()` with `auto_connect=False`), DashConnection drops device messages rather than publishing a backlog when it connects. The app always gets current values from the device; with SAF on, the server sends STATUS itself. Announce messages other than WHO and SDU requests (e.g. STE, CLK) are kept and published once connected. A lost connection still queues messages in zmq, as before, so always-on devices without a store don't lose graph points.
  - Don't confuse SDU with **SAF** (Store And Forward, the `SAF` keyword and the server's `SAFenabled` flag). SAF is a separate Dash server feature for devices that are only connected now and then: the server holds messages between the app and the device until the other end connects. It's a server setting (`SAFenabled`), not turned on by the WHO: `device.store_and_forward = True` adds `SAF` to `deviceSetup`, and the app turns it on and off on the server; with SAF on, the server sends the device a STATUS when it connects, to store the latest values.
- **`PKG` messages** (not in the protocol PDF): `\t<device_id>\tPKG\tJAOS\t<json>\n` packages several messages into one.
  - The payload is a compact JSON array of strings, each a message without its leading `\t<device_id>\t` and trailing `\n`.
  - `JAOS` is the only encoding.
  - A new package is started once a package's messages pass 1000 characters.
  - `dashio/package.py`'s `make_packages()` builds them.
  - `STATUS` replies send `NAME` as a normal message, then the controls' states packaged as `PKG`, like the C++ firmware.
  - `STATUS` leaves out controls that are inside a Menu or ButtonGroup **everywhere** they appear, in their own configs and every loaded layout. Their values are sent when the Menu or ButtonGroup is tapped, because the app asks every time. A control on a DeviceView in any layout must stay in `STATUS`, because STATUS doesn't know which layout the app has. This is `Device._menu_only_controls()`.
  - The device replies to `MENU` and `BTGP` (a Menu or ButtonGroup being tapped) with the state of every control whose parent is that Menu or ButtonGroup, packaged as `PKG`. The controls are found by `parentID`, in the controls and in the loaded layouts.
- **`deviceSetup`** is built by `Device._update_device_setup()`: the connections first (`BLE`, `TCP`, `MQTT` for a DashConnection, from `CONNECTION_SETUP_OPTIONS` by connection ID prefix, updated by `register_connection()`), then the settings from the callbacks (`NAME`, `WIFI`, `DASH` for `set_dashio_callback()`, `RST`, ...). Upper case, as the app writes them. The app's full list is `BLE,TCP,MQTT,NAME,WIFI,DASH,RST,FRST,SAF,BBE,APN,GNSS,OTA,CLK,FLMD`; there's no TCP port option. Connections change the CFG hash, so examples work out cfgRev after adding their connections. `numDeviceViews` is the number of `DVVW` entries.
- **Numbers in messages** are formatted by `format_value(value, digits)` in `control.py`.
  - Precision (Dial, Table) is the number of significant digits the app shows, rounded to the nearest: 62.37 shows as 60 with precision 1, 62 with 2, and 62.4 with 3. It's user settable in the app, so the device doesn't use it: controls with a precision setting always send 6 significant digits (`PRECISION_SIGNIFICANT_DIGITS`, the most the app shows) and the app formats the number to fit.
  - Controls without a precision get 5 significant digits, like the firmware's `%.5g`.
  - Very large or small numbers are sent in exponent notation (`%g`), values smaller than 1e-11 as 0, and `None` as `NA` (not available).
- **Factory reset:** `RST` with `msg[2] == "FRST"` is a factory reset. The reset callback receives the message.
- **Decided against:**
  - re-sending `STE` on reconnect, because the Dash server remembers storage settings
  - changing the MQTT QoS, which is fine as it is
  - `PROV` sub-IDs (`BBE`, `PLMN`, `APN`, `GNSS`), which are for LTE and BLE devices
- **Colours** in a CFG can be names, hex or index strings. The library writes index numbers, and `_get_color` reads names and numbers.

## Leave alone unless asked

- **BLE** (`ble_connection.py`): unfinished, Linux-only (needs dbus), and imported separately on purpose.
- **The modem connections** (`quectel_EG800Q.py`, `telit_LE910Q1.py`, `sim767x.py`, `lte_767x_connection.py`): unfinished, and not exported from `dashio`. Their LWT code never runs.

## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The default five labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
