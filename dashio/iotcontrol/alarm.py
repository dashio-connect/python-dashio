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
from ..constants import BAD_CHARS
from .control import Control
from .enums import SoundName


class Alarm(Control):
    """Alarm control for sending notifications

    Attributes
    ----------
    control_id : str
       An unique control identity string. The control identity string must be a unique string for each control per device
    description : str
        A short description of the alarm
    sound_name : str
        the sound that the alarm makes

    Methods
    -------
    send(header, body)
        Send an alarm with a header and body
    """

    def __init__(self, control_id: str, description="Alarm Description", sound_name=SoundName.DEFAULT):
        """Alarm control for notifications

        Parameters
        ----------
            control_id (str):
                Set the control id string
            description (str, optional):
                Sets the alarm description. Defaults to "Alarm Description"
            sound_name ([soundName], optional):
                The sound name to use. Defaults to SoundName.DEFAULT
        """
        super().__init__("ALM", control_id)
        self.description = description.translate(BAD_CHARS)
        self.sound_name = sound_name

    def send(self, header: str, body: str):
        """Sends the alarm

        Parameters
        ----------
            header : str
                ALarm Header
            body : str
                Alarm body
        """
        self.message_tx_event(self.control_id, header, body)

    @property
    def description(self) -> str:
        """description

        Returns
        -------
        str
            description
        """
        return self._cfg["description"]

    @description.setter
    def description(self, val: str):
        self._cfg["description"] = val

    @property
    def sound_name(self) -> SoundName:
        """sound_name

        Returns
        -------
        SoundName
            sound_name
        """
        return self._sound_name

    @sound_name.setter
    def sound_name(self, val: SoundName):
        self._sound_name = val
        self._cfg["soundName"] = val.value
