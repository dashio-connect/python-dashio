# How to Access Data from the DashIO Server

This guide explains how to retrieve data from the DashIO server for time graphs, maps, and logs using the utility `dashio_data_exporter` included in the dashio library package.

## Prerequisites

- Python 3
- DashIO library package

## Installation

```bash
pip3 install dashio
```

The data retrieval script is included as a utility in the dashio package.

## Basic Usage

```bash
python -m dashio.utilities.get_data -u USERNAME -p PASSWORD -d DEVICE_ID -c CONTROL_ID [options]
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `-u`, `--username` | Your DashIO username |
| `-p`, `--password` | Your DashIO password |
| `-d`, `--device_id` | The ID of the device to access |
| `-c`, `--control_id` | The ID of the control to access |
| `-t`, `--type` | Control type: `TGRPH` (time graph), `MAP`, or `LOG` (default: `TGRPH`) |
| `-n`, `--number_of_days` | Number of days of data to retrieve (default: 1) |
| `-f`, `--format` | Output format: `raw` or `csv` (default: `raw`) |
| `-s`, `--screen` | Display output to the screen |
| `-o`, `--outfile` | Write output to file(s) |

## Examples

### Retrieving Time Graph Data

```bash
python -m dashio.utilities.get_data -u myusername -p mypassword -d mydevice -c mygraph -t TGRPH -n 3 -s
```

This retrieves 3 days of time graph data for the specified device and control, displaying the output on screen.

### Saving Map Data to a File

```bash
python -m dashio.utilities.get_data -u myusername -p mypassword -d mydevice -c mymap -t MAP -f csv -o
```

This retrieves map data in CSV format and saves it to a file.

### Getting Log Data

```bash
python -m dashio.utilities.get_data -u myusername -p mypassword -d mydevice -c mylog -t LOG -s -o
```

This retrieves log data, displaying it on screen and saving it to a file.

## Output File Naming

When using the `-o` option, files are named using the pattern:
```
[device_id]_[control_type]_[control_id]_[line_id].[format]
```

## Understanding Output Formats

### Raw Format

The raw format preserves the original structure from the server with tab-separated values:
```
[device_id]  [control_type]  [control_id]  [data...]
```

### CSV Format

The CSV format converts time graph data to a more readable format:
```
# [device_id], TGRPH, [control_id], [line_id], [line_name], [line_type], [line_color], [line_axis]
Timestamp, Value
[timestamp], [value]
[timestamp], [value]
...
```
