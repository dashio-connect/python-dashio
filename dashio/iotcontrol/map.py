from .enums import MapType
from .control import Control


class MapLocation:
    def __init__(self, location_id, latitude, longitude, tag):
        """A map location used by a map_control

        Arguments:
            location_id {str} -- Location identifier.
            latitude {str} -- Latitude
            longitude {str} -- Longitude
            tag {str} -- A tag to display on the map.
        """
        self.location_id = location_id
        self.latitude = latitude
        self.longitude = longitude
        self.tag = tag

    def get_location_data(self):
        data_str = "{lat}\t{long}\t{tag}\n".format(
            loc_id=self.location_id, lat=self.latitude, long=self.longitude, tag=self.tag
        )
        return data_str


class Map(Control):
    def get_state(self):
        state_str = ""
        for key in self.location_dict.keys():
            state_str += self.get_state_str + self.location_dict[key].get_location_data()
        return state_str

    def __init__(self, control_id, map_type=MapType.STANDARD, control_position=None):
        super().__init__("MAP", control_id, control_position=control_position)
        self.location_dict = {}
        self.get_state_str = "\t{}\t{}\t".format(self.msg_type, self.control_id)
        self.map_type = map_type

    def add_location(self, location):
        self.location_dict[location.location_id] = location

    def send_locations(self):
        state_str = ""
        for key in self.location_dict.keys():
            state_str += self.get_state_str + self.location_dict[key].get_location_data()
        self.state_str = state_str

    @property
    def map_type(self) -> MapType:
        return self._map_type

    @map_type.setter
    def map_type(self, val: MapType):
        self._map_type = val
        self._cfg["mapType"] = val.value
