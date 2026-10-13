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

import datetime
import json
import logging
import sqlite3
import threading
import time
from typing import Callable, NamedTuple

logger = logging.getLogger(__name__)

SDU_MAX_PACKET_LENGTH = 4096  # Bytes, including the message header and hash, as in the DashIO firmware.
SDU_ACK_TIMEOUT = 10.0  # Seconds to wait for the Dash server to ACK a packet before sending it again.
SDU_REQUEST_TIMEOUT = 30.0  # Seconds to wait for the Dash server's SDU REQUEST after the timestamp request.
_AGE_PRUNE_INTERVAL = 60.0  # Seconds between deleting entries older than max_days.


def fnv1a_64(data: bytes) -> int:
    """64-bit FNV-1a hash, as the DashIO firmware uses for SDU UPDATE packets."""
    value = 0xcbf29ce484222325
    for byte in data:
        value = ((value ^ byte) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return value


def _epoch(timestamp: datetime.datetime | int | float) -> int:
    if isinstance(timestamp, datetime.datetime):
        return int(timestamp.timestamp())
    return int(timestamp)


def _json(value) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


class StoreEntry(NamedTuple):
    """An entry in a DashStore."""
    entry_id: int
    control_type: str
    control_id: str
    sub_id: str
    timestamp: int
    data: object

    @property
    def time(self) -> datetime.datetime:
        """The entry's timestamp as a UTC datetime."""
        return datetime.datetime.fromtimestamp(self.timestamp, datetime.timezone.utc)


class DashStore:
    """Persistent storage for TimeGraph, EventLog and Map data, in an sqlite database.

    Give it to a Device with Device(..., store=DashStore("device.db")). The device's TimeGraph, EventLog and Map
    controls then record their data in it, answer the Dash app's history requests from it, and send the data the
    Dash server is missing when the device connects (store and forward), as the DashIO firmware does.
    """

    def __init__(self, path: str = ":memory:", max_entries: int = 100000, max_days: float | None = 31):
        """Persistent storage for TimeGraph, EventLog and Map data.

        Parameters
        ----------
        path : str, optional
            The sqlite database file. Defaults to ":memory:", which isn't kept after the program stops.
        max_entries : int, optional
            The most entries kept. The oldest are deleted to make room. Defaults to 100000.
        max_days : float | None, optional
            Entries older than this many days are deleted. None keeps them, up to max_entries. Defaults to 31.
        """
        self.max_entries = max_entries
        self.max_days = max_days
        self._lock = threading.Lock()
        self._last_age_prune: float | None = None  # time.monotonic() of the last delete of old entries.
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, control_type TEXT NOT NULL, control_id TEXT NOT NULL, "
            "sub_id TEXT NOT NULL, ts INTEGER NOT NULL, data TEXT NOT NULL)"
        )
        self._db.execute("CREATE INDEX IF NOT EXISTS entries_control ON entries (control_type, control_id, sub_id, ts)")
        self._db.execute("CREATE INDEX IF NOT EXISTS entries_ts ON entries (ts)")

    def add(self, control_type: str, control_id: str, sub_id: str, timestamp: datetime.datetime | int, data) -> None:
        """Add an entry, deleting the oldest entries if the store is over its limits.

        Parameters
        ----------
        control_type : str
            "TGRPH", "LOG" or "MAP".
        control_id : str
            The control's ID.
        sub_id : str
            The TimeGraph line ID or Map track ID, "" for an EventLog.
        timestamp : datetime | int
            The time of the entry, as a datetime or seconds since the epoch.
        data
            The entry's data. It must be JSON serialisable.
        """
        with self._lock:
            cursor = self._db.execute(
                "INSERT INTO entries (control_type, control_id, sub_id, ts, data) VALUES (?, ?, ?, ?, ?)",
                (control_type, control_id, sub_id, _epoch(timestamp), _json(data)),
            )
            if self.max_entries:
                self._db.execute("DELETE FROM entries WHERE id <= ?", (cursor.lastrowid - self.max_entries,))
            now = time.monotonic()
            if self.max_days is not None and (self._last_age_prune is None or now - self._last_age_prune >= _AGE_PRUNE_INTERVAL):
                self._last_age_prune = now
                self._db.execute("DELETE FROM entries WHERE ts < ?", (int(time.time() - self.max_days * 86400),))

    def entries(self, control_type: str, control_id: str, sub_id: str = "", after: datetime.datetime | int = 0) -> list[StoreEntry]:
        """The entries for a control's line, track or log that are later than after, oldest first."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM entries WHERE control_type = ? AND control_id = ? AND sub_id = ? AND ts > ? ORDER BY ts, id",
                (control_type, control_id, sub_id, _epoch(after)),
            ).fetchall()
        return [self._entry(row) for row in rows]

    def entries_after_id(self, entry_id: int, limit: int = 500) -> list[StoreEntry]:
        """Up to limit entries added after the entry with entry_id, in the order they were added."""
        with self._lock:
            rows = self._db.execute("SELECT * FROM entries WHERE id > ? ORDER BY id LIMIT ?", (entry_id, limit)).fetchall()
        return [self._entry(row) for row in rows]

    def sub_ids(self, control_type: str, control_id: str) -> list[str]:
        """The line or track IDs stored for a control, in the order they were first stored."""
        with self._lock:
            rows = self._db.execute(
                "SELECT sub_id FROM entries WHERE control_type = ? AND control_id = ? GROUP BY sub_id ORDER BY MIN(id)",
                (control_type, control_id),
            ).fetchall()
        return [row[0] for row in rows]

    def clear(self) -> None:
        """Delete every entry."""
        with self._lock:
            self._db.execute("DELETE FROM entries")

    def close(self) -> None:
        """Close the database."""
        with self._lock:
            self._db.close()

    def __len__(self) -> int:
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

    @staticmethod
    def _entry(row) -> StoreEntry:
        return StoreEntry(row[0], row[1], row[2], row[3], row[4], json.loads(row[5]))


def _sdu_number(value) -> str | None:
    """Format a number as the DashIO firmware does: integers with %d, others with %.6f."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return "NaN"
    if isinstance(value, str) and value.lstrip("-").isdigit():
        return str(int(value))
    return f"{number:.6f}"


def format_sdu_data(entry: StoreEntry) -> str | None:
    """The data of an entry, formatted for an SDU UPDATE packet, or None if it can't be sent.

    TimeGraph data is returned as a quoted JSON string, EventLog and Map data as JSON objects, as the DashIO
    firmware sends them.
    """
    from .iotcontrol.control import format_value  # pylint: disable=import-outside-toplevel

    data = entry.data
    if entry.control_type == "TGRPH":
        if isinstance(data, bool):
            text = "T" if data else "F"
        elif isinstance(data, list):
            text = "[" + ",".join(format_value(item) for item in data) + "]"
        else:
            text = _sdu_number(data)
            if text is None:
                return None
        return _json(text)
    if entry.control_type == "LOG":
        return _json({"color": data.get("color", ""), "lines": data.get("lines", [])})
    if entry.control_type == "MAP":
        location = {"time": entry.time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        for key in ("latitude", "longitude", "altitude", "avgeSpeed", "peakSpeed", "course", "distance"):
            if key in data:
                number = _sdu_number(data[key])
                location[key] = data[key] if number is None else _RawNumber(number)
        return _json_with_numbers(location)
    return None


class _RawNumber(str):
    """A number already formatted, written into JSON without quotes."""


def _json_with_numbers(value: dict) -> str:
    return "{" + ",".join(f"{_json(key)}:{item if isinstance(item, _RawNumber) else _json(item)}" for key, item in value.items()) + "}"


class SDUSession:
    """Sends a device's stored data to the Dash server: the DashIO store and forward (SDU) protocol.

    1. When the device connects to the Dash server, it sends a timestamp request listing its stored lines,
       tracks and logs (timestamp_request()).
    2. The server replies with an SDU REQUEST giving, for each, the newest timestamp it holds, and sendInfo where
       it needs the line or track details (request()).
    3. The device sends the newer entries in SDU UPDATE packets of up to 4096 bytes, one at a time. The server
       ACKs or NACKs each one. A NACK, or no reply within SDU_ACK_TIMEOUT, sends the packet once more; a second
       failure ends the session.

    on_finished is called with True when a session has sent everything, or there was nothing to send, and False
    when it fails: no SDU REQUEST within SDU_REQUEST_TIMEOUT of the timestamp request, a request that can't be
    understood, or a packet that fails twice. A device that only connects now and then can disconnect then.

    Everything runs on the device's thread: poll() checks the timeouts.
    """

    IDLE = 0
    WAITING_ACK = 1
    WAITING_ACK_RETRY = 2
    WAITING_REQUEST = 3

    def __init__(self, device_id: str, store: DashStore, get_registry: Callable[[], list[dict]], send: Callable[[str], None]):
        """SDU session.

        Parameters
        ----------
        device_id : str
            The device ID.
        store : DashStore
            The store to send entries from.
        get_registry : Callable[[], list[dict]]
            Returns the device's stored lines, tracks and logs, in controlInfo order. Each is a dict with "type"
            ("TGRPH", "MAP" or "LOG"), "id" and "sub" (line or track ID, "" for a log), and for TGRPH "name",
            "lineType", "color" and "axis", for MAP "name" and "color".
        send : Callable[[str], None]
            Sends a message to the Dash server.
        """
        self.device_id = device_id
        self.store = store
        self._get_registry = get_registry
        self._send = send
        self.state = self.IDLE
        self._registry = []
        self._thresholds = {}  # (type, control ID, sub ID) -> newest timestamp the server holds.
        self._send_info = set()
        self._scan_id = 0
        self._packet = ""
        self._packet_end_id = 0
        self._deadline = 0.0
        self.on_finished: Callable[[bool], None] | None = None

    def start(self) -> str:
        """Start a sync: return the timestamp request to send, and wait for the Dash server's SDU REQUEST.

        A session left over from an earlier connection is abandoned. If there's nothing stored to ask about,
        returns "" and the sync has finished.
        """
        self.state = self.IDLE
        message = self.timestamp_request()
        if not message:
            self._finish(True)
            return ""
        self.state = self.WAITING_REQUEST
        self._deadline = time.monotonic() + SDU_REQUEST_TIMEOUT
        return message

    def timestamp_request(self) -> str:
        """The timestamp request the device sends to the Dash server's announce topic when it connects.

        Returns "" if there's nothing stored to ask about.
        """
        request = {}
        tgrph_list = []
        map_list = []
        log_list = []
        for item in self._get_registry():
            if item["type"] == "TGRPH":
                if not tgrph_list or tgrph_list[-1]["controlID"] != item["id"]:
                    tgrph_list.append({"controlID": item["id"], "lineList": []})
                tgrph_list[-1]["lineList"].append(item["sub"])
            elif item["type"] == "MAP":
                if not map_list or map_list[-1]["controlID"] != item["id"]:
                    map_list.append({"controlID": item["id"], "trackList": []})
                map_list[-1]["trackList"].append(item["sub"])
            elif item["type"] == "LOG":
                log_list.append(item["id"])
        if tgrph_list:
            request["tgrphList"] = tgrph_list
        if map_list:
            request["mapList"] = map_list
        if log_list:
            request["logList"] = log_list
        if not request:
            return ""
        return f"\t{self.device_id}\tDATA\tSDU\tREQUEST\t{_json(request)}\n"

    def request(self, json_str: str) -> None:
        """Start a session for an SDU REQUEST from the Dash server."""
        if self.state not in (self.IDLE, self.WAITING_REQUEST):
            logger.debug("SDU REQUEST ignored, a session is already running")
            return
        try:
            thresholds, send_info = self._parse_request(json_str)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            logger.warning("SDU REQUEST not understood: %s", error)
            self._finish(False)
            return
        if not thresholds:
            logger.debug("SDU REQUEST has no timestamps, nothing to send")
            self._finish(True)
            return
        self._registry = self._get_registry()
        self._thresholds = thresholds
        self._send_info = send_info
        self._scan_id = 0
        self.state = self.WAITING_ACK
        self._send_next_packet()

    def ack(self) -> None:
        """The Dash server received the last packet: send the next one."""
        if self.state not in (self.WAITING_ACK, self.WAITING_ACK_RETRY):
            logger.debug("SDU ACK received without a session")
            return
        self._scan_id = self._packet_end_id
        # The server has the line and track details after the first packet.
        self._send_info = set()
        self.state = self.WAITING_ACK
        self._send_next_packet()

    def nack(self) -> None:
        """The Dash server didn't accept the last packet: send it again, or end the session after a retry."""
        if self.state not in (self.WAITING_ACK, self.WAITING_ACK_RETRY):
            logger.debug("SDU NACK received without a session")
            return
        self._retry("NACK")

    def poll(self) -> None:
        """Send the last packet again, or end the session, if the Dash server hasn't replied in time."""
        if self.state == self.IDLE or time.monotonic() < self._deadline:
            return
        if self.state == self.WAITING_REQUEST:
            logger.warning("No SDU REQUEST from the Dash server")
            self._finish(False)
        else:
            self._retry("ACK timeout")

    def _retry(self, reason: str) -> None:
        if self.state == self.WAITING_ACK_RETRY:
            logger.warning("SDU %s after a retry, ending the session", reason)
            self._finish(False)
            return
        logger.debug("SDU %s, sending the packet again", reason)
        self.state = self.WAITING_ACK_RETRY
        self._send_packet(self._packet)

    @staticmethod
    def _parse_request(json_str: str) -> tuple[dict, set]:
        request = json.loads(json_str)
        thresholds = {}
        send_info = set()

        def add(key, element):
            if element.get("sendInfo", False):
                send_info.add(key)
            elif not element.get("ts"):
                logger.debug("SDU REQUEST: %s has neither ts nor sendInfo, ignored", key)
                return
            thresholds[key] = int(element.get("ts", 0))

        for control in request.get("tgrphList", []):
            control_id = control["controlID"]
            for line in control.get("lineList", []):
                add(("TGRPH", control_id, line["id"]), line)
        for control in request.get("mapList", []):
            control_id = control["controlID"]
            for track in control.get("trackList", []):
                add(("MAP", control_id, track["id"]), track)
        for log in request.get("logList", []):
            add(("LOG", log["controlID"], ""), log)
        return thresholds, send_info

    def _control_info(self) -> str:
        items = []
        for item in self._registry:
            key = (item["type"], item["id"], item["sub"])
            if item["type"] == "TGRPH":
                info = {"type": "TGRPH", "id": item["id"], "lineID": item["sub"]}
                if key in self._send_info:
                    info.update(name=item["name"], lineType=item["lineType"], color=item["color"], axis=item["axis"])
            elif item["type"] == "MAP":
                info = {"type": "MAP", "id": item["id"], "trackID": item["sub"]}
                if key in self._send_info:
                    info.update(name=item["name"], color=item["color"])
            else:
                info = {"type": "LOG", "id": item["id"]}
            items.append(_json(info))
        return "[" + ",".join(items) + "]"

    def _send_next_packet(self) -> None:
        header = f"\t{self.device_id}\tDATA\tSDU\tUPDATE\t"
        start = '{"controlInfo":' + self._control_info() + ',"data":['
        # Room for the entries, keeping space for the closing "]}", the hash and the newline.
        remaining = SDU_MAX_PACKET_LENGTH - len(header.encode()) - len(start.encode()) - len("]}\t") - 16 - 1
        indexes = {(item["type"], item["id"], item["sub"]): index for index, item in enumerate(self._registry)}
        items = []
        scan_id = self._scan_id
        full = False
        while not full:
            entries = self.store.entries_after_id(scan_id)
            if not entries:
                break
            for entry in entries:
                key = (entry.control_type, entry.control_id, entry.sub_id)
                index = indexes.get(key)
                if index is None or key not in self._thresholds or entry.timestamp <= self._thresholds[key]:
                    scan_id = entry.entry_id
                    continue
                data = format_sdu_data(entry)
                if data is None:
                    scan_id = entry.entry_id
                    continue
                item = ("," if items else "") + f'{{"idx":{index},"ts":{entry.timestamp},"data":{data}}}'
                if len(item.encode()) > remaining:
                    if not items:
                        logger.warning("SDU entry %s is too big for a packet, skipped", entry.entry_id)
                        scan_id = entry.entry_id
                        continue
                    full = True
                    break
                items.append(item)
                remaining -= len(item.encode())
                scan_id = entry.entry_id
        if not items:
            logger.debug("SDU session finished, nothing more to send")
            self._finish(True)
            return
        body = start + "".join(items) + "]}"
        self._packet_end_id = scan_id
        self._send_packet(f"{header}{body}\t{fnv1a_64(body.encode()):016x}\n")

    def _finish(self, completed: bool) -> None:
        self.state = self.IDLE
        if self.on_finished is not None:
            try:
                self.on_finished(completed)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Store sync callback failed")

    def _send_packet(self, packet: str) -> None:
        self._packet = packet
        self._deadline = time.monotonic() + SDU_ACK_TIMEOUT
        self._send(packet)
