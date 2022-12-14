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
import json
import dateutil.parser
from ..constants import BAD_CHARS
from .control import Control, ControlPosition, ControlConfig, _get_title_position
from .enums import Color, TitlePosition
from .ring_buffer import RingBuffer

class EventData:
    """Event log data point
    """
    def __init__(self, lines: str, color=Color.WHITE):
        """EventLog data point

        Parameters
        ----------

        lines : str max 25 lines long. Each line is seperated by '\n'
        color : Color, optional
            The color to display this data point on the iotdashboard app, by default Color.WHITE
        """
        self.color = color
        self.timestamp = datetime.datetime.utcnow().replace(microsecond=0, tzinfo=datetime.timezone.utc)
        self.event_lines = []
        no_l = 0

        for s_line in lines.split("\n"):
            self.event_lines.append(s_line.translate(BAD_CHARS))
            no_l += 1
            if no_l > 25:
                break

    def to_json(self):
        """Convert to JSON

        Returns
        -------
        str
            json representation
        """
        event_dict = {
            'time': self.timestamp.isoformat(),
            'color': str(self.color.value),
            'lines': self.event_lines
        }
        return json.dumps(event_dict)

    def __str__(self):
        header = f"{self.timestamp.isoformat()}\t{str(self.color.value)}"
        for line in self.event_lines:
            header += f"\t{line}"
        header += "\n"
        return header



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
        super().__init__("LOG", control_id)
        self._cfg_columnar.append(ControlConfig(control_id, title, control_position, title_position))

        self.message_rx_event = self._get_log_from_timestamp
        self.log = RingBuffer(max_log_entries)


    @classmethod
    def from_cfg_dict(cls, cfg_dict: dict):
        """Instatiates Menu from cfg dictionary

        Parameters
        ----------
        cfg_dict : dict
            A dictionary usually loaded from a config json from IoTDashboard App

        Returns
        -------
        Menu
        """
        tmp_cls = cls(
            cfg_dict["controlID"],
            cfg_dict["title"],
            _get_title_position(cfg_dict["titlePosition"]),
            ControlPosition(cfg_dict["xPositionRatio"], cfg_dict["yPositionRatio"], cfg_dict["widthRatio"], cfg_dict["heightRatio"])
        )
        tmp_cls.parent_id = cfg_dict["parentID"]
        return tmp_cls

    def _get_log_from_timestamp(self, msg):
        data_str = ""
        try:
            dashboard_id = msg[3]
            from_date = dateutil.parser.isoparse(msg[4])
        except (IndexError, ValueError):
            return ""
        data_str += self._control_hdr_str + dashboard_id
        has_data = False
        for log in self.log.get():
            if log.timestamp > from_date:
                data_str += "\t" + log.to_json()
                has_data = True
        if has_data:
            return data_str


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
