from .enums import Colour
from .control import Control

import datetime
import dateutil.parser


class log_event():
    def __init__(self, data):
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.data_point = data

    def to_string(self):
        data_str = "{ts},{data}".format(ts=self.timestamp.isoformat(), data=self.data_point)
        return data_str


class EventData():
    def __init__(self,
                 name='',
                 line_type=TimeGraphLineType.LINE,
                 colour=Colour.BLACK,
                 transparency=1.0,
                 max_data_points=60):
        self.max_data_points = max_data_points
        self.name = name
        self.line_type = line_type
        self.colour = colour
        self.transparency = transparency
        self.data = []

    def get_line_data(self):
        if not self.data:
            return ''
        data_str = '\t{l_name}\t{l_type}\t{l_colour}\t{l_transparency}'.format(l_name=self.name,
                                                                               l_type=self.line_type.value,
                                                                               l_colour=self.colour.value,
                                                                               l_transparency=self.transparency)
        for d in self.data:
            data_str += '\t' + d.to_string()
        data_str += '\n'
        return data_str

    def get_line_from_timestamp(self, timestamp):
        if not self.data:
            return ''
        data_str = '\t{l_name}\t{l_type}\t{l_colour}\t{l_transparency}'.format(l_name=self.name,
                                                                               l_type=self.line_type.value,
                                                                               l_colour=self.colour.value,
                                                                               l_transparency=self.transparency)

        dt = dateutil.parser.isoparse(timestamp)

        for d in self.data:
            if d.timestamp > dt:
                data_str += '\t' + d.to_string()
        data_str += '\n'
        return data_str

    def add_data_point(self, data_point):
        """Add and sends a single datapoint to the line. It automatically timestamps to the current time.

        Arguments:
            data_point {str} -- A single data point
        """
        dp = DataPoint(data_point)
        # now = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat()
        # data_str = "{ts},{data}".format(ts=now, data=data_point)
        if len(self.data) < self.max_data_points:
            self.data.append(dp)
            return
        for i in range(len(self.data) - 1):
            self.data[i] = self.data[i + 1]
        self.data[-1] = dp

    def get_latest_data(self):
        if not self.data:
            return ''
        data_str = '\t{l_name}\t{l_type}\t{l_colour}\t{l_transparency}'.format(l_name=self.name,
                                                                               l_type=self.line_type.value,
                                                                               l_colour=self.colour.value,
                                                                               l_transparency=self.transparency)
        data_str += '\t' + self.data[-1].to_string()
        data_str += '\n'
        return data_str


class EventLog(Control):

    def get_state(self):
        state_str = ''
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                state_str += self.get_state_str + key + self.line_dict[key].get_latest_data()
        return state_str

    def __init__(self,
                 control_id,
                 title='An Event Log',):
        super().__init__('LOG', control_id, control_position=control_position)

        self.message_rx_event += self.__get_lines_from_timestamp

        self.line_dict = {}
        self.get_state_str = '\t{}\t{}\t'.format(self.msg_type, self.control_id)

    def __get_lines_from_timestamp(self, msg):
        state_str = ''
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                state_str += self.get_state_str + key + self.line_dict[key].get_line_from_timestamp(msg[1])
        self.state_str = state_str

    def send_data(self):
        state_str = ''
        for key in self.line_dict.keys():
            if self.line_dict[key].data:
                state_str += self.get_state_str + key + self.line_dict[key].get_latest_data()
        self.state_str = state_str
