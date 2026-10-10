#!/usr/bin/env python3
"""Python Example to get device data from the DashIO server."""

import argparse
import time
import ssl
import socket
import datetime
import json
from dataclasses import dataclass
import shortuuid
import sys
import paho.mqtt.client as mqtt

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
dashboard_id: str = shortuuid.uuid()
control_topic: str = ""
device_id: str = ""
control_id: str = ""
control_type: str = ""
from_timestamp: str = ""
file_format: str = "raw"
out_to_file: bool = False
screen: bool = False
connect_failed: bool = False

times_up = 3


@dataclass
class ControlData:
    username: str
    device_id: str
    control_type: str
    control_id: str
    data: list[str]


def parse_commandline_arguments():
    """Handle commandline arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="DashIO Username", dest="username", default="")
    parser.add_argument("-a", "--shared-username", help="DashIO Shared By Username", dest="shared_by_username", default="")
    parser.add_argument("-p", "--password", help="DashIO Password", default="")
    parser.add_argument("-d", "--device_id", help="The DeviceID of the device to get the data for.", dest="device_id", default="")
    parser.add_argument("-c", "--control_id", help="The ControlID of the control on the device to get the data for.", dest="control_id", default="")
    parser.add_argument("-t", "--type", help="Type of control, either 'TGRPH', 'MAP', 'LOG'.", dest="control_type", default="TGRPH")
    parser.add_argument("-n", "--number_of_days", help="Number of days of data to get up to present time.", dest="num_days", type=int, default=1)
    parser.add_argument("-f", "--format", help="""Format of the output data, either 'raw' or 'csv'.""", dest="format", default="raw")
    parser.add_argument("-s", "--screen", help="""Write output to stdout""", dest="screen", action="store_true")
    parser.add_argument("-o", "--outfile", help="""Write output to file(s). The filename(s) are generated from the data.""", dest="out_to_file", action="store_true")
    args = parser.parse_args()
    return args


def on_connect(client, userdata, flags, reason_code, properties):
    """print connection result"""
    global connect_failed
    print("Connect code: ", str(reason_code))
    if reason_code.is_failure:
        connect_failed = True


def on_message(client, obj, msg):
    global times_up
    times_up = 3
    l_username, l_device_id, _ = msg.topic.split("/", 2)
    data = str(msg.payload, "utf-8").strip("\r\n\t")
    line_data = data.split("\n")

    for line in line_data:
        parse_line_data(l_username, l_device_id, line.strip("\r\n\t"))


def on_subscribe(client, userdata, mid, reason_codes, properties):
    """Get the data on subscribe event message"""
    msg = f"\t{device_id}\t{control_type}\t{control_id}\t{dashboard_id}\t{from_timestamp}\n"
    mqtt_client.publish(control_topic, msg)


def parse_line_data(rx_username: str, rx_device_id: str, line_data: str) -> None:
    fields = line_data.split("\t")
    if len(fields) < 4:
        return
    d_id, rx_control_type, rx_control_id, rx_dashboard_id, *rx_control_data = fields
    if d_id != device_id or rx_control_id != control_id or rx_dashboard_id != dashboard_id:
        return
    control_data = ControlData(rx_username, rx_device_id, rx_control_type, rx_control_id, rx_control_data)
    if rx_control_type == "TGRPH":
        parse_tgrph_data(control_data)
    elif rx_control_type == "MAP":
        pass
    elif rx_control_type == "LOG":
        parse_log_data(control_data)


def format_log_json_to_csv(log: str) -> str:
    """Convert the json to csv"""
    log_dict = json.loads(log)
    log_str = "{time}, {color}, ".format_map(log_dict)
    log_str += ", ".join(log_dict["lines"])
    return log_str


def parse_log_data(control_data: ControlData):
    """parse the LOG data."""
    line = ""
    if file_format == "raw":
        line = f"\t{control_data.device_id}\tLOG\t{control_data.control_id}\t"
        line += "\t".join(control_data.data)
        line += "\n"
        if screen:
            print(line)
    elif file_format == "csv":
        line = f"# {control_data.device_id}, LOG, {control_data.control_id}"
        line += "\nTimestamp, color, lines\n"
        line += "\n".join(format_log_json_to_csv(l_str) for l_str in control_data.data)
        if screen:
            print(line)
    else:
        return
    if out_to_file:
        # LOG entries are JSON, so unlike TGRPH there is no short id to put in the filename.
        filename = f"{control_data.device_id}_{control_data.control_type}_{control_data.control_id}.{file_format}"
        print("Writing to file: " + filename)
        with open(filename, "w", encoding="utf-8") as writer:
            writer.write(line)


def parse_tgrph_data(control_data: ControlData):
    """parse the TGRPH line"""
    line = ""
    if file_format == "raw":
        line = f"\t{control_data.device_id}\tTGRPH\t{control_data.control_id}\t"
        line += "\t".join(control_data.data)
        line += "\n"
        if screen:
            print(line)
    elif file_format == "csv":
        line_id, line_name, line_type, line_color, line_axis, *line_data = control_data.data
        line = f"# {control_data.device_id}, TGRPH, {control_data.control_id}, {line_id}, {line_name}, {line_type}, {line_color}, {line_axis}\n"
        line += "\nTimestamp, Value\n"
        line += "\n".join(line_data)
        if screen:
            print(line)
    else:
        return
    if out_to_file:
        filename = f"{control_data.device_id}_{control_data.control_type}_{control_data.control_id}_{control_data.data[0]}.{file_format}"
        print("Writing to file: " + filename)
        with open(filename, "w", encoding="utf-8") as writer:
            writer.write(line)


def main():
    """The Main"""

    args = parse_commandline_arguments()
    global control_id, device_id, from_timestamp, file_format, out_to_file, control_type, screen, times_up, control_topic

    control_id = args.control_id
    device_id = args.device_id
    file_format = args.format.lower()
    control_type = args.control_type.upper()
    out_to_file = args.out_to_file
    screen = args.screen

    timestamp = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=args.num_days)).replace(microsecond=0)

    from_timestamp = timestamp.isoformat()

    # Setup callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_subscribe = on_subscribe

    # Setup connection
    mqtt_client.tls_set(
        ca_certs=None,
        certfile=None,
        keyfile=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None,
    )
    mqtt_client.tls_insecure_set(False)
    mqtt_client.username_pw_set(args.username, args.password)

    # MQTT Topics to request and receive the data. A shared device's store is under the owner's username.
    device_owner = args.shared_by_username or args.username
    control_topic = f"{device_owner}/{device_id}/store/control"
    data_topic = f"{device_owner}/{device_id}/store/data"
    try:
        mqtt_client.connect("dash.dashio.io", 8883)
    except (socket.gaierror, ConnectionRefusedError) as error:
        print(f"Exiting, No connection to server: {error}")
        sys.exit(1)

    mqtt_client.subscribe(data_topic, 0)

    mqtt_client.loop_start()

    while times_up >= 0 and not connect_failed:
        time.sleep(1)
        times_up -= 1

    mqtt_client.loop_stop()
    if connect_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
