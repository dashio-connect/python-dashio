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
from __future__ import annotations

import copy
import hashlib
import json
import logging
import threading
import time

import shortuuid
import zmq

from .constants import BAD_CHARS, CONNECTION_PUB_URL
from .dash_store import DashStore, SDUSession
from .iotcontrol.alarm import Alarm
from .iotcontrol.control import Control
from .iotcontrol.device_view import DeviceView
from .iotcontrol.enums import ControlName
from .load_config import CONTROL_INSTANCE_DICT, decode_cfg64, encode_cfg64
from .package import make_packages

MAX_LAYOUT_COLUMNS = 3

logger = logging.getLogger(__name__)


class Device(threading.Thread):
    """Dashio Device

    Attributes
    ----------
    device_type : str
        The type of device (e.g. TempSensor, GPS...).
    device_id : str
        A unique identifier for this device
    device_name : str
        The name for this device (E.g. GlassHouse, MothersZimmerFrame...)

    Methods
    -------
    add_control(iot_control) :
        Add a control to the device.

    remove_control(iot_control) :
        Remove a control from the device.

    get_control(control_type: str, control_id: str):
        returns the instance of a control loaded into the device.

    remove_control(control_type, control_id) :
        Removes the control from the device.

    is_control_loaded(iot_control) :
         Returns boolean if the control is loaded in the device.

    add_cfg64(cfg: str | dict, column_no: int = 1):
        Loads a layout for Dash apps with column_no columns, adding any controls it defines.

    remove_cfg64(column_no: int):
        Removes the layout loaded for column_no.

    get_generated_cfg_dict():
        Returns the layout generated from the device's controls.

    add_all_c64_controls(c64_dict: dict, column_no: int = 1):
        Same as add_cfg64.

    set_reset_callback(callback) :
        Set a callback function that is called when the DashIO app asks the device to reset.

    unset_reset_callback() :
        Unset the reset callback.

    set_wifi_callback(callback) :
        Set a callback function that is called when the DashIO app provides wifi provisioning information.

    unset_wifi_callback() :
        Clears the wifi callback.

    set_dashio_callback(callback) :
        Set a callback function that is called when the DashIO app provides Dash server provisioning information.

    unset_dashio_callback() :
        Clears the set Dash callback.

    set_name_callback(callback) :
        Set a callback function that is called when the DashIO app provides Name provisioning information.

    unset_name_callback() :
        Clears the set Name callback.

    set_tcp_callback(callback) :
         Set a callback function that is called when the DashIO app provides TCP provisioning information.

    unset_tcp_callback() :
        Clears the set TCP callback.

    set_mqtt_callback(callback) :
        Set a callback function that is called when the DashIO app provides MQTT provisioning information.

    unset_mqtt_callback() :
        Clears the set MQTT callback.

    request_clock() :
        Requests UTC Timestamp from the Dash Server.

    set_clock_callback(callback):
        Specify a callback function to be called when The Dash server sends clock data.

    unset_clock_callback():
        Unset the clock rx callback.

    request_ota_build_number() :
        Requests requests latest build number for over the air updates from the Dash Server

    request_ota(build_number, chunk_number) :
        Requests requests latest ota build from the Dash Server.

    set_ota_callback(callback) :
        Specify a callback function to be called when The Dash server sends ota data.
    """

    def _on_message(self, payload):
        data = str(payload, "utf-8").strip()
        command_array = data.split("\n")
        reply = ""
        for command in command_array:
            try:
                reply += self._on_command(command.strip())
            except TypeError:
                pass
        return reply

    def _on_command(self, data):
        data_array = data.split("\t")
        rx_device_id = data_array[0]
        if rx_device_id == "WHO":
            return self._who_message()
        if rx_device_id != self.device_id:
            return ""
        try:
            ctrl_type = data_array[1]
        except IndexError:
            return ""
        if ctrl_type in self._device_commands_dict:
            return self._device_commands_dict[ctrl_type](data_array)
        try:
            reply = self.controls_dict[ctrl_type + "\t" + data_array[2]]._message_rx_event(data_array)
        except (KeyError, IndexError):
            return ""
        if ctrl_type in ("MENU", "BTGP"):
            # Tapping a Menu or ButtonGroup asks for the current values of its controls.
            reply += self._get_child_states(data_array[2])
        return reply.replace("{device_id}", self.device_id)

    def _get_child_states(self, parent_id: str) -> str:
        """The current state of the controls in a Menu or ButtonGroup, packaged as PKG messages.

        The controls are found by parent: controls added to the Menu or ButtonGroup in code, and controls whose
        parent is it in a loaded layout.
        """
        children = {
            key for key, control in self.controls_dict.items()
            if isinstance(control, Control) and any(cfg.cfg.get("parentID") == parent_id for cfg in control._configs)
        }
        for layout in self._column_cfgs.values():
            for control_type, entries in layout.items():
                if isinstance(entries, list):
                    children.update(f"{control_type}\t{entry.get('controlID')}" for entry in entries if entry.get("parentID") == parent_id)
        states = ""
        for key in sorted(children):
            if key not in self.controls_dict:
                continue
            try:
                states += self.controls_dict[key].get_state()
            except (TypeError, KeyError):
                pass
        return make_packages(self.device_id, states.replace("{device_id}", self.device_id))

    def _make_connect(self, _):
        return self._device_id_str + "\tCONNECT\n"

    def _menu_only_controls(self) -> set:
        """The keys of the controls that are inside a Menu or ButtonGroup everywhere they appear.

        Their values are sent when the Menu or ButtonGroup is tapped, so they're left out of the STATUS reply. A
        control that is on a DeviceView anywhere, in its own configs or in any loaded layout, isn't included.
        """
        containers = {control.control_id for control in self.controls_dict.values() if control.ctrl_type in ("MENU", "BTGP")}
        placements = {}
        for key, control in self.controls_dict.items():
            if isinstance(control, Control):
                placements[key] = [cfg.cfg.get("parentID", "") for cfg in control._configs]
        for layout in self._column_cfgs.values():
            for control_type, entries in layout.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if control_type in ("MENU", "BTGP"):
                        containers.add(entry.get("controlID"))
                    key = f"{control_type}\t{entry.get('controlID')}"
                    if key in placements:
                        placements[key].append(entry.get("parentID", ""))
        return {key for key, parents in placements.items() if parents and all(parent in containers for parent in parents)}

    def _make_status(self, _):
        menu_only = self._menu_only_controls()
        states = ""
        for key, value in self.controls_dict.items():
            if key in menu_only:
                continue  # Sent when its Menu or ButtonGroup is tapped.
            try:
                states += value.get_state().replace("{device_id}", self.device_id)
            except (TypeError, KeyError):
                pass
        # The controls' states are packaged into PKG messages, so a device with many controls sends a few messages.
        return f"\t{self.device_id}\tNAME\t{self._device_name}\n" + make_packages(self.device_id, states)

    def _add_generated_cfg(self, cfg: dict, data, layout_controls: bool):
        """Add the CFG of the device's controls to cfg. layout_controls selects the controls that make up the
        layout (iotcontrol Controls), otherwise the non layout ones such as connection setup controls."""
        for control in self.controls_dict.values():
            if control.ctrl_type == "ALM" or isinstance(control, Control) != layout_controls:
                continue
            control_cfg = control.get_cfg64(data)
            # Connection setup controls, e.g. BLE and DASHIO, have a single CFG dict rather than a list.
            if isinstance(control_cfg, dict):
                cfg[control.ctrl_type] = control_cfg
                continue
            cfg.setdefault(control.ctrl_type, []).extend(control_cfg)

    def get_generated_cfg_dict(self) -> dict:
        """Returns the CFG dict generated from the device's controls.

        This is the layout sent to the Dash app when no column layouts are loaded with add_cfg64().
        Encode it with encode_cfg64() to export it, e.g. to load it later as a column layout.
        """
        cfg = {"CFG": copy.deepcopy(self._cfg)}
        self._add_generated_cfg(cfg, [], layout_controls=True)
        return cfg

    def get_cfg_hash(self) -> str:
        """Returns a hash of the CFG the device sends to Dash apps of every column count, without cfgRev.

        The Dash app only fetches a new CFG when the device's cfgRev changes, so cfgRev must be increased
        whenever the CFG changes. Code that builds its layouts when it starts can save this hash with cfgRev,
        and increase cfgRev when the hash changes.
        """
        cfgs = []
        for num_columns in range(1, MAX_LAYOUT_COLUMNS + 1):
            cfg = self._get_layout(["", self.device_id, "", str(num_columns)])
            del cfg["CFG"]["cfgRev"]
            cfgs.append(cfg)
        return hashlib.sha256(json.dumps(cfgs, sort_keys=True).encode()).hexdigest()

    def _select_layout_column(self, num_columns: int) -> int | None:
        """The loaded layout to use for a Dash app with num_columns: the largest column not bigger than
        num_columns, otherwise the smallest. None if no layouts are loaded."""
        if not self._column_cfgs:
            return None
        smaller = [column for column in self._column_cfgs if column <= num_columns]
        return max(smaller) if smaller else min(self._column_cfgs)

    def _get_layout(self, data) -> dict:
        """The CFG dict to send in reply to a Dash app CFG request."""
        try:
            num_columns = int(data[3])
        except (IndexError, ValueError):
            num_columns = 1
        column_no = self._select_layout_column(num_columns)
        if column_no is None:
            cfg = {"CFG": copy.deepcopy(self._cfg)}
            self._add_generated_cfg(cfg, data, layout_controls=True)
        else:
            cfg = copy.deepcopy(self._column_cfgs[column_no])
            cfg["CFG"] = copy.deepcopy(self._cfg)
            cfg["CFG"]["numDeviceViews"] = len(cfg.get("DVVW", []))
            for control_type, entries in cfg.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    control = self.controls_dict.get(f"{control_type}\t{entry.get('controlID')}")
                    if isinstance(control, Control):
                        entry.update(control._cfg_overrides())
        self._add_generated_cfg(cfg, data, layout_controls=False)
        return cfg

    def _make_cfg64(self, data):
        try:
            dashboard_id = data[2]
        except IndexError:
            return ""
        c64_json = encode_cfg64(self._get_layout(data))
        return self._device_id_str + f"\tCFG\t{dashboard_id}\tC64\t{c64_json}\n"

    def _server_clk(self, data):
        if self._clk_rx_callback is not None:
            self._clk_rx_callback(data)

    def _server_ota(self, data):
        if self._ota_rx_callback is not None:
            self._ota_rx_callback(data)

    def _make_cfg(self, data):
        try:
            dashboard_id = data[2]
            #  no_views = data[3]
        except IndexError:
            return ""
        layout = self._get_layout(data)
        reply = self._device_id_str + f"\tCFG\t{dashboard_id}\tDVCE\t{json.dumps(layout.pop('CFG'))}\n"
        dvvw_str = ""
        for control_type, entries in layout.items():
            if not isinstance(entries, list):
                entries = [entries]
            for entry in entries:
                cfg_str = self._device_id_str + f"\tCFG\t{dashboard_id}\t{control_type}\t{json.dumps(entry)}\n"
                if control_type == "DVVW":
                    dvvw_str += cfg_str
                else:
                    reply += cfg_str
        reply += dvvw_str
        return reply

    def _send_alarm(self, alarm_id, message_header, message_body):
        payload = self._device_id_str + f"\tALM\t{alarm_id}\t{message_header}\t{message_body}\n"
        logger.debug("ALARM: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ALL", payload.encode('utf-8')])

    def _send_data(self, data: str):
        if not data:
            return
        reply_send = ""
        if isinstance(data, str):
            reply_send = data.replace("{device_id}", self.device_id)
        elif isinstance(data, list):
            reply_send = "\t" + "\t".join(data) + "\n"
        try:
            self.tx_zmq_pub.send_multipart([b"ALL", reply_send.encode('utf-8')])
        except zmq.error.ZMQError:
            pass

    def storage_enable(self, control_type: ControlName, control_id: str) -> None:
        """Turn On Dash Server Storage for the Event Log, Map, or Time Graph control."""
        key = f"{control_type.value}\t{control_id}"
        if key not in self.controls_dict:
            return
        if control_type not in [ControlName.LOG, ControlName.MAP, ControlName.TGRPH]:
            return
        payload = self._device_id_str + f"\tSTE\t{control_type.value}\t{control_id}\n"
        logger.debug("STORAGE ENABLE: %s", payload)
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def _who_message(self) -> str:
        """The WHO message, used to reply to WHO and to announce the device.

        It always includes cfgRev: the Dash app takes a WHO without one as cfgRev 0.
        """
        return self._device_id_str + f"\tWHO\t{self.device_type}\t{self.device_name}\t{self._cfg['cfgRev']}\n"

    def _send_announce(self):
        payload = self._who_message()
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def request_clock(self):
        """Requests UTC Timestamp from the Dash Server
        """
        payload = self._device_id_str + "\tCLK\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def request_ota_build_number(self):
        """Requests requests latest build number for over the air updates from the Dash Server
        """
        payload = self._device_id_str + f"\tOTA\t{self.device_type}\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def request_ota(self, build_number, chunk_number):
        """Requests requests latest ota build from the Dash Server
        """
        payload = self._device_id_str + f"\tOTA\t{self.device_type}\t{build_number}\t{chunk_number}\n"
        logger.debug("ANNOUNCE: %s", payload.rstrip())
        self.tx_zmq_pub.send_multipart([b"ANNOUNCE", payload.encode('utf-8')])

    def is_control_loaded(self, control_type, control_id: str) -> bool:
        """Is the control loaded in the device?"""
        key = f"{control_type}\t{control_id}"
        return key in self.controls_dict

    def add_cfg64(self, cfg: str | dict, column_no: int = 1):
        """Load a layout for Dash apps that report column_no columns.

        The Dash app reports its screen size in columns: 1 for phones, 2 for fold out phones and 3 for tablets.
        A layout can be loaded for each. When the app asks for a CFG it is sent the layout for its column count,
        or if there isn't one, the largest layout with fewer columns, otherwise the smallest layout. The layout
        generated from the device's controls is only sent when no layouts are loaded.

        Controls in the layout that the device doesn't have are instantiated from the layout and added.

        Parameters
        ----------
        cfg : str | dict
            A CFG64 string, e.g. exported by the Dash app, or a dict decoded from one with decode_cfg64.
        column_no : int, optional
            The column count the layout is for, 1 to 3. Defaults to 1.
        """
        if not 1 <= column_no <= MAX_LAYOUT_COLUMNS:
            raise ValueError(f"column_no must be 1 to {MAX_LAYOUT_COLUMNS}, not {column_no}")
        cfg_dict = decode_cfg64(cfg) if isinstance(cfg, str) else copy.deepcopy(cfg)
        for control_type, control_list in cfg_dict.items():
            if isinstance(control_list, list):
                for control in control_list:
                    if not self.is_control_loaded(control_type, control['controlID']):
                        self.add_control(CONTROL_INSTANCE_DICT[control_type].from_cfg_dict(control))
            elif control_type == "CFG" and isinstance(control_list, dict):
                if 'name' in control_list.get('deviceSetup', '').lower().split(','):
                    self._set_device_setup("name", True)
                    self.set_name_callback(self._name_callback)
        self._column_cfgs[column_no] = cfg_dict

    def remove_cfg64(self, column_no: int):
        """Remove the layout loaded for column_no. Controls added with the layout stay on the device."""
        self._column_cfgs.pop(column_no, None)

    def add_all_c64_controls(self, c64_dict: dict, column_no=1):
        """Loads a layout and its controls into the device. Same as add_cfg64()."""
        self.add_cfg64(c64_dict, column_no)

    def add_control(self, iot_control):
        """Add a control to the device.

        Parameters
        ----------
            iot_control : iotControl
        """
        try:
            if isinstance(iot_control, Alarm):
                iot_control.add_transmit_message_callback(self._send_alarm)
            else:
                iot_control.add_transmit_message_callback(self._send_data)
        except AttributeError:
            pass
        key = f"{iot_control.ctrl_type}\t{iot_control.control_id}"

        if key not in self.controls_dict:
            if isinstance(iot_control, DeviceView):
                self._cfg["numDeviceViews"] += 1
            if self.store is not None and iot_control.ctrl_type in ("TGRPH", "LOG", "MAP"):
                iot_control._store = self.store
            self.controls_dict[key] = iot_control
            return True
        return False

    def get_control(self, control_type: ControlName, control_id: str):
        """Get the control instance.

        Parameters
        ----------
            control_type : ControlName
                The type of control
            control_id : str
                The controlID of the control

        Returns
        -------
            Control | None
                The requested control or None if the control isn't available.
        """
        key = f"{control_type.value}\t{control_id}"
        return self.controls_dict.get(key, None)

    def remove_control(self, iot_control):
        """Remove a control a control to the device.

        Parameters
        ----------
            iot_control : iotControl
        """
        if isinstance(iot_control, DeviceView):
            self._cfg["numDeviceViews"] -= 1
        key = f"{iot_control.ctrl_type}\t{iot_control.control_id}"
        if key in self.controls_dict:
            del self.controls_dict[key]

    def _set_device_setup(self, control_name: str, settable: bool):
        if settable:
            self._device_commands_dict[control_name.upper()] = getattr(self, '_' + control_name + '_rx_event', None)
            if control_name not in self._device_setup_list:
                self._device_setup_list.append(control_name)
        else:
            try:
                del self._device_commands_dict[control_name.upper()]
            except KeyError:
                pass
            try:
                self._device_setup_list.remove(control_name)
            except ValueError:
                pass
        self._cfg["deviceSetup"] = ','.join(self._device_setup_list)

    def _add_action_device_setup(self, settable: bool):
        if settable:
            if 'actn' not in self._device_setup_list:
                self._device_setup_list.append('actn')
        else:
            try:
                del self._device_commands_dict['actn']
            except KeyError:
                pass
            try:
                self._device_setup_list.remove('actn')
            except ValueError:
                pass
        self._cfg["deviceSetup"] = ','.join(self._device_setup_list)

    def set_clock_callback(self, callback):
        """
        Specify a callback function to be called when The Dash server sends clock data.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from dash server.
                The callback must return a Boolean indicating success.
        """
        self._clk_rx_callback = callback

    def unset_clock_callback(self):
        """
        Unset the clock rx callback.
        """
        self._ota_rx_callback = None

    def set_ota_callback(self, callback):
        """
        Specify a callback function to be called when The Dash server sends ota data.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from dash server.
                The callback must return a Boolean indicating success.
        """
        self._clk_rx_callback = callback

    def unset_ota_callback(self):
        """
        Unset the ota rx callback.
        """
        self._ota_rx_callback = None

    def set_reset_callback(self, callback):
        """
        Specify a callback function to be called when the Dash app asks the device to reset.

        Setting it tells the Dash app that the device can be reset. The device replies to the Dash app before
        calling the callback, as the protocol requires, so the callback should reset the device, e.g. after a
        short delay so the reply reaches the app.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from the Dash app.
        """
        self._set_device_setup("rst", True)
        self._rst_rx_callback = callback

    def unset_reset_callback(self):
        """
        Unset the reset callback function.
        """
        self._set_device_setup("rst", False)
        self._rst_rx_callback = None

    def _rst_rx_event(self, msg) -> str:
        if self._rst_rx_callback is not None:
            data = self._device_id_str + "\tRST\n"
            self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
            self._rst_rx_callback(msg)
        return ""

    def set_wifi_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets wifi parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("wifi", True)
        self._wifi_rx_callback = callback

    def unset_wifi_callback(self):
        """
        Unset the wifi_rx_callback.
        """
        self._set_device_setup("wifi", False)
        self._wifi_rx_callback = None

    def _wifi_rx_event(self, msg) -> str:
        if self._wifi_rx_callback is not None:
            if self._wifi_rx_callback(msg):
                data = self._device_id_str + "\tWIFI\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def set_dashio_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets dashio parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("dashio", True)
        self._dashio_rx_callback = callback

    def unset_dashio_callback(self):
        """
        Unset the dashio callback function.
        """
        self._set_device_setup("dashio", False)
        self._dashio_rx_callback = None

    def _dashio_rx_event(self, msg):
        if self._dashio_rx_callback is not None:
            if self._dashio_rx_callback(msg):
                data = self._device_id_str + "\tDASHIO\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def set_name_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets dashio parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return the new name.
        """
        self._set_device_setup("name", True)
        self._name_rx_callback = callback

    def unset_name_callback(self):
        """
        Unset the name callback function.
        """
        self._set_device_setup("name", False)
        self._name_rx_callback = None
        # Keep answering requests for the device name.
        self._device_commands_dict['NAME'] = self._name_rx_event

    def _name_callback(self, msg) -> str:
        logger.debug("Name msg: %s", msg)
        return msg[2]

    def _name_rx_event(self, msg) -> str:
        if len(msg) < 3 or not msg[2]:
            # An empty name is a request for the current name.
            return self._device_id_str + f"\tNAME\t{self._device_name}\n"
        if self._name_rx_callback is not None:
            name = self._name_rx_callback(msg)
            if name:
                self._device_name = name
                data = self._device_id_str + f"\tNAME\t{name}\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def set_tcp_callback(self, callback):
        """Specify a callback function to be called when IoTDashboard sets tcp parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("tcp", True)
        self._tcp_rx_callback = callback

    def unset_tcp_callback(self):
        """
        Unset the tcp callback function.
        """
        self._set_device_setup("tcp", False)
        self._tcp_rx_callback = None

    def _tcp_rx_event(self, msg):
        if self._tcp_rx_callback is not None:
            if self._tcp_rx_callback(msg):
                data = self._device_id_str + "\tTCP\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
            return ""

    def set_mqtt_callback(self, callback):
        """
        Specify a callback function to be called when IoTDashboard sets mqtt parameters.

        Parameters
        ----------
            callback:
                The callback function. It will be invoked with one argument, the msg from IoTDashboard.
                The callback must return a Boolean indicating success.
        """
        self._set_device_setup("mqtt", True)
        self._mqtt_rx_callback = callback

    def unset_mqtt_callback(self):
        """
        Unset the mqtt callback function.
        """
        self._set_device_setup("mqtt", False)
        self._mqtt_rx_callback = None

    def _mqtt_rx_event(self, msg):
        if self._mqtt_rx_callback is not None:
            if self._mqtt_rx_callback(msg):
                data = self._device_id_str + "\tMQTT\n"
                self.tx_zmq_pub.send_multipart([b"ALL", data.encode('utf-8')])
        return ""

    def register_connection(self, connection):
        """Connections registered here"""
        if connection.zmq_connection_uuid not in self.connections_list:
            logger.debug("DEVICE REG CONECTION")
            self.connections_list.append(connection.zmq_connection_uuid)
            self.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=connection.zmq_connection_uuid))
            connection.rx_zmq_sub.connect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

    def de_register_connection(self, connection):
        """Connections unregistered here"""
        if connection.zmq_connection_uuid in self.connections_list:
            logger.debug("DEVICE DE-REG CONECTION")
            self.connections_list.remove(connection.zmq_connection_uuid)
            self.rx_zmq_sub.disconnect(CONNECTION_PUB_URL.format(id=connection.zmq_connection_uuid))
            connection.rx_zmq_sub.disconnect(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))

    def __init__(
        self,
        device_type: str,
        device_id: str,
        device_name: str,
        cfg_dict: dict | None = None,
        context: zmq.Context | None = None,
        store: DashStore | None = None
    ) -> None:
        """DashDevice

        Parameters
        ----------
            device_type : str
                A Short description of the device type.
            device_id : str
                A unique identifier for this device
            device_name : str
                The name for this device
            cfg_dict : dict optional
                A layout decoded with decode_cfg64, loaded for 1 column. Or a dict of column number to layout,
                each a CFG64 string or decoded dict, e.g. {1: phone_cfg64, 3: tablet_cfg64}. The layouts are
                loaded with add_cfg64() and cfgRev is set from them. Defaults to None.
            context : optional
                ZMQ context. Defaults to None.
            store : DashStore, optional
                Stores the data of the device's TimeGraph, EventLog and Map controls, answers the Dash app's history
                requests from it, and sends the Dash server the data it is missing when the device connects.
                Defaults to None, which keeps a short history of each control in memory.
        """
        threading.Thread.__init__(self, daemon=True)
        self.store = store
        self._sdu = None

        self.zmq_connection_uuid = "DVCE:" + shortuuid.uuid()
        self._b_zmq_connection_uuid = self.zmq_connection_uuid.encode()
        self.context = context or zmq.Context.instance()
        self._wifi_rx_callback = None
        self._dashio_rx_callback = None
        self._name_rx_callback = None
        self._tcp_rx_callback = None
        self._mqtt_rx_callback = None
        self._clk_rx_callback = None
        self._ota_rx_callback = None
        self.device_type = device_type.translate(BAD_CHARS)
        self.device_id = device_id.translate(BAD_CHARS)
        self._b_device_id = self.device_id.encode('utf-8')
        self._device_name = device_name.strip()
        self._device_setup_list = []
        self.connections_list = []
        self._device_commands_dict = {}
        self._device_commands_dict['CONNECT'] = self._make_connect
        self._device_commands_dict['STATUS'] = self._make_status
        self._device_commands_dict['CFG'] = self._make_cfg64
        self._device_commands_dict['CLK'] = self._server_clk
        self._device_commands_dict['OTA'] = self._server_ota
        self._device_commands_dict['NAME'] = self._name_rx_event
        if store is not None:
            self._sdu = SDUSession(device_id.translate(BAD_CHARS), store, self._store_registry, self._send_to_dash_server)
            self._device_commands_dict['DATA'] = self._data_rx
        self._rst_rx_callback = None
        self.controls_dict = {}
        self._cfg = {}
        self._cfg["deviceSetup"] = ''
        self._cfg["cfgRev"] = 1
        self._device_id_str = f"\t{device_id}"
        self._cfg["numDeviceViews"] = 0
        self._column_cfgs = {}
        if cfg_dict is not None:
            column_cfgs = cfg_dict if all(isinstance(key, int) for key in cfg_dict) else {1: cfg_dict}
            for column_no, cfg in column_cfgs.items():
                self.add_cfg64(cfg, column_no)
            self._cfg["cfgRev"] = max(cfg.get('CFG', {}).get('cfgRev', 1) for cfg in self._column_cfgs.values())
            self.use_cfg64()

        self.running = True
        time.sleep(0.5)
        self.start()

    def use_cfg64(self):
        """Generate a CFG64 formated CFG message
        """
        self._device_commands_dict['CFG'] = self._make_cfg64

    def use_cfg(self):
        """Generate JSON formated CFG messages
        """
        self._device_commands_dict['CFG'] = self._make_cfg

    @property
    def number_of_device_views(self) -> int:
        """Number of device views registered for the device

        Returns
        -------
        int
            Number of device views
        """
        return self._cfg["numDeviceViews"]

    @number_of_device_views.setter
    def number_of_device_views(self, val: int):
        self._cfg["numDeviceViews"] = val

    @property
    def config_revision(self) -> int:
        """Sets the cfgRev number. Increment this number to indicate a new CFG

        Returns
        -------
        int
            The cfgRev number
        """
        return self._cfg["cfgRev"]

    @config_revision.setter
    def config_revision(self, val: int):
        self._cfg["cfgRev"] = val

    def inc_config_revision(self):
        """Incements the configuration revision."""
        if "cfgRev" in self._cfg:
            self._cfg["cfgRev"] = self._cfg["cfgRev"] + 1
        else:
            self._cfg["cfgRev"] = 1

    @property
    def device_name(self) -> str:
        """Device name

        Returns
        -------
        str
            The device name
        """
        return self._device_name

    @device_name.setter
    def device_name(self, val: str):
        self._device_name = val
        self._send_data(f"\t{{device_id}}\tNAME\t{self._device_name}\t")

    def close(self):
        """Close the device"""
        self.running = False

    def _local_command(self, msg_dict):
        logging.debug("LOCAL COMMAND: %s", msg_dict)
        if msg_dict.get('deviceID', '') != self.device_id:
            return
        if msg_dict.get('msgType', '') == 'send_announce':
            self._send_announce()
        elif msg_dict.get('msgType', '') == 'send_store_request' and self._sdu is not None:
            request = self._sdu.start()
            if request:
                logger.debug("ANNOUNCE: %s", request.rstrip())
                self.tx_zmq_pub.send_multipart([b"ANNOUNCE", request.encode('utf-8')])

    def set_store_sync_callback(self, callback):
        """Set a callback for the end of each sync of the device's DashStore with the Dash server.

        A sync starts each time the device connects to the Dash server. The callback is called with True when
        the server has everything, and False when the sync fails, e.g. the server doesn't reply. A device that
        only connects now and then can disconnect in the callback, e.g. with DashConnection.disconnect().

        Parameters
        ----------
        callback : Callable[[bool], None]
            Called on the device's thread.
        """
        if self._sdu is None:
            raise ValueError("The device has no DashStore")
        self._sdu.on_finished = callback

    def unset_store_sync_callback(self):
        """Clears the store sync callback."""
        if self._sdu is not None:
            self._sdu.on_finished = None

    def _send_to_dash_server(self, message: str):
        """Send a message to the Dash server connections only."""
        self.tx_zmq_pub.send_multipart([b"DASH", message.encode('utf-8')])

    def _data_rx(self, data_array) -> str:
        """DATA messages from the Dash server: the SDU (store and forward) session."""
        if len(data_array) < 4 or data_array[2] != "SDU":
            return ""
        if data_array[3] == "REQUEST" and len(data_array) > 4:
            self._sdu.request(data_array[4])
        elif data_array[3] == "ACK":
            self._sdu.ack()
        elif data_array[3] == "NACK":
            self._sdu.nack()
        return ""

    def _store_registry(self) -> list[dict]:
        """The device's stored TimeGraph lines, Map tracks and EventLogs, in SDU controlInfo order."""
        lines, tracks, logs = [], [], []
        for control in list(self.controls_dict.values()):
            if control.ctrl_type == "TGRPH":
                for line_id, line in list(control.line_dict.items()):
                    lines.append({
                        "type": "TGRPH", "id": control.control_id, "sub": line_id, "name": line.name,
                        "lineType": line.line_type.value, "color": "" if line.color is None else str(line.color.value),
                        "axis": "R" if line.axis_side == "right" else "L"
                    })
            elif control.ctrl_type == "MAP":
                track_ids = self.store.sub_ids("MAP", control.control_id)
                track_ids += [track_id for track_id in control.tracks if track_id not in track_ids]
                for track_id in track_ids:
                    track = control.tracks.get(track_id)
                    tracks.append({
                        "type": "MAP", "id": control.control_id, "sub": track_id, "name": track.text if track else "",
                        "color": str(track.color.value) if track else ""
                    })
            elif control.ctrl_type == "LOG":
                logs.append({"type": "LOG", "id": control.control_id, "sub": ""})
        return lines + tracks + logs

    def run(self):
        # Continue the network loop, exit when an error occurs

        self.tx_zmq_pub = self.context.socket(zmq.PUB)
        self.tx_zmq_pub.bind(CONNECTION_PUB_URL.format(id=self.zmq_connection_uuid))
        self.rx_zmq_sub = self.context.socket(zmq.SUB)
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"\tWHO")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, b"COMMAND")
        self.rx_zmq_sub.setsockopt(zmq.SUBSCRIBE, self._b_zmq_connection_uuid)
        self.rx_zmq_sub.setsockopt_string(zmq.SUBSCRIBE, "\t" + self.device_id)

        poller = zmq.Poller()
        poller.register(self.rx_zmq_sub, zmq.POLLIN)

        while self.running:
            try:
                socks = dict(poller.poll(100))
            except zmq.error.ContextTerminated:
                break
            if self._sdu is not None:
                self._sdu.poll()
            if self.rx_zmq_sub in socks:
                try:
                    [data, msg_from] = self.rx_zmq_sub.recv_multipart()
                except ValueError:
                    logger.debug("Device value error")
                #  logger.debug("DEVICE RX: %s ,%s", msg_from, data)
                if data == b"COMMAND":
                    msg_dict = json.loads(msg_from)
                    self._local_command(msg_dict)
                    continue
                reply = self._on_message(data)
                if reply != "":
                    #  logger.debug("DEVICE TX: %s ,%s", msg_from, data)
                    self.tx_zmq_pub.send_multipart([msg_from, reply.encode('utf-8')])
        # Only close the device's sockets. The context is shared with other devices and connections.
        self.tx_zmq_pub.close()
        self.rx_zmq_sub.close()
