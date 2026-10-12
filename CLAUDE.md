# CLAUDE.md

Notes for working on python-dashio, the Python library for the DashIO protocol and the **Dash** IoT app. It's published on PyPI as `dashio` and requires Python 3.11 or later.

## Repository

- `dashio/`: the library.
  - `device.py`: Device, layouts and CFG replies.
  - `dash_connection.py`: Dash server MQTT connection.
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
- `JMB_Test_Code/`: James's local test code, git-ignored. Includes `server_mon.py` and `db_notify_listener.py`.

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
  - Announce messages are sent at QoS 1. LWT is best effort; the Dash server also has its own last-connected check.
- **`Device.close()` doesn't terminate the ZMQ context,** which is shared by default.
- **`PKG` messages** (not in the protocol PDF): `\t<device_id>\tPKG\tJAOS\t<json>\n` packages several messages into one.
  - The payload is a compact JSON array of strings, each a message without its leading `\t<device_id>\t` and trailing `\n`.
  - `JAOS` is the only encoding.
  - A new package is started once a package's messages pass 1000 characters.
  - `dashio/package.py`'s `make_packages()` builds them.
  - `STATUS` replies send `NAME` as a normal message, then the controls' states packaged as `PKG`, like the C++ firmware.
  - `STATUS` leaves out controls that are inside a Menu or ButtonGroup **everywhere** they appear, in their own configs and every loaded layout. Their values are sent when the Menu or ButtonGroup is tapped, because the app asks every time. A control on a DeviceView in any layout must stay in `STATUS`, because STATUS doesn't know which layout the app has. This is `Device._menu_only_controls()`.
  - The device replies to `MENU` and `BTGP` (a Menu or ButtonGroup being tapped) with the state of every control whose parent is that Menu or ButtonGroup, packaged as `PKG`. The controls are found by `parentID`, in the controls and in the loaded layouts.
- **`deviceSetup`:** the app accepts `dash` or `dashio`. `numDeviceViews` is the number of `DVVW` entries.
- **Colours** in a CFG can be names, hex or index strings. The library writes index numbers, and `_get_color` reads names and numbers.

## Leave alone unless asked

- **BLE** (`ble_connection.py`): unfinished, Linux-only (needs dbus), and imported separately on purpose.
- **The modem connections** (`quectel_EG800Q.py`, `telit_LE910Q1.py`, `sim767x.py`, `lte_767x_connection.py`): unfinished, and not exported from `dashio`. Their LWT code never runs.

## Progress, October 2026

### Released in 3.6.2 (first PyPI release since 3.5.10)

- **Removed:** `MQTTConnection`, the action station, and Python 3.10.
- **MQTT v5:** DashConnection uses MQTT v5, with announce messages at QoS 1.
- **Layouts:** held by the Device for each column count, with `add_cfg64`, `remove_cfg64`, `get_generated_cfg_dict`, `generate_cfg64` and `get_cfg_hash`. `column_no` was removed from the controls.
- **Time graphs:** lines of arrays (`TimeGraphLine([...], color=None)`, and `add_data_point(list)`).
- **Fixes:**
  - The installed utility commands work; they moved into `dashio/utilities`.
  - Closing a Device no longer terminates the shared ZMQ context.
  - Layouts generated by the library can be loaded back (colours, ColorPicker).
  - Loading layouts for 2 and 3 columns works.
  - A Table can be created without headings.
  - `NAME` in an app layout's `deviceSetup` is recognised in any case.
  - DashControl and BLEControl can be added to a Device.
  - Exporter fixes, and shared devices with `-a`.
- **CI** tests Python 3.11 to 3.14 and uses Node.js 24 actions. The docs were reviewed against the PDFs.

### Released in 3.7.0

- **DashConnection:** ONLINE, OFFLINE and the Last Will, with `offline_delay`.
- **History replies:** devices answer history requests again. They hadn't since January 2023, because `Event.fire` discarded replies. The Map history crashes and track IDs were fixed.
- **Exports:** `EG800Q` and `Lte767xConnection` are no longer exported.

### Since 3.7.0, not released

- **README:** improved, with a Dash server example (`Examples/ex06.py`), badges and a utilities table.
- **`generate_cfg64`:** documented, with examples.
- **Device reset:** `device.set_reset_callback()` advertises `rst` and replies `RST` before calling the callback.
- **Name requests:** an empty `NAME` (a request for the current name) is always answered.
- **TCPConnection:** `TCPConnection(use_zero_conf=False).add_device()` no longer crashes.
- **Control IDs limited to 7 characters:** enforced, with all the tests and examples shortened, including the CFG64 embedded in `ex04`, `ex05_SIM767X` and `all_controls`. This is a breaking change.
- **The greenhouse lights times:** Date/Time text boxes, sent and read as ISO 8601 times such as `16:30:00+1300`.
- **Announce:** includes cfgRev. Without it, the app took the announce as cfgRev 0.
- **Menu and ButtonGroup taps:** answered with the state of their controls, packaged as `PKG`.
- **`STATUS` replies:** packaged as `PKG`, after the `NAME` message, without controls that are only inside Menus or ButtonGroups.

## Open items

- **Protocol gaps still open:**
  - history requests for the most recent *n* points
  - OTA progress to the app
  - the `tcp_port`, `ble`, `tcp` and `mqtt` options in `deviceSetup`. The library advertises `tcp` for changing the port, which is wrong.
  - the TCP and MQTT connection entries in the CFG
- `CaptionMode` and `DeviceViewStyle` are used by TextBox and DeviceView but aren't exported from `dashio`.
- `dashio_data_exporter -t MAP` produces no output. The exporter's wait for replies is only about 4 seconds.
- The server monitor example has no 2-column layout.
- There are `datetime.utcnow()` deprecation warnings. They're accepted for now.
- DashConnection retries connecting even without credentials, and its retry delay is reset after every failed login, so it doesn't back off.
- Map history only returns tracks that started after the requested time.
