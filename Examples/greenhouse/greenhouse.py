#!/usr/bin/env python3
"""Greenhouse controller example.

Controls the heater, fan and lights of a greenhouse from its temperature and humidity, and lets you monitor
and adjust it from the Dash app. It shows how to:

- Build a layout for phones, fold out phones and tablets in code with generate_cfg64(), and load each with
  add_cfg64() so the Dash app gets the layout for its screen.
- Connect over TCP on the local network and, with a DashIO account, through the Dash server at the same time.
- Store time graph and event log data on the Dash server, so the history can be viewed or exported with
  dashio_data_exporter.
- Run a control loop and a lighting schedule with a Schedular.
- Send alarms, keep an event log, and save settings so they survive a restart.

The greenhouse is simulated (see simulator.py) so the example runs anywhere. Replace the simulator to
control a real one.

Run it with:
    python3 greenhouse.py
The first run writes greenhouse.ini. Add your DashIO username and password to it to connect through the
Dash server, otherwise the controller is only available over TCP on the local network.
"""
import argparse
import configparser
import datetime
import logging
import signal
import threading
import time

import shortuuid

import dashio
from simulator import GreenhouseSimulator

CONTROL_PERIOD = 5.0  # Seconds between reading the sensors and updating the outputs.
GRAPH_PERIOD = 60.0  # Seconds between time graph data points.
HEATER_HYSTERESIS = 0.5  # The heater turns on below target - this and off above target + this.
FAN_TEMPERATURE_OFFSET = 3.0  # The fan turns on above target + this to vent heat.
HUMIDITY_HYSTERESIS = 5.0  # The fan turns off once humidity is this far below the maximum.
FROST_ALARM = 4.0
HEAT_ALARM = 35.0

MODES = ["Auto", "Manual"]

# A Menu whose parent is PROV appears in the Dash app's device provisioning menu instead of on a DeviceView.
PROVISIONING_MENU = "PROV"
MENU_POSITION = (0.25, 0.25, 0.15, 0.1)  # A Menu in the provisioning menu isn't drawn, but needs a position.

# Control IDs are kept under 8 characters, which the Dash app works best with. The code refers to the controls by
# longer names, the keys of the dict make_controls() returns.

# A layout for each number of columns the Dash app reports: 1 for phones, 2 for fold out phones and 3 for
# tablets. Each layout is (views, positions):
#   views: DeviceView key -> (title, number of columns the view is wide)
#   positions: control key -> (DeviceView key, (x, y, width, height)), as ratios of the view's size
LAYOUTS = {
    # Phones: three views, one column wide.
    1: (
        {
            "clim": ("Climate", 1),
            "ctrl": ("Controls", 1),
            "hist": ("History", 1),
        },
        {
            "temperature": ("clim", (0.0, 0.0, 0.5, 0.3)),
            "humidity": ("clim", (0.5, 0.0, 0.5, 0.3)),
            "target": ("clim", (0.2, 0.32, 0.6, 0.4)),
            "status": ("clim", (0.0, 0.75, 1.0, 0.1)),
            "mode": ("ctrl", (0.0, 0.0, 1.0, 0.12)),
            "heater": ("ctrl", (0.0, 0.15, 0.33, 0.2)),
            "fan": ("ctrl", (0.335, 0.15, 0.33, 0.2)),
            "lights": ("ctrl", (0.67, 0.15, 0.33, 0.2)),
            "climate_graph": ("hist", (0.0, 0.0, 1.0, 0.55)),
            "event_log": ("hist", (0.0, 0.57, 1.0, 0.43)),
        },
    ),
    # Fold out phones: one view, two columns wide. Climate and controls on the left, history on the right.
    2: (
        {
            "main": ("Greenhouse", 2),
        },
        {
            "temperature": ("main", (0.0, 0.0, 0.24, 0.22)),
            "humidity": ("main", (0.25, 0.0, 0.24, 0.22)),
            "target": ("main", (0.05, 0.24, 0.39, 0.3)),
            "status": ("main", (0.0, 0.56, 0.49, 0.07)),
            "mode": ("main", (0.0, 0.65, 0.49, 0.1)),
            "heater": ("main", (0.0, 0.77, 0.16, 0.15)),
            "fan": ("main", (0.165, 0.77, 0.16, 0.15)),
            "lights": ("main", (0.33, 0.77, 0.16, 0.15)),
            "climate_graph": ("main", (0.51, 0.0, 0.49, 0.6)),
            "event_log": ("main", (0.51, 0.62, 0.49, 0.38)),
        },
    ),
    # Tablets: one view, three columns wide. Climate, then controls and events, then history.
    3: (
        {
            "main": ("Greenhouse", 3),
        },
        {
            "temperature": ("main", (0.0, 0.0, 0.16, 0.25)),
            "humidity": ("main", (0.17, 0.0, 0.16, 0.25)),
            "target": ("main", (0.0, 0.27, 0.33, 0.33)),
            "status": ("main", (0.0, 0.62, 0.33, 0.08)),
            "mode": ("main", (0.35, 0.0, 0.3, 0.1)),
            "heater": ("main", (0.35, 0.12, 0.095, 0.15)),
            "fan": ("main", (0.4525, 0.12, 0.095, 0.15)),
            "lights": ("main", (0.555, 0.12, 0.095, 0.15)),
            "event_log": ("main", (0.35, 0.3, 0.3, 0.7)),
            "climate_graph": ("main", (0.67, 0.0, 0.33, 1.0)),
        },
    ),
}


def make_controls(views: dict, positions: dict) -> dict:
    """Creates the DeviceViews and controls, positioned for a layout.

    It is called once for the controls the device uses, and again for each other layout. Controls for
    different layouts are separate instances with the same control IDs, which generate_cfg64() turns into
    independent layouts.
    """
    controls = {}
    for key, (title, num_columns) in views.items():
        controls[f"view_{key}"] = dashio.DeviceView(f"dv_{key}", title, num_columns=num_columns)

    def place(key, control):
        controls[f"view_{positions[key][0]}"].add_control(control)
        controls[key] = control

    def position(key):
        return dashio.ControlPosition(*positions[key][1])

    place("temperature", dashio.Dial(
        "temp", "Temperature", dial_min=0.0, dial_max=40.0, red_value=30.0, units="°C",
        precision=dashio.Precision.ONE, control_position=position("temperature")
    ))
    place("humidity", dashio.Dial(
        "humid", "Humidity", dial_min=0.0, dial_max=100.0, red_value=85.0, units="%",
        dial_fill_color=dashio.Color.DODGER_BLUE, control_position=position("humidity")
    ))
    place("target", dashio.Knob(
        "target", "Target Temperature", dial_min=5.0, dial_max=35.0, red_value=30.0, show_min_max=True,
        control_position=position("target")
    ))
    place("status", dashio.TextBox(
        "status", "Status", text_align=dashio.TextAlignment.CENTER, keyboard_type=dashio.Keyboard.NONE,
        control_position=position("status")
    ))
    place("mode", dashio.Selector("mode", "Mode", selection=MODES, control_position=position("mode")))
    place("heater", dashio.Button(
        "heater", "Heater", icon_name=dashio.Icon.TEMPERATURE, on_color=dashio.Color.RED,
        off_color=dashio.Color.DARK_GRAY, control_position=position("heater")
    ))
    place("fan", dashio.Button(
        "fan", "Fan", icon_name=dashio.Icon.FAN, on_color=dashio.Color.DODGER_BLUE,
        off_color=dashio.Color.DARK_GRAY, control_position=position("fan")
    ))
    place("lights", dashio.Button(
        "lights", "Lights", icon_name=dashio.Icon.LIGHT_BULB, on_color=dashio.Color.GOLD,
        off_color=dashio.Color.DARK_GRAY, control_position=position("lights")
    ))

    # The settings are changed less often, so they go in the Dash app's device provisioning menu.
    settings = dashio.Menu("setup", "Greenhouse Settings", text="Greenhouse Settings", icon_name=dashio.Icon.COG,
                           control_position=dashio.ControlPosition(*MENU_POSITION))
    settings.parent_id = PROVISIONING_MENU
    controls["settings"] = settings
    for key, control in (
        ("max_humidity", dashio.Slider(
            "maxhum", "Max Humidity %", bar_min=40.0, bar_max=95.0, red_value=90.0, show_min_max=True
        )),
        # Date/Time format, so the Dash app shows the time nicely and offers a date/time entry keyboard.
        ("lights_on", dashio.TextBox(
            "lt_on", "Lights On", text_format=dashio.TextFormat.DATETIME, keyboard_type=dashio.Keyboard.TIME
        )),
        ("lights_off", dashio.TextBox(
            "lt_off", "Lights Off", text_format=dashio.TextFormat.DATETIME, keyboard_type=dashio.Keyboard.TIME
        )),
    ):
        settings.add_control(control)
        controls[key] = control

    # One graph: temperature and target on the left axis, humidity on the right axis. Temperature and target
    # share a line of [temperature, target] arrays, and the Dash app chooses a color for each.
    climate_graph = dashio.TimeGraph(
        "graph", "Climate", y_axis_label="°C", y_axis_min=0.0, y_axis_max=40.0,
        y_axis_label_rt="%", y_axis_min_rt=0.0, y_axis_max_rt=100.0, control_position=position("climate_graph")
    )
    climate_graph.add_line("temperatures", dashio.TimeGraphLine(["Temperature", "Target"], color=None))
    climate_graph.add_line("humidity", dashio.TimeGraphLine("Humidity", color=dashio.Color.DODGER_BLUE, right_axis=True))
    place("climate_graph", climate_graph)
    place("event_log", dashio.EventLog("events", "Events", control_position=position("event_log")))
    return controls


def parse_time(text: str) -> str | None:
    """Returns text as local HH:MM, or None if it isn't a time.

    Accepts an ISO 8601 time, as the Dash app sends from a Date/Time text box, e.g. "16:30:00+1300", an ISO 8601
    date time, or HH:MM.
    """
    text = text.strip()
    try:
        when = datetime.datetime.fromisoformat(text)
    except ValueError:
        try:
            when = datetime.datetime.combine(datetime.date.today(), datetime.time.fromisoformat(text))
        except ValueError:
            return None
    if when.tzinfo is not None:
        when = when.astimezone()  # The lights times are local.
    return when.strftime("%H:%M")


def iso_time(hh_mm: str) -> str:
    """Local time HH:MM as an ISO 8601 time with its UTC offset, e.g. "16:30:00+1300", for a Date/Time text box."""
    when = datetime.datetime.combine(datetime.date.today(), datetime.time.fromisoformat(hh_mm)).astimezone()
    return when.strftime("%H:%M:%S%z")


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
    """The controller's settings, kept in an ini file so they survive a restart."""

    def __init__(self, filename: str):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read_dict({
            "DEVICE": {"device_id": shortuuid.uuid(), "device_name": "Greenhouse", "cfg_rev": "1", "cfg_hash": ""},
            "DASH": {"username": "", "password": ""},
            "SETTINGS": {
                "mode": "Auto",
                "target_temperature": "20.0",
                "max_humidity": "85.0",
                "lights_on": "06:00",
                "lights_off": "20:00",
            },
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


class GreenhouseController:
    """Runs the greenhouse and its Dash device."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.greenhouse = GreenhouseSimulator()
        # Dash app messages arrive on the device thread and the control loop runs on the Schedular thread.
        self.lock = threading.Lock()
        self.heater = False
        self.fan = False
        self.lights = False
        self.temperature = 0.0
        self.humidity = 0.0
        self.active_alarms = set()

        self.device = dashio.Device("Greenhouse", settings.get("DEVICE", "device_id"), settings.get("DEVICE", "device_name"))
        # The device's own controls use the phone layout. Each layout, including that one, is loaded for its
        # number of columns, so the Dash app gets the layout for its screen.
        self.controls = make_controls(*LAYOUTS[1])
        for control in self.controls.values():
            self.device.add_control(control)
        self.alarm = dashio.Alarm("alarm")
        self.device.add_control(self.alarm)
        for num_columns, layout in LAYOUTS.items():
            controls = self.controls if num_columns == 1 else make_controls(*layout)
            self.device.add_cfg64(dashio.generate_cfg64(*controls.values()), num_columns)

        self.controls["target"].add_receive_message_callback(self.target_handler)
        self.controls["mode"].add_receive_message_callback(self.mode_handler)
        for output in ("heater", "fan", "lights"):
            self.controls[output].add_receive_message_callback(self.output_handler)
        self.controls["max_humidity"].add_receive_message_callback(self.max_humidity_handler)
        self.controls["lights_on"].add_receive_message_callback(self.lights_time_handler)
        self.controls["lights_off"].add_receive_message_callback(self.lights_time_handler)
        self.device.set_name_callback(self.name_handler)

        self.connections = [dashio.TCPConnection()]
        username, password = settings.get("DASH", "username"), settings.get("DASH", "password")
        if username and password:
            self.connections.append(dashio.DashConnection(username, password))
        else:
            logging.info("No DashIO username and password, only using TCP.")
        for connection in self.connections:
            connection.add_device(self.device)
        # After adding the connections, which are listed in the CFG's deviceSetup.
        update_config_revision(self.device, settings)

        self.schedular = dashio.Schedular("Greenhouse")
        # Start after the device has started, as the first tick sends the controls' initial state.
        self.schedular.add_timer(CONTROL_PERIOD, -CONTROL_PERIOD + 1.0, self.control_tick)
        self.schedular.add_timer(GRAPH_PERIOD, -GRAPH_PERIOD + 2.0, self.graph_tick)
        self.started = False

    @property
    def auto(self) -> bool:
        return self.settings.get("SETTINGS", "mode") == "Auto"

    @property
    def target(self) -> float:
        return float(self.settings.get("SETTINGS", "target_temperature"))

    @property
    def max_humidity(self) -> float:
        return float(self.settings.get("SETTINGS", "max_humidity"))

    def log_event(self, text: str, color=dashio.Color.WHITE):
        logging.info(text)
        self.controls["event_log"].add_event_data(dashio.EventData(text, color))

    def send_settings(self):
        """Send the settings to the Dash app."""
        self.controls["target"].knob_value = self.target
        self.controls["mode"].position = MODES.index(self.settings.get("SETTINGS", "mode"))
        self.controls["max_humidity"].slider_value = self.max_humidity
        self.controls["lights_on"].text = iso_time(self.settings.get("SETTINGS", "lights_on"))
        self.controls["lights_off"].text = iso_time(self.settings.get("SETTINGS", "lights_off"))

    def start(self):
        """Send the initial state and turn on Dash server storage for the history."""
        self.send_settings()
        for control_type, control_id in (
            (dashio.ControlName.TGRPH, self.controls["climate_graph"].control_id),
            (dashio.ControlName.LOG, self.controls["event_log"].control_id),
        ):
            self.device.storage_enable(control_type, control_id)
        self.log_event(f"Started in {self.settings.get('SETTINGS', 'mode')} mode", dashio.Color.LIME)
        self.started = True

    def lights_scheduled_on(self) -> bool:
        now = time.strftime("%H:%M")
        on, off = self.settings.get("SETTINGS", "lights_on"), self.settings.get("SETTINGS", "lights_off")
        if on <= off:
            return on <= now < off
        return now >= on or now < off  # The lights are on overnight.

    def set_outputs(self, heater: bool, fan: bool, lights: bool, reason: str):
        """Switch the outputs, and update the buttons and event log for any that changed."""
        for name, old, new in (("heater", self.heater, heater), ("fan", self.fan, fan), ("lights", self.lights, lights)):
            if old != new:
                self.log_event(f"{name.capitalize()} {'on' if new else 'off'} ({reason})", dashio.Color.YELLOW)
                self.controls[name].btn_state = dashio.ButtonState.ON if new else dashio.ButtonState.OFF
        self.heater, self.fan, self.lights = heater, fan, lights
        self.greenhouse.set_outputs(heater, fan, lights)

    def send_buttons(self):
        """Send the outputs' button states, e.g. as feedback when a button press is refused."""
        for name, state in (("heater", self.heater), ("fan", self.fan), ("lights", self.lights)):
            self.controls[name].btn_state = dashio.ButtonState.ON if state else dashio.ButtonState.OFF

    def auto_control(self):
        """The control loop for Auto mode."""
        heater = self.heater
        if self.temperature < self.target - HEATER_HYSTERESIS:
            heater = True
        elif self.temperature > self.target + HEATER_HYSTERESIS:
            heater = False

        too_hot = self.temperature > self.target + FAN_TEMPERATURE_OFFSET
        too_humid = self.humidity > self.max_humidity
        fan = self.fan
        if too_hot or too_humid:
            fan = True
        elif self.temperature < self.target + FAN_TEMPERATURE_OFFSET - 1.0 and self.humidity < self.max_humidity - HUMIDITY_HYSTERESIS:
            fan = False
        if fan:
            heater = False  # Don't heat air that is being vented.

        self.set_outputs(heater, fan, self.lights_scheduled_on(), "auto")

    def check_alarm(self, name: str, active: bool, message: str):
        """Send an alarm when a condition starts, and log when it clears."""
        if active and name not in self.active_alarms:
            self.active_alarms.add(name)
            self.alarm.send("Greenhouse Alarm", message)
            self.log_event(message, dashio.Color.RED)
        elif not active and name in self.active_alarms:
            self.active_alarms.remove(name)
            self.log_event(f"Cleared: {message}", dashio.Color.LIME)

    def control_tick(self, _) -> bool:
        """Read the sensors and update the outputs. Called by the Schedular every CONTROL_PERIOD seconds."""
        try:
            with self.lock:
                if not self.started:
                    self.start()
                self.temperature, self.humidity = self.greenhouse.read()
                self.controls["temperature"].dial_value = self.temperature
                self.controls["humidity"].dial_value = self.humidity
                self.controls["target"].knob_dial_value = self.temperature
                if round(self.humidity) != self.controls["max_humidity"].bar1_value:
                    self.controls["max_humidity"].bar1_value = round(self.humidity)  # Humidity against the limit.
                if self.auto:
                    self.auto_control()
                outputs = [name for name, on in (("heating", self.heater), ("venting", self.fan)) if on]
                state = " and ".join(outputs).capitalize() if outputs else "Idle"
                status = f"{self.settings.get('SETTINGS', 'mode')}: {state}"
                if status != self.controls["status"].text:
                    self.controls["status"].text = status
                self.check_alarm("frost", self.temperature < FROST_ALARM, f"Frost risk: {self.temperature}°C")
                self.check_alarm("heat", self.temperature > HEAT_ALARM, f"Too hot: {self.temperature}°C")
                self.check_alarm("humidity", self.humidity > 95.0, f"Humidity very high: {self.humidity}%")
        except Exception:  # pylint: disable=broad-except
            logging.exception("Control loop error")  # Keep the Schedular running.
        return True

    def graph_tick(self, _) -> bool:
        """Add a point to the time graphs. Called by the Schedular every GRAPH_PERIOD seconds."""
        try:
            with self.lock:
                climate_graph = self.controls["climate_graph"]
                climate_graph.line_dict["temperatures"].add_data_point([self.temperature, self.target])
                climate_graph.line_dict["humidity"].add_data_point(self.humidity)
                climate_graph.send_data()
        except Exception:  # pylint: disable=broad-except
            logging.exception("Graph error")
        return True

    def target_handler(self, msg):
        with self.lock:
            target = round(float(msg[3]), 1)
            self.settings.set("SETTINGS", "target_temperature", target)
            self.controls["target"].knob_value = target
            self.log_event(f"Target set to {target}°C")

    def mode_handler(self, msg):
        with self.lock:
            mode = MODES[int(msg[3])]
            self.settings.set("SETTINGS", "mode", mode)
            self.controls["mode"].position = int(msg[3])
            self.log_event(f"{mode} mode")

    def output_handler(self, msg):
        with self.lock:
            name = msg[2]
            if self.auto:
                self.log_event(f"Switch to Manual mode to control the {name}", dashio.Color.ORANGE)
                self.send_buttons()
                return
            outputs = {"heater": self.heater, "fan": self.fan, "lights": self.lights}
            outputs[name] = not outputs[name]
            self.set_outputs(outputs["heater"], outputs["fan"], outputs["lights"], "manual")

    def max_humidity_handler(self, msg):
        with self.lock:
            max_humidity = round(float(msg[3]))
            self.settings.set("SETTINGS", "max_humidity", max_humidity)
            self.controls["max_humidity"].slider_value = max_humidity
            self.log_event(f"Max humidity set to {max_humidity}%")

    def lights_time_handler(self, msg):
        with self.lock:
            key = "lights_on" if msg[2] == self.controls["lights_on"].control_id else "lights_off"
            lights_time = parse_time(msg[3])
            if lights_time is None:
                self.log_event(f"Not a time: {msg[3]}", dashio.Color.ORANGE)
            else:
                self.settings.set("SETTINGS", key, lights_time)
                self.log_event(f"{'Lights on' if key == 'lights_on' else 'Lights off'} at {lights_time}")
            self.controls[key].text = iso_time(self.settings.get("SETTINGS", key))

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
    parser = argparse.ArgumentParser(description="Greenhouse controller example for DashIO.")
    parser.add_argument("-i", "--ini", default="greenhouse.ini", help="Settings file. Defaults to greenhouse.ini")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(message)s")

    shutdown = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: shutdown.set())
    signal.signal(signal.SIGTERM, lambda *_: shutdown.set())

    controller = GreenhouseController(Settings(args.ini))
    while not shutdown.wait(1.0):
        pass
    controller.close()


if __name__ == "__main__":
    main()
