from .enums import Color, TitlePosition
from .control import Control
from .ring_buffer import RingBuffer

import datetime
import dateutil.parser


class EventData:
    def __init__(self, header, body, color=Color.WHITE):
        self.color = color
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.header = header
        self.body = body

    def to_string(self):
        data_str = "{ts}\t{color}\t{header}\t{body}\n".format(
            ts=self.timestamp.isoformat(), color=str(self.color.value), header=self.header, body=self.body
        )
        return data_str


# TODO: Finish the Event log
class EventLog(Control):
    def get_state(self):
        return ""

    def __init__(self,
                 control_id,
                 title="An Event Log",
                 title_position=TitlePosition.BOTTOM,
                 control_position=None, max_log_entries=100):
        super().__init__("LOG", control_id, title=title, control_position=control_position, title_position=title_position)
        self.message_rx_event = self.__get_log_from_timestamp
        self.log = RingBuffer(max_log_entries)

    def __get_log_from_timestamp(self, msg):
        dt = dateutil.parser.isoparse(msg[3])
        data_str = ""
        for log in self.log.get():
            if log.timestamp > dt:
                data_str += self._state_str + log.to_string()
        self.state_str = data_str

    def add_event_data(self, data: EventData):
        if isinstance(data, EventData):
            self.log.append(data)
            self.state_str = self._state_str + data.to_string()

    def send_data(self):
        if self.log:
            self.state_str = self._state_str + self.log.get_latest().to_string()
