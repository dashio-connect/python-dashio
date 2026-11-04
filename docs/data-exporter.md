# Exporting data from the Dash server

`dashio_data_exporter` exports the time graph and event log history the Dash server keeps for a device, to the screen or to files. It's installed with the library.

The server keeps a control's history once the device has turned on storage for it ([storage.md](storage.md#on-the-dash-server)):

```python
device.storage_enable(dashio.ControlName.TGRPH, "tg1")
```

## Usage

```sh
dashio_data_exporter -u USERNAME -p PASSWORD -d DEVICE_ID -c CONTROL_ID [options]
```

Or `python3 -m dashio.utilities.dashio_data_exporter`.

| Option | |
|---|---|
| `-u`, `--username` | Your Dash username |
| `-p`, `--password` | Your Dash password |
| `-a`, `--shared-username` | For a device shared with you, the username of the account that shared it |
| `-d`, `--device_id` | The device's ID |
| `-c`, `--control_id` | The control's ID |
| `-t`, `--type` | `TGRPH` (time graph, the default) or `LOG` (event log). `MAP` is accepted, but map data isn't exported yet |
| `-n`, `--number_of_days` | Days of history, up to now. Default 1 |
| `-f`, `--format` | `raw` (the default) or `csv` |
| `-s`, `--screen` | Write it to the screen |
| `-o`, `--outfile` | Write it to files, named as [below](#files) |

## Examples

Three days of a time graph, on the screen:

```sh
dashio_data_exporter -u myusername -p mypassword -d mydevice -c tg1 -t TGRPH -n 3 -s
```

A day of an event log, as CSV in a file:

```sh
dashio_data_exporter -u myusername -p mypassword -d mydevice -c log1 -t LOG -f csv -o
```

A device shared with you: log in as yourself, and give the account that shared it with `-a`:

```sh
dashio_data_exporter -u myusername -p mypassword -a ownerusername -d theirdevice -c tg1 -t TGRPH -s
```

## Files

With `-o`, the files are named:

- time graphs: `[device_id]_TGRPH_[control_id]_[line_id].[format]`, a file for each line;
- event logs: `[device_id]_LOG_[control_id].[format]`.

## Formats

`raw` keeps the tab separated messages the server sends:

```text
[device_id]  [control_type]  [control_id]  [data...]
```

`csv` writes a file for each time graph line:

```text
# [device_id], TGRPH, [control_id], [line_id], [line_name], [line_type], [line_color], [line_axis]

Timestamp, Value
[timestamp], [value]
...
```

and for an event log:

```text
# [device_id], LOG, [control_id]
Timestamp, color, lines
[timestamp], [color], [line 1], [line 2]...
...
```
