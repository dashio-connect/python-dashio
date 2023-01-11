import json
import unittest


def _get_cfg_dict(cfg_list: list):
    json_str = cfg_list[0].rpartition('\t')[2]
    return json.loads(json_str)


"""
class TestMapLocation(unittest.TestCase):

    def test_map_location_timestamp(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748)
        test_loc = json.loads(str(test_location))
        self.assertIsInstance(dateutil.parser.isoparse(test_loc['time']), datetime, "Should be datetime")

    def test_map_location_message(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['message'], 'TAG', "message should be TAG")

    def test_map_location_latitude(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['latitude'], -45.237101516008835, "latitude should be -45.237101516008835")

    def test_map_location_longitude(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['longitude'], 168.84818243505748, "latitude should be 168.84818243505748")

    def test_map_location_avg_speed(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748, average_speed=10)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['avgeSpeed'], 10, "avgeSpeed should be 10")

    def test_map_location_peak_speed(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748, peak_speed=10)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['peakSpeed'], 10, "peakSpeed should be 10")

    def test_map_location_course(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748, course=10)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['course'], 10, "course should be 10")

    def test_map_location_altitude(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748, altitude=10)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['altitude'], 10, "altitude should be 10")

    def test_map_location_distance(self):
        test_location = MapLocation("TAG", -45.237101516008835, 168.84818243505748, distance=10)
        test_loc = json.loads(str(test_location))
        self.assertEqual(test_loc['distance'], 10, "distance should be 10")


class TestMap(unittest.TestCase):

    def test_knob_control_type(self):
        test_control = Map("MAPID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[2], 'MAP', "control type should be MAP")

    def test_knob_control_id(self):
        test_control = Map("MAPID")
        test_str_list = test_control._control_hdr_str.split('\t')
        self.assertEqual(test_str_list[3], 'MAPID', "control type should be MAPID")

"""


if __name__ == '__main__':
    unittest.main()
