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
import datetime
import json
from dateutil import parser

from ..constants import BAD_CHARS
from .control import Control, ControlPosition, ControlConfig, _get_title_position
from .enums import TitlePosition, Color
from .event import Event


class MapLocation:
    """
    A json version of a map location.
    """

    def __init__(self, latitude: str, longitude: str, average_speed=None, peak_speed=None, course=None, altitude=None, distance=None):
        """MapLocation

        Parameters
        ----------
        latitude : str
            The latitude
        longitude : str
            The longitude
        average_speed : str, optional
            Average speed, by default None
        peak_speed : str, optional
            Peak speed, by default None
        course : str, optional
            course, by default None
        altitude : str, optional
            altitude, by default None
        distance : str, optional
            distance, by default None
        """
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self._map_loc = {}
        self._map_loc["time"] = self.timestamp.isoformat()
        self._map_loc["latitude"] = latitude.translate(BAD_CHARS)
        self._map_loc["longitude"] = longitude.translate(BAD_CHARS)
        if average_speed:
            self._map_loc["avgeSpeed"] = average_speed
        if peak_speed:
            self._map_loc["peakSpeed"] = peak_speed
        if course:
            self._map_loc["course"] = course
        if altitude:
            self._map_loc["altitude"] = altitude
        if distance:
            self._map_loc["distance"] = distance

    def to_json(self):
        """Make a json representation of a map point.

        Returns
        -------
        str
        """
        return json.dumps(self._map_loc)

    def get_simple_format(self):
        """Returns the simple format of the MAP Location

        Returns
        -------
        _type_
            _description_
        """
        lat = self._map_loc["latitude"]
        long = self._map_loc["longitude"]
        return f"\t{lat},{long}\n"


class MapTrack:
    """A Map track
    """

    def __init__(self, track_id: str, text="", color=Color.RED) -> None:
        self.track_id = track_id.translate(BAD_CHARS)
        self.text = text.translate(BAD_CHARS)
        self.color = color
        self.track_start_time = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.locations = []

    def add_location(self, location: MapLocation) -> None:
        """Add a location to the Track

        Parameters
        ----------
        location : MapLocation
            The Map location to add to the track.
        """
        if isinstance(location, MapLocation):
            self.locations.append(location)

    def get_track(self) -> str:
        """Returns the track in DashIO long format

        Returns
        -------
        str
            track in DashIO long format
        """
        reply = f"\t{self.track_id}\t{self.text}\t{self.color.value}"
        for loc in self.locations:
            reply += f"\t{loc.to_json()}"
        return reply

    def get_last_location(self) -> str:
        """Returns the last track location in short format

        Returns
        -------
        str
            The last location in track in short format
        """
        reply = f"{self.track_id}" + self.locations[-1].get_simple_format()
        return reply


class Map(Control):
    """A Map control
    """

    def __init__(
        self,
        control_id,
        title="A Map",
        title_position=TitlePosition.BOTTOM,
        control_position=None,
    ):
        """A Map control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device.
        title : str, optional
            Title of the control, by default "A Map"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the **Dash** app, by default None
        """
        super().__init__("MAP", control_id)
        self._configs.append(ControlConfig(control_id, title, control_position, title_position))
        self.tracks = {}
        self._store = None  # The device's DashStore, set when the Map is added to a Device with a store.

        self._message_rx_event = Event()
        self._message_rx_event += self._get_tracks_from_timestamp

    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instantiates Map from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from the IoTDashboard App

        Returns
        -------
        Map
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"]),
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def _get_tracks_from_timestamp(self, msg):
        reply = ""
        try:
            dashboard_id = msg[3]
            from_timestamp = parser.isoparse(msg[4])
        except (IndexError, ValueError):
            return ""
        if self._store is not None:
            # Every location after the requested time, including tracks stored before the program restarted.
            for track_id in self._store.sub_ids("MAP", self.control_id):
                entries = self._store.entries("MAP", self.control_id, track_id, from_timestamp)
                if not entries:
                    continue
                track = self.tracks.get(track_id) or MapTrack(track_id)
                reply += self._control_hdr_str + dashboard_id + f"\t{track.track_id}\t{track.text}\t{track.color.value}"
                for entry in entries:
                    reply += "\t" + json.dumps({"time": entry.time.isoformat(), **entry.data})
                reply += "\n"
            return reply
        if self.tracks:
            for value in self.tracks.values():
                if value.track_start_time > from_timestamp:
                    reply += self._control_hdr_str + dashboard_id + value.get_track() + "\n"
        return reply

    def add_location_to_track(self, location: MapLocation, track_id: str) -> None:
        """Add Location to the map

        Parameters
        ----------
        location : MapLocation.
            The location to add to the map
        track_id : Track ID for the location.
        """
        if track_id in self.tracks:
            self.tracks[track_id].add_location(location)
        else:
            self.tracks[track_id] = MapTrack(track_id)
            self.tracks[track_id].add_location(location)
        if self._store is not None:
            self._store.add("MAP", self.control_id, track_id, location.timestamp, {key: value for key, value in location._map_loc.items() if key != "time"})
        self.send_location(location, track_id)

    def send_location(self, location: MapLocation, track_id: str = ""):
        """Sends the locations to the map
        """
        state_str = ""
        state_str += self._control_hdr_str + track_id + location.get_simple_format()
        self.state_str = state_str
