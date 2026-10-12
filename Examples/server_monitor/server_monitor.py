#!/usr/bin/env python3
"""Server monitor example.

Monitors a computer's CPU, memory, disk and network, shows its busiest processes, and sends alarms when it
runs short of resources. Run it on a server, home lab machine or Raspberry Pi and keep an eye on it from the
Dash app. It shows how to:

- Build separate phone and tablet layouts in code with generate_cfg64() and load them with add_cfg64().
- Connect over TCP on the local network and, with a DashIO account, through the Dash server at the same time.
- Store time graph and event log data on the Dash server, so the history can be viewed or exported with
  dashio_data_exporter.
- Use Tables for system information and a process list.
- Send alarms only when a problem lasts, set the alarm levels from the app, and save them.

It needs psutil:
    pip install psutil

Run it with:
    python3 server_monitor.py
The first run writes server_monitor.ini. Add your DashIO username and password to it to connect through
the Dash server, otherwise the monitor is only available over TCP on the local network.
"""
import argparse
import configparser
import logging
import os
import platform
import signal
import socket
import threading
import time

import psutil
import shortuuid

import dashio

SAMPLE_PERIOD = 5.0  # Seconds between readings.
GRAPH_PERIOD = 60.0  # Seconds between time graph data points.
TABLE_PERIOD = 30.0  # Seconds between process and system table updates.
NUM_PROCESSES = 8  # Processes shown in the process table.
DISK_PATH = os.path.abspath(os.sep)  # The disk to monitor, / or C:\

# Control IDs are kept under 8 characters, which the Dash app works best with. The code refers to the controls by
# longer names, the keys of the dict make_controls() returns.

# The layouts: control key -> (DeviceView key, (x, y, width, height)). Positions are ratios of the view size.
# The phone layout spreads the controls over three views. The tablet layout puts them all on one view that
# is three columns wide.
PHONE_VIEWS = {
    "over": ("Overview", 1),
    "hist": ("History", 1),
    "proc": ("Processes", 1),
}
PHONE_LAYOUT = {
    "cpu": ("over", (0.0, 0.0, 0.33, 0.2)),
    "memory": ("over", (0.335, 0.0, 0.33, 0.2)),
    "disk": ("over", (0.67, 0.0, 0.33, 0.2)),
    "system": ("over", (0.0, 0.22, 1.0, 0.6)),
    "usage_graph": ("hist", (0.0, 0.0, 1.0, 0.5)),
    "network_graph": ("hist", (0.0, 0.5, 1.0, 0.5)),
    "processes": ("proc", (0.0, 0.0, 1.0, 0.6)),
    "event_log": ("proc", (0.0, 0.62, 1.0, 0.38)),
}
TABLET_VIEWS = {
    "main": ("Server", 3),
}
TABLET_LAYOUT = {
    "cpu": ("main", (0.0, 0.0, 0.105, 0.2)),
    "memory": ("main", (0.11, 0.0, 0.105, 0.2)),
    "disk": ("main", (0.22, 0.0, 0.105, 0.2)),
    "system": ("main", (0.0, 0.22, 0.33, 0.6)),
    "usage_graph": ("main", (0.34, 0.0, 0.32, 0.5)),
    "network_graph": ("main", (0.34, 0.5, 0.32, 0.5)),
    "processes": ("main", (0.67, 0.0, 0.33, 0.6)),
    "event_log": ("main", (0.67, 0.62, 0.33, 0.38)),
}

# A Menu whose parent is PROV appears in the Dash app's device provisioning menu instead of on a DeviceView.
PROVISIONING_MENU = "PROV"
MENU_POSITION = (0.25, 0.25, 0.15, 0.1)  # A Menu in the provisioning menu isn't drawn, but needs a position.

# Alarms: key -> (name, default level %, seconds the level must be exceeded for before the alarm is sent).
ALARMS = {
    "cpu": ("CPU", 90, 300),
    "memory": ("Memory", 90, 120),
    "disk": ("Disk", 90, 0),
}


def make_controls(views: dict, layout: dict, alarm_levels: dict) -> dict:
    """Creates the DeviceViews and controls, positioned for a layout. The dials show alarm_levels in red.

    It is called once for the controls the device uses, and again for each other layout. Controls for
    different layouts are separate instances with the same control IDs, which generate_cfg64() turns into
    independent layouts.
    """
    controls = {}
    for key, (title, num_columns) in views.items():
        controls[f"view_{key}"] = dashio.DeviceView(f"dv_{key}", title, num_columns=num_columns)

    def place(key, control):
        controls[f"view_{layout[key][0]}"].add_control(control)
        controls[key] = control

    def position(key):
        return dashio.ControlPosition(*layout[key][1])

    for key, (name, _, _) in ALARMS.items():
        place(key, dashio.Dial(
            key, name, dial_min=0.0, dial_max=100.0, red_value=alarm_levels[key], units="%", style=dashio.DialStyle.BAR,
            number_position=dashio.DialNumberPosition.CENTER, control_position=position(key)
        ))
    place("system", dashio.Table(
        "system", "System", columns=2, label_width_percent=35, control_position=position("system")
    ))

    # The alarm levels are changed less often, so they go in the Dash app's device provisioning menu.
    alarm_levels = dashio.Menu("levels", "Alarm Levels", text="Alarm Levels", icon_name=dashio.Icon.BELL,
                               control_position=dashio.ControlPosition(*MENU_POSITION))
    alarm_levels.parent_id = PROVISIONING_MENU
    controls["alarm_levels"] = alarm_levels
    for key, (name, _, _) in ALARMS.items():
        slider = dashio.Slider(f"{key}L", f"{name} Alarm %", bar_min=50.0, bar_max=100.0, show_min_max=True)
        alarm_levels.add_control(slider)
        controls[f"{key}_level"] = slider

    usage_graph = dashio.TimeGraph(
        "usage", "CPU and Memory", y_axis_label="%", y_axis_min=0.0, y_axis_max=100.0,
        control_position=position("usage_graph")
    )
    usage_graph.add_line("cpu", dashio.TimeGraphLine("CPU", color=dashio.Color.RED))
    usage_graph.add_line("memory", dashio.TimeGraphLine("Memory", color=dashio.Color.DODGER_BLUE))
    place("usage_graph", usage_graph)
    network_graph = dashio.TimeGraph(
        "network", "Network", y_axis_label="kB/s", y_axis_min=0.0, y_axis_max=1000.0,
        control_position=position("network_graph")
    )
    network_graph.add_line("received", dashio.TimeGraphLine("Received", color=dashio.Color.LIME))
    network_graph.add_line("sent", dashio.TimeGraphLine("Sent", color=dashio.Color.ORANGE))
    place("network_graph", network_graph)
    place("processes", dashio.Table(
        "procs", "Busiest Processes", columns=3, label_width_percent=50,
        column_headings=["Process", "CPU %", "Mem %"], control_position=position("processes")
    ))
    place("event_log", dashio.EventLog("events", "Events", control_position=position("event_log")))
    return controls


def format_duration(seconds: float) -> str:
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    return f"{days}d {hours}h {seconds // 60}m" if days else f"{hours}h {seconds // 60}m"


def ip_address() -> str:
    """The address used to reach the network, without sending anything."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 80))
            return sock.getsockname()[0]
    except OSError:
        return "-"


def max_temperature() -> float | None:
    """The hottest temperature sensor in C, or None where psutil can't read temperatures (e.g. macOS)."""
    if not hasattr(psutil, "sensors_temperatures"):
        return None
    readings = [sensor.current for sensors in psutil.sensors_temperatures().values() for sensor in sensors]
    return max(readings) if readings else None


def update_config_revision(device: dashio.Device, settings: "Settings"):
    """Set the device's cfgRev, increasing it when the CFG has changed since the last run.

    The Dash app only fetches a new CFG when cfgRev changes. The layouts are built here each time the program
    starts, so the CFG's hash is saved with cfgRev to tell when the layouts, or anything else in the CFG, change.
    """
    cfg_hash = device.get_cfg_hash()
    cfg_rev = int(settings.get("DEVICE", "cfg_rev"))
    if cfg_hash != settings.get("DEVICE", "cfg_hash"):
        cfg_rev += 1
        settings.set("DEVICE", "cfg_rev", cfg_rev)
        settings.set("DEVICE", "cfg_hash", cfg_hash)
        logging.info("CFG changed, cfgRev is now %s", cfg_rev)
    device.config_revision = cfg_rev


class Settings:
    """The monitor's settings, kept in an ini file so they survive a restart."""

    def __init__(self, filename: str):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read_dict({
            "DEVICE": {"device_id": shortuuid.uuid(), "device_name": socket.gethostname(), "cfg_rev": "1", "cfg_hash": ""},
            "DASH": {"username": "", "password": ""},
            "ALARMS": {f"{key}_level": str(level) for key, (_, level, _) in ALARMS.items()},
        })
        if not self.config.read(filename):
            self.save()
            logging.info("Wrote %s. Add your DashIO username and password to it to use the Dash server.", filename)

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as ini_file:
            self.config.write(ini_file)

    def get(self, section: str, key: str) -> str:
        return self.config.get(section, key)

    def set(self, section: str, key: str, value):
        self.config.set(section, key, str(value))
        self.save()


class ServerMonitor:
    """Reads the computer's resources and runs its Dash device."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Dash app messages arrive on the device thread and the readings are taken on the Schedular thread.
        self.lock = threading.Lock()
        self.usage = {key: 0.0 for key in ALARMS}
        self.cpu_samples = []
        self.memory_samples = []
        self.network = psutil.net_io_counters()
        self.network_time = time.time()
        self.alarm_since = {}  # Alarm key -> when its level was first exceeded.
        self.active_alarms = set()
        # The first CPU readings are meaningless, they set the start of the next interval.
        psutil.cpu_percent()
        for _ in psutil.process_iter(["cpu_percent"]):
            pass

        self.device = dashio.Device(
            "ServerMonitor", settings.get("DEVICE", "device_id"), settings.get("DEVICE", "device_name")
        )
        alarm_levels = {key: self.alarm_level(key) for key in ALARMS}
        self.controls = make_controls(PHONE_VIEWS, PHONE_LAYOUT, alarm_levels)
        for control in self.controls.values():
            self.device.add_control(control)
        self.alarm = dashio.Alarm("alarm")
        self.device.add_control(self.alarm)

        # Phone and fold out apps (1 and 2 columns) get the phone layout, tablets (3 columns) the tablet layout.
        self.device.add_cfg64(dashio.generate_cfg64(*self.controls.values()), 1)
        self.device.add_cfg64(dashio.generate_cfg64(*make_controls(TABLET_VIEWS, TABLET_LAYOUT, alarm_levels).values()), 3)

        for key in ALARMS:
            self.controls[f"{key}_level"].add_receive_message_callback(self.alarm_level_handler)
        self.device.set_name_callback(self.name_handler)
        update_config_revision(self.device, settings)

        self.connections = [dashio.TCPConnection()]
        username, password = settings.get("DASH", "username"), settings.get("DASH", "password")
        if username and password:
            self.connections.append(dashio.DashConnection(username, password))
        else:
            logging.info("No DashIO username and password, only using TCP.")
        for connection in self.connections:
            connection.add_device(self.device)

        self.schedular = dashio.Schedular("ServerMonitor")
        # Start after the device has started, as the first tick sends the controls' initial state.
        self.started = False
        self.schedular.add_timer(SAMPLE_PERIOD, -SAMPLE_PERIOD + 1.0, self.sample_tick)
        self.schedular.add_timer(TABLE_PERIOD, -TABLE_PERIOD + 1.5, self.table_tick)
        self.schedular.add_timer(GRAPH_PERIOD, -GRAPH_PERIOD + 2.0, self.graph_tick)

    def alarm_level(self, key: str) -> float:
        return float(self.settings.get("ALARMS", f"{key}_level"))

    def log_event(self, text: str, color=dashio.Color.WHITE):
        logging.info(text)
        self.controls["event_log"].add_event_data(dashio.EventData(text, color))

    def start(self):
        """Send the initial state and turn on Dash server storage for the history."""
        for key in ALARMS:
            self.controls[f"{key}_level"].slider_value = self.alarm_level(key)
        for control_type, control_id in (
            (dashio.ControlName.TGRPH, self.controls["usage_graph"].control_id),
            (dashio.ControlName.TGRPH, self.controls["network_graph"].control_id),
            (dashio.ControlName.LOG, self.controls["event_log"].control_id),
        ):
            self.device.storage_enable(control_type, control_id)
        self.log_event("Monitor started", dashio.Color.LIME)
        self.started = True

    def check_alarm(self, key: str):
        """Send an alarm once a usage level has been exceeded for long enough, and log when it clears."""
        name, _, delay = ALARMS[key]
        level = self.alarm_level(key)
        if self.usage[key] >= level:
            since = self.alarm_since.setdefault(key, time.time())
            if key not in self.active_alarms and time.time() - since >= delay:
                self.active_alarms.add(key)
                message = f"{name} at {self.usage[key]:.0f}% (alarm level {level:.0f}%)"
                self.alarm.send(f"{self.device.device_name}: {name} alarm", message)
                self.log_event(message, dashio.Color.RED)
        else:
            self.alarm_since.pop(key, None)
            if key in self.active_alarms:
                self.active_alarms.remove(key)
                self.log_event(f"{name} back to {self.usage[key]:.0f}%", dashio.Color.LIME)

    def sample_tick(self, _) -> bool:
        """Read CPU, memory and disk use. Called by the Schedular every SAMPLE_PERIOD seconds."""
        try:
            with self.lock:
                if not self.started:
                    self.start()
                self.usage["cpu"] = psutil.cpu_percent()
                self.usage["memory"] = psutil.virtual_memory().percent
                self.usage["disk"] = psutil.disk_usage(DISK_PATH).percent
                self.cpu_samples.append(self.usage["cpu"])
                self.memory_samples.append(self.usage["memory"])
                for key, value in self.usage.items():
                    if round(value) != self.controls[key].dial_value:  # Only send changes.
                        self.controls[key].dial_value = round(value)
                        self.controls[f"{key}_level"].bar1_value = round(value)  # Usage against the alarm level.
                    self.check_alarm(key)
        except Exception:  # pylint: disable=broad-except
            logging.exception("Sample error")  # Keep the Schedular running.
        return True

    def table_tick(self, _) -> bool:
        """Update the system and process tables. Called by the Schedular every TABLE_PERIOD seconds."""
        try:
            with self.lock:
                memory = psutil.virtual_memory()
                load = os.getloadavg() if hasattr(os, "getloadavg") else None
                rows = [
                    ("Host", socket.gethostname()),
                    ("OS", f"{platform.system()} {platform.release()}"),
                    ("IP", ip_address()),
                    ("Uptime", format_duration(time.time() - psutil.boot_time())),
                    ("CPUs", f"{psutil.cpu_count()} at {self.usage['cpu']:.0f}%"),
                    ("Load", " ".join(f"{value:.2f}" for value in load) if load else "-"),
                    ("Memory", f"{memory.used / 2**30:.1f} of {memory.total / 2**30:.1f} GB"),
                    ("Disk", f"{psutil.disk_usage(DISK_PATH).free / 2**30:.0f} GB free"),
                ]
                temperature = max_temperature()
                if temperature is not None:
                    rows.append(("Temperature", f"{temperature:.0f}°C"))
                for index, (label, value) in enumerate(rows):
                    self.controls["system"].update_table_row(dashio.TableRow(label, [value]), index)

                processes = []
                for process in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
                    info = process.info
                    if info["cpu_percent"] is not None and info["memory_percent"] is not None:
                        processes.append(info)
                processes.sort(key=lambda info: (info["cpu_percent"], info["memory_percent"]), reverse=True)
                for index, info in enumerate(processes[:NUM_PROCESSES]):
                    row = dashio.TableRow(info["name"], [f"{info['cpu_percent']:.1f}", f"{info['memory_percent']:.1f}"])
                    self.controls["processes"].update_table_row(row, index)
        except Exception:  # pylint: disable=broad-except
            logging.exception("Table error")
        return True

    def graph_tick(self, _) -> bool:
        """Add a point to the time graphs. Called by the Schedular every GRAPH_PERIOD seconds."""
        try:
            with self.lock:
                usage_graph = self.controls["usage_graph"]
                if self.cpu_samples:
                    # Average over the period, so short spikes and dips between points aren't missed.
                    usage_graph.line_dict["cpu"].add_data_point(round(sum(self.cpu_samples) / len(self.cpu_samples), 1))
                    usage_graph.line_dict["memory"].add_data_point(round(sum(self.memory_samples) / len(self.memory_samples), 1))
                    self.cpu_samples.clear()
                    self.memory_samples.clear()
                    usage_graph.send_data()

                network = psutil.net_io_counters()
                now = time.time()
                seconds = max(now - self.network_time, 1.0)
                network_graph = self.controls["network_graph"]
                network_graph.line_dict["received"].add_data_point(round((network.bytes_recv - self.network.bytes_recv) / seconds / 1000, 1))
                network_graph.line_dict["sent"].add_data_point(round((network.bytes_sent - self.network.bytes_sent) / seconds / 1000, 1))
                network_graph.send_data()
                self.network, self.network_time = network, now
        except Exception:  # pylint: disable=broad-except
            logging.exception("Graph error")
        return True

    def alarm_level_handler(self, msg):
        with self.lock:
            key = msg[2].removesuffix("L")  # The alarm level sliders' IDs are cpuL, memoryL and diskL.
            level = round(float(msg[3]))
            self.settings.set("ALARMS", f"{key}_level", level)
            self.controls[f"{key}_level"].slider_value = level
            # The dial's red zone is part of its layout, so it shows the new level after a restart.
            self.log_event(f"{ALARMS[key][0]} alarm level set to {level}%")

    def name_handler(self, msg) -> str:
        name = msg[2]
        self.settings.set("DEVICE", "device_name", name)
        self.log_event(f"Renamed to {name}")
        return name

    def close(self):
        self.schedular.stop()
        for connection in self.connections:
            connection.close()
        self.device.close()


def main():
    parser = argparse.ArgumentParser(description="Server monitor example for DashIO.")
    parser.add_argument("-i", "--ini", default="server_monitor.ini", help="Settings file. Defaults to server_monitor.ini")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(message)s")

    shutdown = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: shutdown.set())
    signal.signal(signal.SIGTERM, lambda *_: shutdown.set())

    monitor = ServerMonitor(Settings(args.ini))
    while not shutdown.wait(1.0):
        pass
    monitor.close()


if __name__ == "__main__":
    main()
