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
from .control import Control


class Alarm(Control):
    """Alarm control for sending notifications

    Attributes
    ----------
    control_id : str
       An unique control identity string. The control identity string must be a unique string for each control per device

    Methods
    -------
    send(header, body)
        Send an alarm with a header and body
    """

    def get_cfg(self, data):
        """Alarms do not appear in the CFG
        """
        return ""

    def __init__(self, control_id: str):
        """Alarm control for notifications

        Parameters
        ----------
            control_id (str):
                Set the control id string
        """
        super().__init__("ALM", control_id)

    def send(self, header: str, body: str):
        """Sends the alarm

        Parameters
        ----------
            header : str
                ALarm Header
            body : str
                Alarm body
        """
        self._message_tx_event(self.control_id, header, body)
