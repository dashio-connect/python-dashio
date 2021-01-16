#!/bin/python3
import time
import argparse
import signal
import dashio
import psutil
import logging

def get_network_rx_tx():
    data = psutil.net_io_counters()
    return data.bytes_recv / 1024, data.bytes_sent / 1024


shutdown = False


def signal_cntrl_c(os_signal, os_frame):
    global shutdown
    shutdown = True

def init_logging(logfilename, level):
    log_level = logging.WARN
    if level == 1:
        log_level = logging.INFO
    elif level == 2:
        log_level = logging.DEBUG
    if not logfilename:
        formatter = logging.Formatter("%(asctime)s, %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(log_level)
    else:
        logging.basicConfig(
            filename=logfilename,
            level=log_level,
            format="%(asctime)s, %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    logging.info("==== Started ====")


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
    parser.add_argument("-n", "--device_name", dest="device_name", default="SystemMon", help="IotDashboard Device name alias.")
    parser.add_argument("-u", "--username", help="mqtt Username", dest="username", default="")
    parser.add_argument("-w", "--password", help="MQTT Password", default="")
    parser.add_argument("-l", "--logfile", dest="logfilename", default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args


def main():
    # Catch CNTRL-C signel
    global shutdown
    signal.signal(signal.SIGINT, signal_cntrl_c)

    no_datapoints = 60
    args = parse_commandline_arguments()
    init_logging(args.logfilename, args.verbose)

    logging.info("Connecting to server: %s", args.server)
    logging.info("       Connection ID: %s", args.connection)
    logging.info("       Control topic: %s/%s/%s/control", args.username, args.connection, args.device_id)
    logging.info("          Data topic: %s/%s/%s/data", args.username, args.connection, args.device_id)

    device = dashio.dashDevice(args.connection, args.device_id, args.device_name)
    dash_conn = dashio.dashConnection(args.username, args.password)
    dash_conn.add_device(device)

    monitor_page = dashio.Page("monpg", "Dash Server Moniter")
    gph_network = dashio.TimeGraph("NETWORKGRAPH")
    gph_network.title = "Server Network Traffic: {}".format(args.connection)
    gph_network.y_axis_label = "Kbytes"
    gph_network.y_axis_min = 0.0
    gph_network.y_axis_max = 1000.0
    gph_network.y_axis_num_bars = 11
    Network_Rx = dashio.TimeGraphLine(
        "RX", dashio.TimeGraphLineType.LINE, color=dashio.Color.FUSCIA, max_data_points=no_datapoints
    )
    Network_Tx = dashio.TimeGraphLine(
        "TX", dashio.TimeGraphLineType.LINE, color=dashio.Color.AQUA, max_data_points=no_datapoints
    )

    gph_network.add_line("NET_RX", Network_Rx)
    gph_network.add_line("NET_TX", Network_Tx)
    last_Tx, last_Rx = get_network_rx_tx()

    gph_cpu = dashio.TimeGraph("CPULOAD")
    gph_cpu.title = "CPU load: {}".format(args.connection)
    gph_cpu.y_axis_label = "Percent"
    gph_cpu.y_axis_max = 100
    gph_cpu.y_axis_min = 0
    gph_cpu.y_axis_num_bars = 8
    monitor_page.add_control(gph_network)
    monitor_page.add_control(gph_cpu)
    device.add_control(gph_network)
    device.add_control(gph_cpu)
    number_of_cores = psutil.cpu_count()

    cpu_core_line_array = []
    cpu_data = psutil.cpu_percent(percpu=True)
    for cpu in range(0, number_of_cores):
        line = dashio.TimeGraphLine(
            name="CPU:{}".format(cpu),
            line_type=dashio.TimeGraphLineType.LINE,
            color=dashio.Color(cpu + 1),
            transparency=1.0,
            max_data_points=no_datapoints,
        )
        cpu_core_line_array.append(line)
        gph_cpu.add_line("CPU:{}".format(cpu), line)

    hd_dial = dashio.Dial("HD_USAGE")
    hd_dial.title = "Disk Usage"
    hd_dial.dial_value = psutil.disk_usage("/").percent
    hd_dial.min = 0.0
    hd_dial.max = 100.0
    hd_dial.red_value = 95.0
    hd_dial.show_min_max = True
    disk_usage = 0
    device.add_control(hd_dial)
    monitor_page.add_control(hd_dial)
    device.add_control(monitor_page)
    while not shutdown:
        time.sleep(10)

        Tx, Rx = get_network_rx_tx()

        Network_Rx.add_data_point(Tx - last_Tx)
        Network_Tx.add_data_point(Rx - last_Rx)

        last_Tx = Tx
        last_Rx = Rx

        gph_network.send_data()

        cpu_data = psutil.cpu_percent(percpu=True)

        i = 0
        for line in cpu_core_line_array:
            line.add_data_point(cpu_data[i])
            i += 1
        gph_cpu.send_data()
        du = psutil.disk_usage("/").percent
        if du != disk_usage:
            disk_usage = du
            # Only send if changed.
            hd_dial.dial_value = disk_usage

    device.close()


if __name__ == "__main__":
    main()
