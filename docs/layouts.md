# Layouts

A **layout** tells the Dash app how to show your device: its DeviceViews (screens), where each control goes, and how each looks. Your code creates the controls and gives them values (see [controls.md](controls.md)); the layout arranges them.

## How layouts work

- A layout is JSON, compressed and base64 encoded into a string called **CFG64**.
- The Dash app reports its screen size in **columns**: 1 for phones, 2 for fold out phones, 3 for tablets. A device can hold one layout for each.
- The app is sent the layout for its column count. If there isn't one, it gets the largest layout with fewer columns, or failing that the smallest. Each layout is sent whole, so layouts are never mixed. A device with only a 1 column layout shows it everywhere.
- With no layout loaded, the device sends a layout **generated from its controls**: their positions, DeviceViews and settings in your code. That's what [getting-started.md](getting-started.md) uses.
- The device tells the app which layout it has, its **layout ID**, and the app fetches the layout again only when that changes. By default the ID is a hash of the layout, so the app notices a changed layout by itself.
- The ID is the layout's revision, **cfgRev**, instead when the device has layouts for more than one column count (one hash can't describe them), with `Device(layout_hash=False)` for Dash app versions from before the hash, or with `use_cfg()`. Then **increase cfgRev every time you change a layout** ([below](#keeping-cfgrev-up-to-date)).

## Loading layouts

Load a layout for each column count, as a CFG64 string or a dict from `decode_cfg64()`:

```python
device = dashio.Device("PumpController", "pump1", "Pump", cfg_dict={1: phone_cfg64, 3: tablet_cfg64})

# Or after creating the device
device.add_cfg64(phone_cfg64, 1)
device.add_cfg64(tablet_cfg64, 3)
```

- **The controls in a layout that the device doesn't have are created.** Get them with `device.get_control(dashio.ControlName.KNOB, "aKNB")` to set their values and add callbacks.
- **Add the device's own controls before loading layouts**, if you create them in code. A control the device already has is kept, so the instances you add callbacks to are the ones the device uses.
- `Device(cfg_dict=...)` sets cfgRev from the layouts' own cfgRev.
- `cfg_dict` can also be a single decoded layout, loaded for 1 column.

| Device method | |
|---|---|
| `add_cfg64(cfg, column_no=1)` | Loads a layout, a CFG64 string or a decoded dict, for apps that report `column_no` columns. Raises `ValueError` naming every control ID over 7 characters, before any of the layout is loaded |
| `remove_cfg64(column_no)` | Removes the layout loaded for `column_no` |
| `get_generated_cfg_dict()` | The layout generated from the device's controls, as a dict. Export it with `encode_cfg64()` |
| `layout_id` | What the device reports: `#` and the 64-bit FNV-1a hash of the CFG64 the app downloads (16 hex digits), or cfgRev |
| `layout_hash` | True (the default) to report the hash when the device can. `Device(layout_hash=False)` reports cfgRev |
| `get_cfg_hash()` | A hash of the layouts the device sends, without cfgRev. See [below](#keeping-cfgrev-up-to-date) |
| `config_revision` | cfgRev. Set it, or `inc_config_revision()` adds 1 |
| `use_cfg64()`, `use_cfg()` | Send layouts to the app as CFG64 (the default) or as JSON |

### Layouts from older Dash apps

Layouts exported from older versions of the Dash app load too. Settings the app added later get their defaults: a TextBox's `captionMode` is `MSG`, a Knob's `dialMode` is `FOLLOW`, and a Slider's `barMode` comes from the older `barFollowsSlider`, or is `FOLLOW` without it.

Older layouts can have control IDs longer than 7 characters, which the library refuses. Decode the layout with `c64_decode`, shorten the IDs in the JSON, encode it again with `c64_encode`, and use the same IDs in your code.

## Making a layout

### In the Dash app

1. Run your device with its controls, as in [getting-started.md](getting-started.md). Give them positions and a DeviceView, or not: the app can place them.
2. In the app, edit the device's layout: move and resize the controls, add DeviceViews, Labels and Menus, and change colours and styles.
3. Export the layout from the app. It's a CFG64 string.
4. Load it into the device, as above. Increase cfgRev if the device reports cfgRev ([above](#how-layouts-work)).

Do it for each screen size you want to support: export from a phone for 1 column and from a tablet for 3.

### In code, with `generate_cfg64()`

`generate_cfg64(*controls, cfg_rev=1)` makes a CFG64 layout from controls, without a Device. Create the controls once for each layout, with that layout's positions, using the same IDs:

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
device.add_cfg64(dashio.generate_cfg64(*phone), 1)   # Phones and fold out phones
device.add_cfg64(dashio.generate_cfg64(*tablet), 3)  # Tablets

view, dial, knob = phone
knob.add_receive_message_callback(lambda msg: print("Target:", msg[3]))
```

- **Pass every control in the layout:** its DeviceViews, and the controls in its Menus and ButtonGroups. Alarms are skipped; they aren't part of a layout.
- Put each control on its DeviceView with `view.add_control(control)`, which sets the control's parent.
- The layout holds the controls' settings when it's generated. To change it, change the controls and generate it again.
- `cfg_rev` is only used when the layout is passed to `Device(cfg_dict=...)`.

To save a layout to a file, e.g. for firmware:

```python
view = dashio.DeviceView("main", "Main")
dial = dashio.Dial("temp", "Temperature", dial_max=40.0, units="°C", control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.3))
view.add_control(dial)

with open("layout.c64", "w", encoding="utf-8") as c64_file:
    c64_file.write(dashio.generate_cfg64(view, dial))
```

Load it again with `device.add_cfg64(open("layout.c64").read(), 1)`.

### Layouts for firmware

A layout works on any device with controls of the same types and IDs. Prototype the device in Python, design its layout in the app or with `generate_cfg64()`, and build it into the firmware: `c64_encode -f C` writes it as a C string.

### The command line utilities

| Command | |
|---|---|
| `c64_decode layout.c64` | Decodes a CFG64 layout to JSON, in `layout.json`. `-p` prints it too, `-o` names the file, `-c` leaves out empty keys |
| `c64_encode layout.json` | Encodes a JSON layout to CFG64, in `layout.c64`. `-f C` or `-f Python` formats it as a string for code, `-w` sets the line width |

`decode_cfg64(cfg)` and `encode_cfg64(cfg_dict)` do the same in Python.

## Keeping cfgRev up to date

Only needed when the device reports cfgRev rather than the layout hash ([above](#how-layouts-work)): the app then only fetches a layout again when cfgRev changes. Layouts built in code are rebuilt each time the program starts, so save the hash of the layouts with cfgRev, and increase cfgRev when the hash changes:

```python
cfg_hash = device.get_cfg_hash()
if cfg_hash != saved_cfg_hash:
    saved_cfg_rev += 1
    saved_cfg_hash = cfg_hash
    # Save saved_cfg_rev and saved_cfg_hash, e.g. in a settings file.
device.config_revision = saved_cfg_rev
```

Work out the hash after adding the device's connections and callbacks: they change `deviceSetup`, which is part of the layout ([device.md](device.md#what-the-device-offers-the-app)). The [greenhouse](../Examples/greenhouse) and [server monitor](../Examples/server_monitor) examples do this.

## Menus, ButtonGroups and the provisioning menu

- A **Menu** shows a popup list of TextBoxes, Sliders, Selectors and Buttons, added with `menu.add_control()`. The app sorts them by control ID: numbers, then upper case, then lower case.
- A **ButtonGroup** shows a popup grid of Buttons, added with `button_group.add_button()`.
- When the user opens one, the app asks the device for the values of the controls in it, and the device answers by itself. So their values aren't sent when the app connects, only when they're opened. A control on a DeviceView in any layout is always sent.
- A Menu whose parent is `"PROV"` appears in the app's **provisioning menu** for the device, rather than on a DeviceView. It suits settings that change rarely. It still needs a position:

```python
settings = dashio.Menu("setup", "Settings", control_position=dashio.ControlPosition(0.25, 0.25, 0.15, 0.1))
settings.parent_id = "PROV"
```

Pass a Menu and its controls to `generate_cfg64()` together. The greenhouse and server monitor examples have a Menu in the provisioning menu.

## Checklist

- [ ] Every control in the layout has the same type and ID as in your code, and the IDs are at most 7 characters.
- [ ] Controls created in code were added to the device before the layouts were loaded.
- [ ] Every control, DeviceView and Menu child was passed to `generate_cfg64()`, with a position.
- [ ] The device reports the layout hash (`device.layout_id` starts with `#`), or cfgRev went up.
