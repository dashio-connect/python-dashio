# Greenhouse Controller

Controls a greenhouse's heater, fan and lights from its temperature and humidity. You can monitor and adjust it from the **Dash** app.

The greenhouse is simulated, so the example runs on any computer. To control a real greenhouse, replace `simulator.py` with code that reads your sensor and switches your relays. The controller only calls `read()` and `set_outputs()`.

## Running it

```bash
python3 greenhouse.py
```

The first run writes `greenhouse.ini`.

- **Without a DashIO account:** the controller is available on your local network. In the **Dash** app, find it with "Find New Device" over TCP.
- **With a DashIO account:** add your username and password to the `[DASH]` section of `greenhouse.ini` and restart. The controller then also connects through the Dash server, so you can reach it from anywhere.

Settings changed in the app are saved to `greenhouse.ini`, so they survive a restart. That covers the target temperature, mode, maximum humidity, lights times and device name.

## What it does

- **Auto mode:**
  - The heater holds the target temperature, turning on 0.5°C below it and off 0.5°C above it.
  - The fan vents the greenhouse when it's 3°C over the target or the humidity is over its maximum.
  - The lights follow the on and off times.
- **Manual mode:** the Heater, Fan and Lights buttons switch the outputs directly.
- **Alarms:** sent for frost risk (below 4°C), overheating (above 35°C) and very high humidity (above 95%). An alarm is sent once when its condition starts, and logged when it clears.
- **Event log:** records every change, whether automatic or from the app.
- **Climate graph:** temperature and target on the left axis and humidity on the right axis, one point a minute. Temperature and target share one line of `[temperature, target]` arrays, and the app chooses their colors.

## What it shows

- **Layouts for each screen size.**
  - `make_controls()` creates the controls for a layout.
  - The layouts are in the `LAYOUTS` table, one for each number of columns.
  - `make_controls()` is called once for the controls the device uses, positioned for phones, and again for the fold-out and tablet layouts.
  - `generate_cfg64()` turns each set of controls into a layout, and `add_cfg64()` loads it for its column count.
  - Phones (1 column) get three views. Fold-out phones (2 columns) get one view two columns wide, with the climate and controls on the left and the history on the right. Tablets (3 columns) get one view three columns wide.
- **TCP and Dash connections together**, from one device.
- **Dash server storage:** `storage_enable()` keeps the time graph and event log history on the Dash server. You can export it with the `dashio_data_exporter` utility, for example:

  ```bash
  dashio_data_exporter -u USERNAME -p PASSWORD -d DEVICE_ID -c graph -t TGRPH -n 7 -f csv -o
  ```

  The device ID is in `greenhouse.ini`.
- **Keeping the app's layout up to date:** the **Dash** app only fetches a new layout when the device's cfgRev changes. The layouts are built each time the controller starts, so `update_config_revision()` saves the CFG's hash from `get_cfg_hash()` with cfgRev in `greenhouse.ini`, and increases cfgRev when the hash changes.
- **A Schedular** runs the control loop every 5 seconds and adds graph points every minute.
- **A lock**, because messages from the app arrive on the device thread while the control loop runs on the Schedular thread.
- **Knob, Menu and Slider feedback:**
  - The target knob's dial shows the current temperature, beside the target it sets.
  - The Greenhouse Settings menu holds controls that are changed less often. Its parent is `PROV`, so it appears in the app's device provisioning menu instead of on a view.
  - The maximum humidity slider's bar shows the current humidity against the limit.
