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

import dateutil.parser

from ..constants import BAD_CHARS
from .control import Control
from .enums import Color, TitlePosition
from .ring_buffer import RingBuffer


class EventData:
    """Event log data point
    """
    def __init__(self, header: str, body: str, color=Color.WHITE):
        """EventLog data point

        Parameters
        ----------

        header : str
            Header or title of the data
        body : str
            The event data
        color : Color, optional
            The color tto diplay this data point io iotdashboard app, by default Color.WHITE
        """
        self.color = color
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.header = header.translate(BAD_CHARS)
        self.body = body.translate(BAD_CHARS)

    def __str__(self):
        return "{ts}\t{color}\t{header}\t{body}\n".format(
            ts=self.timestamp.isoformat(), color=str(self.color.value), header=self.header, body=self.body
        )


class EventLog(Control):
    """EventLog control
    """

    def __init__(self,
                 control_id: str,
                 title="An Event Log",
                 title_position=TitlePosition.BOTTOM,
                 control_position=None,
                 max_log_entries=100):
        """An EventLog control

        Parameters
        ----------

        control_id : str
            A unique identifier for this control
        title : str, optional
            The title for this control will be displayed on the iotdashboard app, by default "An Event Log"
        title_position : TitlePosition, optional
            The position of the title, by default TitlePosition.BOTTOM
        control_position : ControlPosition, optional
            The position of the control on a DeviceView, by default None
        max_log_entries : int, optional
            The EventLog usues a ring buffer for data entries this dfines the number of
            entries before over wrting older entires, by default 100
        """
        super().__init__("LOG", control_id, title=title, control_position=control_position, title_position=title_position)
        self.message_rx_event = self._get_log_from_timestamp
        self.log = RingBuffer(max_log_entries)

    def _get_log_from_timestamp(self, msg):
        log_date = dateutil.parser.isoparse(msg[3])
        data_str = ""
        for log in self.log.get():
            if log.timestamp > log_date:
                data_str += self._control_hdr_str + str(log)
        self.state_str = data_str

    def add_event_data(self, data: EventData):
        """Add a data point to the log and send it to any connected iotdashboard app

        Parameters
        ----------
        data : EventData
            The data to add to the log
        """
        if isinstance(data, EventData):
            self.log.append(data)
            self.state_str = self._control_hdr_str + str(data)

    def send_data(self):
        """Send the latest log entry to any connected iotdashboard app.
        """
        if self.log:
            self.state_str = self._control_hdr_str + str(self.log.get_latest())
