"""map.py

Class
-----
SimpleMapLocation
    A simple location
MapLocation
    Map location
Map
    A Map control
"""
import datetime
import json

from .control import Control
from .enums import TitlePosition


class SimpleMapLocation:
    """
    A non json map location.
    """
    def __init__(self, tag: str, latitude: str, longitude: str):
        """A map location used by a map_control

        Parameters
            latitude : str
                Latitude
            longitude : str
                Longitude
            tag : str
                A tag to display on the map.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.tag = tag

    def __str__(self):
        return f"{self.latitude}\t{self.longitude}\t{self.tag}\n"

class MapLocation:
    """
    A json version of a map location.
    """
    def __init__(self, tag: str, latitude: str, longitude: str, average_speed=None, peak_speed=None, course=None, altitude=None, distance=None):
        """MapLocation

        Parameters
        ----------
        tag : str
            Location tag
        latitude : str
            The latitude
        longitude : str
            The longitude
        average_speed : str, optional
            Average speed, by default None
        peak_speed : str, optional
            Peak speed, by default None
        course : str, optional
            couse, by default None
        altitude : str, optional
            altitude, by default None
        distance : str, optional
            distance, by default None
        """
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self._map_loc = {}
        self._map_loc["time"] = self.timestamp.isoformat()
        self._map_loc["message"] = tag
        self._map_loc["latitude"] = latitude
        self._map_loc["longitude"] = longitude
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

    def __str__(self):
        return json.dumps(self._map_loc) + "\n"


class Map(Control):
    """A Map control
    """
    def get_state(self):
        state_str = ""
        for locs in self.location_list:
            state_str += self._control_hdr_str + str(locs)
        return state_str

    def __init__(self,
                 control_id,
                 title="A Map",
                 title_position=TitlePosition.BOTTOM,
                 control_position=None):
        """A Map control

        Parameters
        ----------
        control_id : str
            An unique control identity string. The control identity string must be a unique string for each control per device
        title : str, optional
            Title of the control, by default "A Map"
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        title_position : TitlePosition, optional
            Position of the title when displayed on the iotdashboard app, by default None
        """
        super().__init__("MAP", control_id, title=title, control_position=control_position, title_position=title_position)
        self.location_list = []

    def add_location(self, location):
        """Add Location to the map

        Parameters
        ----------
        location : MapLocation, SimpleMapLocation
            The location to add to the map
        """
        self.location_list.append(location)

    def send_locations(self):
        """Sends the locations to the map
        """
        state_str = ""
        for locs in self.location_list:
            state_str += self._control_hdr_str + str(locs)
        self.state_str = state_str
