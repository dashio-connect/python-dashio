# Server Monitor

Monitors a computer's CPU, memory, disk and network, shows its busiest processes, and sends alarms when it runs short of resources. Run it on a server, home lab machine or Raspberry Pi, and keep an eye on it from the **Dash** app.

## Running it

It needs [psutil](https://pypi.org/project/psutil/):

```bash
pip install psutil
python3 server_monitor.py
```

The first run writes `server_monitor.ini`.

- **Without a DashIO account:** the monitor is available on your local network. In the **Dash** app, find it with "Find New Device" over TCP.
- **With a DashIO account:** add your username and password to the `[DASH]` section of `server_monitor.ini` and restart. The monitor then also connects through the Dash server, so you can reach it from anywhere.

The device is named after the computer. Renaming it in the app, or changing an alarm level, is saved to `server_monitor.ini`.

To keep it running on Linux, run it as a systemd service.

## What it does

- **Dials:** CPU, memory and disk use. The red zone is the alarm level.
- **System table:** host, OS, IP address, uptime, CPUs, load average, memory, free disk space, and the hottest temperature sensor where psutil can read one. psutil can't read temperatures on macOS.
- **Busiest processes:** a table updated every 30 seconds.
- **Time graphs:**
  - CPU and memory, averaged over each minute, so short spikes aren't missed.
  - Network receive and send rates.
- **Alarms:** sent when a level is exceeded for long enough, after 5 minutes for CPU, 2 minutes for memory, or straight away for disk. Each alarm is sent once, and logged when usage drops back below its level.
- **Alarm Levels menu:** sets each alarm's level. Its parent is `PROV`, so it appears in the app's device provisioning menu instead of on a view. The sliders' bars show the current usage. A dial's red zone shows a new level after a restart, because the red zone is part of the layout. The restart increases cfgRev, so the app fetches the updated layout.

## What it shows

- **Layouts for each screen size.**
  - `make_controls()` creates the controls for a layout.
  - `generate_cfg64()` turns each set of controls into a layout, and `add_cfg64()` loads it for its column count.
  - Phones and fold-out phones (1 and 2 columns) get three views. Tablets (3 columns) get one view three columns wide.
- **TCP and Dash connections together**, from one device.
- **Dash server storage:** `storage_enable()` keeps the time graph and event log history on the Dash server. You can export it with the `dashio_data_exporter` utility, for example:

  ```bash
  dashio_data_exporter -u USERNAME -p PASSWORD -d DEVICE_ID -c usage_graph -t TGRPH -n 7 -f csv -o
  ```

  The device ID is in `server_monitor.ini`.
- **Tables**, with and without column headings, updated row by row with `update_table_row()`.
- **Keeping the app's layout up to date:** the **Dash** app only fetches a new layout when the device's cfgRev changes. The layouts are built each time the monitor starts, so `update_config_revision()` saves the CFG's hash from `get_cfg_hash()` with cfgRev in `server_monitor.ini`, and increases cfgRev when the hash changes.
- **Fewer messages:** dial values are only sent when they change.
- **A Schedular** runs the readings, table updates and graph points at their own intervals.
