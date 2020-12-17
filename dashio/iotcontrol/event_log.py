from .enums import Color
from .control import Control

import datetime
import dateutil.parser


class EventData:
    def __init__(self, header, body, color=Color.BLACK):
        self.color = color
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.header = header
        self.body = body

    def to_string(self):
        data_str = "{ts}\t{Color}\t{header}\t{body}\n".format(
            ts=self.timestamp.isoformat(), color=self.color, header=self.header, body=self.body
        )
        return data_str

# TODO: Finish the Event log
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

        dt = dateutil.parser.isoparse(msg[0])
        data_str = ""
        for log in self.log_list:
            if log.timestamp > dt:
                data_str += self.get_state_str + log.to_string()
        self.state_str = data_str

    def add_event_data(self, data: EventData):
        if isinstance(data, EventData):
            self.log_list.append(data)
            self.state_str = self.get_state_str + data.to_string()

    def add_event_data(self, header, body, color=Color.BLACK):
        nl = EventData(header, body, color=color)
        self.log_list.append(nl)
        self.state_str = self.get_state_str + nl.to_string()

    def send_data(self):
        if self.log_list:
            self.state_str = self.get_state_str + self.log_list[-1].to_string()
