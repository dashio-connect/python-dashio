from .enums import TitlePosition
from .control import Control
import datetime
import json

class SimpleMapLocation:
    def __init__(self, tag, latitude, longitude):
        """A map location used by a map_control

        Arguments:
            latitude {str} -- Latitude
            longitude {str} -- Longitude
            tag {str} -- A tag to display on the map.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.tag = tag

    def get_location_data(self):
        data_str = f"{self.latitude}\t{self.longitude}\t{self.tag}\n"
        return data_str

class MapLocation:
    def __init__(self, tag, latitude, longitude, average_speed=None, peak_speed=None, course=None, altitude=None, distance=None):
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

    def get_location_data(self):
        data_str = json.dumps(self._map_loc) + "\n"
        return data_str
    

class Map(Control):
    def get_state(self):
        state_str = ""
        for locs in self.location_list:
            state_str += self._state_str + locs.get_location_data()
        return state_str

    def __init__(self,
                 control_id,
                 title="A Map",
                 title_position=TitlePosition.BOTTOM,
                 control_position=None):
        super().__init__("MAP", control_id, title=title, control_position=control_position, title_position=title_position)
        self.location_list = []

    def add_location(self, location):
        self.location_list.append(location)

    def send_locations(self):
        state_str = ""
        for locs in self.location_list:
            state_str += self._state_str + locs.get_location_data()
        self.state_str = state_str
