#!/usr/bin/env python3
"""A data logger that only connects to the Dash server now and then.

Devices on LTE often keep the connection down to save power, and connect every so often to send their data.
This example shows how to:

- Keep the time graph and event log data in a DashStore while disconnected.
- Connect with DashConnection(auto_connect=False) and connect() on a schedule.
- Disconnect with disconnect() when the store has synced with the Dash server, using the store sync callback.
  The server is sent the data it missed, and the Dash app gets the history from the server.
- Support store and forward (SAF), so the Dash app can turn it on for the device on the Dash server.
- Provision the device over an always on TCP connection on the local network, as an IoT device usually does
  over BLE: the Dash app gets the layout, sets the device name and the Dash server username and password, and
  sets the connection and record intervals in the device's provisioning menu.

Run it with:
    python3 intermittent_connection.py
then find the device in the Dash app on the local network, and set the Dash username and password in its
provisioning menu. Or give them on the command line with -u and -w.
"""
import argparse
import configparser
import logging
import math
import random
import signal
import threading
import time

import shortuuid

import dashio

SYNC_TIME_LIMIT = 120  # Seconds to stay connected if the sync doesn't finish, e.g. the server doesn't reply.
# A Menu whose parent is PROV appears in the Dash app's device provisioning menu instead of on a DeviceView.
PROVISIONING_MENU = "PROV"


def seconds_to_interval(seconds: int) -> str:
    """Seconds as an ISO 8601 interval, HH:MM:SS, for an Interval text box."""
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def interval_to_seconds(text: str) -> int | None:
    """An interval from the Dash app, e.g. "00:15:00", in seconds, or None if it isn't one."""
    try:
        hours, minutes, seconds = (int(part) for part in text.strip()[:8].split(":"))
    except ValueError:
        return None
    return hours * 3600 + minutes * 60 + seconds


class Settings:
    """The logger's settings, kept in an ini file so they survive a restart."""

    def __init__(self, filename: str):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read_dict({
            "DEVICE": {"device_id": shortuuid.uuid(), "device_name": "Intermittent Logger", "cfg_rev": "1", "cfg_hash": ""},
            "DASH": {"username": "", "password": ""},
            "SETTINGS": {"connect_interval": "900", "record_interval": "10"},
        })
        if not self.config.read(filename):
            self.save()

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as ini_file:
            self.config.write(ini_file)

    def get(self, section: str, key: str) -> str:
        return self.config.get(section, key)

    def set(self, section: str, key: str, value):
        self.config.set(section, key, str(value))
        self.save()


class Logger:
    """Records a temperature, and connects every connection interval to sync with the Dash server."""

    def __init__(self, settings: Settings, store: dashio.DashStore, port: int):
        self.settings = settings
        self.store = store
        self.lock = threading.Lock()
        self.disconnect_at = None  # When connected, the time to disconnect.
        self.next_record = self.next_connect = time.monotonic()

        self.device = dashio.Device(
            "IntermittentLogger", settings.get("DEVICE", "device_id"), settings.get("DEVICE", "device_name"), store=store
        )
        self.graph = dashio.TimeGraph("graph", "Temperature", y_axis_label="°C", y_axis_min=0.0, y_axis_max=40.0,
                                      control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.5))
        self.graph.add_line("temp", dashio.TimeGraphLine("Temperature", color=dashio.Color.RED))
        self.events = dashio.EventLog("events", "Connections", control_position=dashio.ControlPosition(0.0, 0.5, 1.0, 0.5))
        view = dashio.DeviceView("dv_main", "Logger")
        for control in (self.graph, self.events):
            self.device.add_control(control)
            view.add_control(control)
        self.device.add_control(view)

        # The settings are in the Dash app's provisioning menu, available over the local TCP connection.
        setup = dashio.Menu("setup", "Logger Settings", text="Logger Settings", icon_name=dashio.Icon.COG,
                            control_position=dashio.ControlPosition(0.0, 0.0, 1.0, 0.1))
        setup.parent_id = PROVISIONING_MENU
        self.connect_interval = dashio.TextBox("conn", "Connect Every", text_format=dashio.TextFormat.INTVL,
                                               keyboard_type=dashio.Keyboard.INTVL)
        self.record_interval = dashio.TextBox("rec", "Record Every", text_format=dashio.TextFormat.INTVL,
                                              keyboard_type=dashio.Keyboard.INTVL)
        self.connect_now = dashio.Button("now", "Connect Now", icon_name=dashio.Icon.REFRESH)
        for control in (self.connect_interval, self.record_interval, self.connect_now):
            setup.add_control(control)
            self.device.add_control(control)
        self.device.add_control(setup)
        self.connect_interval.text = seconds_to_interval(int(settings.get("SETTINGS", "connect_interval")))
        self.record_interval.text = seconds_to_interval(int(settings.get("SETTINGS", "record_interval")))
        self.connect_interval.add_receive_message_callback(self.interval_handler)
        self.record_interval.add_receive_message_callback(self.interval_handler)
        self.connect_now.add_receive_message_callback(lambda _msg: self.wake())
        self.device.set_dashio_callback(self.dashio_handler)
        self.device.set_name_callback(self.name_handler)
        # Lets the Dash app turn on store and forward on the Dash server, which keeps the app's messages for the
        # device while it's disconnected, and the device's latest values for the app.
        self.device.store_and_forward = True

        # Always on, for provisioning and live values on the local network.
        self.tcp = dashio.TCPConnection(port=port)
        self.tcp.add_device(self.device)
        self.dash = dashio.DashConnection(settings.get("DASH", "username"), settings.get("DASH", "password"), auto_connect=False)
        self.dash.add_device(self.device)
        self.device.set_store_sync_callback(self.synced)
        # The Dash server keeps the history, so the app gets it from the server. STE is sent when connected.
        self.device.storage_enable(dashio.ControlName.TGRPH, "graph")
        self.device.storage_enable(dashio.ControlName.LOG, "events")
        # After adding the connections, which are listed in the CFG's deviceSetup.
        self.update_config_revision()

    def update_config_revision(self):
        """Increase cfgRev when the CFG has changed, so the Dash app fetches the new layout."""
        cfg_hash = self.device.get_cfg_hash()
        cfg_rev = int(self.settings.get("DEVICE", "cfg_rev"))
        if cfg_hash != self.settings.get("DEVICE", "cfg_hash"):
            cfg_rev += 1
            self.settings.set("DEVICE", "cfg_rev", cfg_rev)
            self.settings.set("DEVICE", "cfg_hash", cfg_hash)
        self.device.config_revision = cfg_rev

    def interval_handler(self, msg):
        seconds = interval_to_seconds(msg[3])
        if msg[2] == "conn":
            box, key, label = self.connect_interval, "connect_interval", "Connection interval"
        else:
            box, key, label = self.record_interval, "record_interval", "Record interval"
        if seconds is None or seconds < 1:
            logging.warning("Not an interval: %s", msg[3])
        else:
            with self.lock:
                self.settings.set("SETTINGS", key, seconds)
                if key == "connect_interval":
                    self.next_connect = time.monotonic() + seconds
                else:
                    self.next_record = time.monotonic()
            logging.info("%s set to %s", label, seconds_to_interval(seconds))
        box.text = seconds_to_interval(int(self.settings.get("SETTINGS", key)))

    def name_handler(self, msg) -> str:
        """The Dash app renames the device."""
        name = msg[2]
        self.settings.set("DEVICE", "device_name", name)
        logging.info("Renamed to %s", name)
        return name

    def dashio_handler(self, msg) -> bool:
        """The Dash app sets the Dash server username and password."""
        try:
            username, password = msg[2], msg[3]
        except IndexError:
            return False
        self.settings.set("DASH", "username", username)
        self.settings.set("DASH", "password", password)
        self.dash.username, self.dash.password = username, password
        logging.info("Dash server username set to %s", username)
        self.wake()
        return True

    def synced(self, completed: bool):
        """Store sync callback, called on the device thread when the sync with the Dash server ends."""
        logging.info("Sync %s", "finished" if completed else "failed")
        with self.lock:
            if self.disconnect_at is not None:
                self.disconnect_at = time.monotonic()

    def record(self):
        temperature = 20 + 5 * math.sin(time.time() / 600) + random.uniform(-0.5, 0.5)
        self.graph.line_dict["temp"].add_data_point(round(temperature, 2))

    def wake(self):
        if not self.dash.username or not self.dash.password:
            logging.info("Not connecting to the Dash server: set the username and password in the provisioning menu")
            return
        logging.info("Connecting")
        self.events.add_event_data(dashio.EventData("Connecting", dashio.Color.GREEN))
        with self.lock:
            self.disconnect_at = time.monotonic() + SYNC_TIME_LIMIT
        self.dash.connect()

    def sleep(self):
        logging.info("Disconnecting")
        with self.lock:
            self.disconnect_at = None
        self.dash.disconnect()

    def run(self, shutdown: threading.Event):
        while not shutdown.wait(0.5):
            now = time.monotonic()
            with self.lock:
                record = now >= self.next_record
                if record:
                    self.next_record = now + int(self.settings.get("SETTINGS", "record_interval"))
                wake = now >= self.next_connect
                if wake:
                    self.next_connect = now + int(self.settings.get("SETTINGS", "connect_interval"))
                disconnect = self.disconnect_at is not None and now >= self.disconnect_at
            if record:
                self.record()
            if wake:
                self.wake()
            if disconnect:
                self.sleep()

    def close(self):
        self.dash.close()
        self.tcp.close()
        self.device.close()
        self.store.close()


def main():
    parser = argparse.ArgumentParser(description="A data logger that only connects to the Dash server now and then.")
    parser.add_argument("-u", "--username", help="DashIO username, saved in the settings file")
    parser.add_argument("-w", "--password", help="DashIO password, saved in the settings file")
    parser.add_argument("-p", "--port", type=int, default=5650, help="TCP port for the Dash app on the local network. Defaults to 5650")
    parser.add_argument("-i", "--ini", default="intermittent.ini", help="Settings file. Defaults to intermittent.ini")
    parser.add_argument("--db", default="intermittent.db", help="Data store. Defaults to intermittent.db")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(message)s")

    settings = Settings(args.ini)
    if args.username and args.password:
        settings.set("DASH", "username", args.username)
        settings.set("DASH", "password", args.password)

    shutdown = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: shutdown.set())
    signal.signal(signal.SIGTERM, lambda *_: shutdown.set())

    data_logger = Logger(settings, dashio.DashStore(args.db), args.port)
    data_logger.run(shutdown)
    data_logger.close()


if __name__ == "__main__":
    main()
