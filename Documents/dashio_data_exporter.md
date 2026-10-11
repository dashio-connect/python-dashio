# How to Access Data from the DashIO Server

This guide explains how to export the data the Dash server stores for time graphs and event logs, using the `dashio_data_exporter` utility included with the dashio library.

The Dash server stores a control's data once the device has turned on storage for it with `device.storage_enable()`, for example:

```python
device.storage_enable(dashio.ControlName.TGRPH, "temperature_graph")
```

## Prerequisites

- Python 3.11 or later
- The dashio library
- A DashIO account

## Installation

```bash
pip3 install dashio
```

This installs the `dashio_data_exporter` command. From a copy of the repository, you can also run it as `python3 utilities/dashio_data_exporter`.

## Basic Usage

```bash
dashio_data_exporter -u USERNAME -p PASSWORD -d DEVICE_ID -c CONTROL_ID [options]
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `-u`, `--username` | Your DashIO username |
| `-p`, `--password` | Your DashIO password |
| `-a`, `--shared-username` | For a device shared with you, the username of the account that shared it |
| `-d`, `--device_id` | The ID of the device |
| `-c`, `--control_id` | The ID of the control |
| `-t`, `--type` | Control type: `TGRPH` (time graph) or `LOG` (event log) (default: `TGRPH`) |
| `-n`, `--number_of_days` | Number of days of data to export, up to now (default: 1) |
| `-f`, `--format` | Output format: `raw` or `csv` (default: `raw`) |
| `-s`, `--screen` | Write the output to the screen |
| `-o`, `--outfile` | Write the output to file(s) |

`-t` also accepts `MAP`, but map data isn't exported yet and produces no output.

## Examples

### Time Graph Data

```bash
dashio_data_exporter -u myusername -p mypassword -d mydevice -c mygraph -t TGRPH -n 3 -s
```

This exports 3 days of time graph data for the device's control and shows it on the screen.

### Event Log Data

```bash
dashio_data_exporter -u myusername -p mypassword -d mydevice -c mylog -t LOG -f csv -o
```

This exports a day of event log data as CSV and saves it to a file.

### A Device Shared With You

```bash
dashio_data_exporter -u myusername -p mypassword -a ownerusername -d theirdevice -c theirgraph -t TGRPH -s
```

Log in with your own username and password, and give the username of the account that shared the device with `-a`.

## Output File Naming

With the `-o` option, files are named:

- Time graphs: `[device_id]_TGRPH_[control_id]_[line_id].[format]`, a file for each line.
- Event logs: `[device_id]_LOG_[control_id].[format]`

## Output Formats

### Raw Format

The raw format keeps the tab separated structure the server sends:

```text
[device_id]  [control_type]  [control_id]  [data...]
```

### CSV Format

For time graphs, a file for each line:

```text
# [device_id], TGRPH, [control_id], [line_id], [line_name], [line_type], [line_color], [line_axis]

Timestamp, Value
[timestamp], [value]
[timestamp], [value]
...
```

For event logs:

```text
# [device_id], LOG, [control_id]
Timestamp, color, lines
[timestamp], [color], [line 1], [line 2]...
...
```
