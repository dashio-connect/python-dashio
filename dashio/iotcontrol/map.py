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
        data_str = "{lat}\t{long}\t{tag}\n".format(
            lat=self.latitude, long=self.longitude, tag=self.tag
        )
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
            state_str += self.get_state_str + locs.get_location_data()
        return state_str

    def __init__(self,
                 control_id,
                 title="A Map",
                 title_position=TitlePosition.BOTTOM,
                 control_position=None):
        super().__init__("MAP", control_id, control_position=control_position, title_position=title_position)
        self.title = title
        self.location_list = []
        self.get_state_str = "\t{}\t{}\t".format(self.msg_type, self.control_id)

    def add_location(self, location):
        self.location_list.append(location)

    def send_locations(self):
        state_str = ""
        for locs in self.location_list:
            state_str += self.get_state_str + locs.get_location_data()
        self.state_str = state_str
