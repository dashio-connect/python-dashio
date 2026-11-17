"""
MIT License

Copyright (c) 2026 DashIO-Connect

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

Installations: a device on certificates fills a role in a business's installation, an account of its own on the Dash
server (inst- and 12 hex digits), whose name is the device's topic prefix. The spec is dash_docs
Installations/DashIO_Installations.md.

An UPDATE from the app is checked like a move (the device goes back if the new prefix is refused), and a move made
while another is being checked keeps the last confirmed prefix.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .device_certificates import DeviceCertificates

logger = logging.getLogger(__name__)

INS_NO_CERT = 420  # The device isn't in the certificate state CERT.
INS_BAD_VALUE = 421  # A prefix, role, coordinate or metadata value isn't valid.
INS_STORE_FAILED = 422  # The device couldn't store the values.
INS_MOVE_FAILED = 423  # The broker refused the new prefix's control topic: back under the previous prefix.

ASSIGNED = "ASSIGNED"
TAKEN = "TAKEN"
NO_ROLE = "NO_ROLE"
NOT_INSTALLATION = "NOT_INSTALLATION"
MOVE_FAILED = "MOVE_FAILED"
SERVER_STATUSES = (ASSIGNED, TAKEN, NO_ROLE, NOT_INSTALLATION)

# The changes passed to the installation callback.
SET_BY_APP = "SET_BY_APP"  # The Dash app put the device in an installation, on site.
SET_BY_MOVE = "SET_BY_MOVE"  # The Dash server moved the device, or sent it home.
WENT_BACK = "WENT_BACK"  # The new prefix was refused: back to the previous one.
LEFT = "LEFT"  # Out of its installation: home, or a new Dash login.
STATUS = "STATUS"  # The server answered the role report.

ROLE_RETRY_MIN = 60.0  # Seconds to wait for the answer to SVR_ROLE before reporting again.
ROLE_RETRY_MAX = 3600.0  # The wait doubles after each unanswered report, up to this.
MOVE_SILENCE = 60.0  # During a move, nothing from the server for this long after connecting counts as refused.
MAX_METADATA_LENGTH = 512

INSTALLATION_FILE = "installation.json"

PREFIX_PATTERN = re.compile(r"inst-[0-9a-f]{12}")
ROLE_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,32}")


class InstallationError(Exception):
    """An INS error, with its code."""

    def __init__(self, code: int, message: str = ""):
        super().__init__(message or str(code))
        self.code = code


def _place(prefix: str = "", role: str = "", lat: float | None = None, lon: float | None = None, metadata: dict | None = None) -> dict:
    return {"prefix": prefix, "role": role, "lat": lat, "lon": lon, "metadata": metadata}


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_values(values: dict, by_move: bool) -> dict:
    """The prefix, role, coordinates and metadata of an UPDATE or SVR_MOVE, checked. Raises InstallationError."""
    if not isinstance(values, dict):
        raise InstallationError(INS_BAD_VALUE, "Not a JSON object")
    prefix, role = values.get("prefix", ""), values.get("role", "")
    if not isinstance(prefix, str) or not isinstance(role, str):
        raise InstallationError(INS_BAD_VALUE, "The prefix and role are strings")
    if by_move and prefix == "":
        # Home to the owner's account: no role.
        if role:
            raise InstallationError(INS_BAD_VALUE, "A move home has no role")
        return _place()
    if not PREFIX_PATTERN.fullmatch(prefix):
        raise InstallationError(INS_BAD_VALUE, f"Prefix {prefix!r}")
    if not ROLE_PATTERN.fullmatch(role):
        raise InstallationError(INS_BAD_VALUE, f"Role {role!r}")
    lat, lon = values.get("lat"), values.get("lon")
    if (lat is None) != (lon is None):
        raise InstallationError(INS_BAD_VALUE, "lat and lon go together")
    if lat is not None and not (_is_number(lat) and _is_number(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
        raise InstallationError(INS_BAD_VALUE, "Coordinates")
    metadata = values.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict) or len(json.dumps(metadata, separators=(",", ":"))) > MAX_METADATA_LENGTH:
            raise InstallationError(INS_BAD_VALUE, f"Metadata is a JSON object of at most {MAX_METADATA_LENGTH} characters")
    return _place(prefix, role, lat, lon, metadata)


class Installation:
    """The device's installation: its topic prefix, role, coordinates and metadata, kept with its certificate.

    Made by DeviceCertificates, as device.installation. Set by the Dash app (INS UPDATE) and the Dash server
    (SVR_MOVE); the DashConnection uses the prefix for its topics when it logs in with the certificate.

    Used by the device's and the connection's threads.
    """

    def __init__(self, certificates: DeviceCertificates):
        self._certificates = certificates
        self._lock = threading.RLock()
        self._changed = False  # The prefix changed, so the connection logs in again.
        self.callback: Callable[[str, Installation], None] | None = None
        self.owner = ""  # The owner's username, from the DashConnection, for REQUEST INFO.
        state = {}
        try:
            state = json.loads(certificates.read_file(INSTALLATION_FILE))
        except (OSError, ValueError):
            pass
        self._current = self._load_place(state.get("current"))
        self._previous = self._load_place(state.get("previous"))
        self._moving = bool(state.get("moving", False))  # previous is where it goes back to, until confirmed.
        self._status = state.get("status", "") if state.get("status") in SERVER_STATUSES + (MOVE_FAILED,) else ""
        self._report_failed = bool(state.get("reportFailed", False))  # ERR 423 to send on the next connection.
        if self._current["prefix"]:
            logger.info("Installation %s, role %s%s", self._current["prefix"], self._current["role"], ", moving" if self._moving else "")

    @staticmethod
    def _load_place(place) -> dict:
        if not isinstance(place, dict):
            return _place()
        try:
            return check_values(place, by_move=True)
        except InstallationError:
            return _place()

    def _save(self):
        state = {
            "current": self._current, "previous": self._previous, "moving": self._moving,
            "status": self._status, "reportFailed": self._report_failed
        }
        self._certificates.write_file(INSTALLATION_FILE, json.dumps(state).encode())

    def _notify(self, change: str):
        if self.callback is not None:
            try:
                self.callback(change, self)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Installation callback")

    # Read by the program

    @property
    def prefix(self) -> str:
        """The installation account, e.g. inst-3f9a01c2b7de, or "" on the owner's account."""
        with self._lock:
            return self._current["prefix"]

    @property
    def role(self) -> str:
        """The role the device fills, or ""."""
        with self._lock:
            return self._current["role"]

    @property
    def location(self) -> tuple[float, float] | None:
        """The installed coordinates (lat, lon) the Dash app gave, or None."""
        with self._lock:
            if self._current["lat"] is None:
                return None
            return (self._current["lat"], self._current["lon"])

    @property
    def metadata(self) -> dict | None:
        """The metadata the Dash app gave, for the program's own use, or None."""
        with self._lock:
            metadata = self._current["metadata"]
            return dict(metadata) if metadata is not None else None

    @property
    def status(self) -> str:
        """The server's last answer to the role report, MOVE_FAILED, or "" before the first."""
        with self._lock:
            return self._status

    @property
    def moving_from(self) -> str | None:
        """While a move is being confirmed, the prefix the device goes back to if it's refused ("" for the owner's
        account), otherwise None."""
        with self._lock:
            return self._previous["prefix"] if self._moving else None

    def in_installation(self) -> bool:
        """In an installation, or moving out of one: the device never logs in with its owner's password."""
        with self._lock:
            return bool(self._current["prefix"] or (self._moving and self._previous["prefix"]))

    def info(self) -> dict:
        """REQUEST INFO's reply."""
        with self._lock:
            info = {"action": "INFO", "prefix": self._current["prefix"] or self.owner, "role": self._current["role"]}
            if self._current["lat"] is not None:
                info["lat"], info["lon"] = self._current["lat"], self._current["lon"]
            info["status"] = self._status
            if self._moving:
                info["movingFrom"] = self._previous["prefix"] or self.owner
            return info

    # Used by the connection

    def topic_prefix(self, owner: str) -> str:
        """The topic prefix for a login with the certificate: the installation account, or the owner's username."""
        with self._lock:
            return self._current["prefix"] or owner

    def take_changed(self) -> bool:
        """Whether the prefix changed since the last call, so the connection logs in again."""
        with self._lock:
            changed, self._changed = self._changed, False
            return changed

    def topic_refused(self) -> bool:
        """The broker refused the control topic. During a move, go back to the previous prefix and return True.
        Otherwise stay: the broker also refuses when its database can't be read, and a whole fleet mustn't leave
        their installations at once."""
        with self._lock:
            if not self._moving:
                logger.error("The broker refused %s's control topic, with no move to go back from", self._current["prefix"] or "the owner's account")
                if self._status != MOVE_FAILED:
                    self._status = MOVE_FAILED
                    self._save_quietly()
                return False
            self._go_back()
        self._notify(WENT_BACK)
        return True

    def _go_back(self):
        logger.warning("The broker refused %s: back to %s", self._current["prefix"] or "the owner's account", self._previous["prefix"] or "the owner's account")
        self._current, self._previous = self._previous, _place()
        self._moving = False
        self._status = MOVE_FAILED
        self._report_failed = True
        self._changed = True
        self._save_quietly()

    def _save_quietly(self):
        try:
            self._save()
        except OSError as error:
            logger.error("The installation wasn't saved: %s", error)

    # Used by the device

    def set(self, values: dict, by_move: bool):
        """Put the device in an installation: UPDATE from the app (by_move False), or SVR_MOVE from the server.
        Raises InstallationError. Returns False for a move it's already making."""
        place = check_values(values, by_move)
        if self._certificates.state != "CERT":
            raise InstallationError(INS_NO_CERT, "Not on certificates")  # An installation account has no password.
        with self._lock:
            if by_move and self._current["prefix"] == place["prefix"] and (self._moving or not place["prefix"]):
                return False  # The server sends it again after each WHO while the move is pending.
            old = (self._current, self._previous, self._moving, self._status, self._report_failed)
            if not self._moving:
                # Where it goes back to is the last prefix the server confirmed, kept through a second move.
                self._previous = self._current
            self._current = place
            self._moving = self._previous["prefix"] != place["prefix"]
            if not self._moving:
                self._previous = _place()  # A new role or coordinates in the same installation.
            self._status = ""
            self._report_failed = False
            try:
                self._save()
            except OSError as error:
                self._current, self._previous, self._moving, self._status, self._report_failed = old
                raise InstallationError(INS_STORE_FAILED, str(error)) from error
            self._changed = True
            if place["prefix"]:
                logger.info("%s installation %s, role %s", "Moved to" if by_move else "Joined", place["prefix"], place["role"])
            else:
                logger.info("Moving home to the owner's account")
        self._notify(SET_BY_MOVE if by_move else SET_BY_APP)
        return True

    def connected(self) -> tuple[bool, bool, bool]:
        """Logged in with the certificate and WHO sent. Returns whether the device has a role to report, whether to
        send ERR 423, and whether a move is being checked."""
        with self._lock:
            report_failed, self._report_failed = self._report_failed, False
            if report_failed:
                self._save_quietly()
            return bool(self._current["role"]), report_failed, self._moving

    def server_heard(self):
        """The server was heard under the current prefix during a move, so the prefix works. A move home is
        confirmed by it: the device leaves its installation. A move into one is confirmed by the role answer."""
        with self._lock:
            going_home = self._moving and not self._current["prefix"]
        if going_home and self.leave():
            logger.info("Moved home: left the installation")

    def role_answer(self, status: str, role: str) -> bool:
        """The server's answer to SVR_ROLE. Returns whether it answers the device's current role."""
        if status not in SERVER_STATUSES:
            logger.warning("Role report answer %s unknown", status)
            return False
        with self._lock:
            if role != self._current["role"]:
                logger.warning("Role report answer for %s, not %s", role, self._current["role"])
                return False
            if self._moving and status == NOT_INSTALLATION:
                # The installation was retired during the move: as a refused one.
                self._go_back()
                change = WENT_BACK
            else:
                # The move is done once the server has heard from the device under the new prefix, even if the
                # role turned out to be taken. The device never drops its role because of the answer.
                confirmed = self._moving
                self._moving = False
                self._previous = _place()
                self._status = status
                self._save_quietly()
                change = STATUS
                logger.info("Role %s: %s%s", role, status, ", move confirmed" if confirmed else "")
                if status != ASSIGNED:
                    logger.warning("Unassigned: an administrator settles it on the Dash server, or on site")
        self._notify(change)
        return True

    def leave(self) -> bool:
        """Out of any installation, e.g. on a new Dash login from the app. Returns whether it was in one."""
        with self._lock:
            if not (self._current["prefix"] or self._moving or self._status):
                return False
            was_in = bool(self._current["prefix"] or self._moving)
            self._current, self._previous = _place(), _place()
            self._moving = False
            self._status = ""
            self._report_failed = False
            self._changed = True
            try:
                self._certificates.remove_file(INSTALLATION_FILE)
            except OSError as error:
                logger.error("The installation wasn't removed: %s", error)
        if was_in:
            self._notify(LEFT)
        return was_in


class InstallationSession:
    """The device's role report to the Dash server (SVR_ROLE), ERR 423 after going back, and the check that the
    server is heard under a new prefix during a move.

    The check is for connections that can't report a refused subscription, such as the SIM7672 modem's, and for a
    move home, which has no role to report. The device asks the server for the time (CLK), which the server answers
    at once; nothing from the server within MOVE_SILENCE seconds counts as the prefix being refused.

    It runs on the device's thread: poll() is called from Device.run().
    """

    def __init__(self, installation: Installation, certificates: DeviceCertificates, device_id: str, send: Callable[[str], None]):
        self.installation = installation
        self.certificates = certificates
        self.device_id = device_id
        self._send = send
        self._connection = certificates.connection()
        self._deadline: float | None = None
        self._wait = ROLE_RETRY_MIN
        self._silence_deadline: float | None = None  # During a move: when to give up hearing from the server.

    def _message(self, *fields: str) -> str:
        return f"\t{self.device_id}\tDATA\tINS\t" + "\t".join(fields) + "\n"

    def connected(self):
        """Logged in with the certificate, and WHO sent."""
        self._deadline = None
        has_role, report_failed, moving = self.installation.connected()
        self._silence_deadline = None
        if moving:
            self._silence_deadline = time.monotonic() + MOVE_SILENCE
            self._send(f"\t{self.device_id}\tCLK\n")  # The server answers at once.
        if report_failed:
            self._send(self._message("ERR", str(INS_MOVE_FAILED)))
        if has_role:
            self._wait = ROLE_RETRY_MIN
            self._report()

    def _report(self):
        role = self.installation.role
        if not role:
            self._deadline = None
            return
        self._send(self._message("SVR_ROLE", json.dumps({"role": role}, separators=(",", ":"))))
        self._deadline = time.monotonic() + self._wait
        self._wait = min(self._wait * 2, ROLE_RETRY_MAX)

    def poll(self):
        connection = self.certificates.connection()
        if connection != self._connection:
            self._connection = connection
            if connection[1] is None:
                # The connection dropped: report again, and check the prefix again, on the next.
                self._deadline = None
                self._silence_deadline = None
        if self._silence_deadline is not None and time.monotonic() >= self._silence_deadline:
            self._silence_deadline = None
            if self.installation.moving_from is not None:
                logger.warning("Nothing from the Dash server for %d s under the new prefix: taken as refused", MOVE_SILENCE)
                self.installation.topic_refused()
                self._deadline = None
        if self._deadline is not None and time.monotonic() >= self._deadline:
            self._report()

    def server_heard(self):
        """A message from the Dash server for the device."""
        if self._silence_deadline is None:
            return  # Not checking a move.
        self._silence_deadline = None
        self.installation.server_heard()

    def answer(self, status: str, role: str):
        """SVR_ROLE from the server."""
        if self.installation.role_answer(status, role):
            self._deadline = None
