#!/bin/python3
import time
import argparse
import signal
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
    # Catch CNTRL-C signel
    global SHUTDOWN
    signal.signal(signal.SIGINT, signal_cntrl_c)

    args = parse_commandline_arguments()
    print("Connecting to server: {}".format(args.server))
    print("       Connection ID: {}".format(args.connection))
    print("       Control topic: %s/%s/%s/control", args.username, args.connection, args.device_id)
    print("          Data topic: %s/%s/%s/data", args.username, args.connection, args.device_id)

    device = dashio.DashDevice(args.connection, args.device_id, args.device_name)
    dash_conn = dashio.DashConnection(args.username, args.password)
    dash_conn.add_device(device)

    my_map = dashio.Map("MAP1")
    my_map.title = "A cool map"
    myloc = dashio.MapLocation("James Peak", -45.237101516008835, 168.84818243505748)
    my_map.add_location(myloc)
    device.add_control(my_map)

    while not SHUTDOWN:
        time.sleep(1)

    device.close()


if __name__ == "__main__":
    main()
