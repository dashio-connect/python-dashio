from .enums import Colour
from .control import Control

import datetime
import dateutil.parser


class EventData:
    def __init__(self, header, body, colour=Colour.BLACK):
        self.colour = colour
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.header = header
        self.body = body

    def to_string(self):
        data_str = "{ts}\t{colour}\t{header}\t{body}\n".format(
            ts=self.timestamp.isoformat(), colour=self.colour, header=self.header, body=self.body
        )
        return data_str


class EventLog(Control):
    def get_state(self):
        state_str = ""
        return state_str

    def __init__(self, control_id, title="An Event Log", control_position=None):
        super().__init__("LOG", control_id, control_position=control_position)

        self.message_rx_event += self.__get_log_from_timestamp

        self.log_list = []
        self.get_state_str = "\t{}\t{}\t".format(self.msg_type, self.control_id)

    def __get_log_from_timestamp(self, msg):

        dt = dateutil.parser.isoparse(msg[1])
        print(msg[1])
        data_str = ""
        for log in self.log_list:
            if log.timestamp > dt:
                data_str += self.get_state_str + log.to_string()
        self.state_str = data_str

    def add_event_data(self, data: EventData):
        if isinstance(data, EventData):
            self.log_list.append(data)
            self.state_str = self.get_state_str + data.to_string()

    def add_event_data(self, header, body, colour=Colour.BLACK):
        nl = EventData(header, body, colour=colour)
        self.log_list.append(nl)
        self.state_str = self.get_state_str + nl.to_string()

    def send_data(self):
        if self.log_list:
            self.state_str = self.get_state_str + self.log_list[-1].to_string()
