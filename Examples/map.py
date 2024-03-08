"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import argparse
import signal
import time

import dashio

SHUTDOWN = False


def signal_cntrl_c(os_signal, os_frame):
    global SHUTDOWN
    SHUTDOWN = True


def parse_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        const=1,
        default=1,
        type=int,
        nargs="?",
        help="""increase verbosity:
                        0 = only warnings, 1 = info, 2 = debug.
                        No number means info. Default is no verbosity.""",
    )
    parser.add_argument("-s", "--server", help="Server URL.", dest="server", default="localhost")
    parser.add_argument(
        "-p", "--port", type=int, help="Port number.", default=1883, dest="port",
    )
    parser.add_argument(
        "-c", "--connection_name", dest="connection", default="NETWORK_TRAFFIC", help="IotDashboard Connection name"
    )
    parser.add_argument("-d", "--device_id", dest="device_id", default="00001", help="IotDashboard Device ID.")
    parser.add_argument("-n", "--device_name", dest="device_name", default="TestMap", help="IotDashboard Device name alias.")
    parser.add_argument("-u", "--username", help="MQTT Username", dest="username", default="")
    parser.add_argument("-w", "--password", help="MQTT Password", default="")
    parser.add_argument(
        "-l",
        "--logfile",
        dest="logfilename",
        default="/var/log/networkMQTT.log",
        help="logfile location",
        metavar="FILE",
    )
    args = parser.parse_args()
    return args


def main():
    # Catch CNTRL-C signal
    global SHUTDOWN
    signal.signal(signal.SIGINT, signal_cntrl_c)

    args = parse_commandline_arguments()
    print(f"Connecting to server: {args.server}")
    print(f"       Control topic: {args.username}/{args.device_id}/control")
    print(f"          Data topic: {args.username}/{args.device_id}/data")

    device = dashio.Device("Test Map", args.device_id, args.device_name)
    dash_conn = dashio.DashConnection(args.username, args.password)
    dash_conn.add_device(device)

    my_map = dashio.Map("MAP1", title="A cool map")
    myloc = dashio.MapLocation("-45.237101516008835", "168.84818243505748")
    my_map.send_location(myloc, "Mt James")
    device.add_control(my_map)

    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
