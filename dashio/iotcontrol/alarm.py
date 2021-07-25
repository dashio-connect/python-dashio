"""alarm.py

    Exports Alarm
"""
from .control import Control
from .enums import SoundName


class Alarm(Control):
    """Alarm control for notifications

     Attributes
    ----------
    control_id : str
        a unique alarm identity string
    description : str
        A short description of the alarm
    sound_name : str
        the sound that the alarm makes.

    Methods
    -------
    send(header, body)
        Send an alarm with a header and body.
    """

    def __init__(self, control_id: str, description="Alarm Description", sound_name=SoundName.DEFAULT):
        """Alarm control for notifications

        Args:
            control_id (str): [description]
            description (str, optional): [description]. Defaults to "Alarm Descritption".
            sound_name ([soundName], optional): [description]. Defaults to SoundName.DEFAULT.
        """
        super().__init__("ALM", control_id)
        self.description = description
        self.sound_name = sound_name

    def send(self, header: str, body:str):
        """Sends the alarm.

        Args:
            header (str): ALarm Header
            body (str): Alarm body
        """
        self.message_tx_event(self.control_id, header, body)

    def get_state(self):
        return ""

    @property
    def description(self) -> str:
        return self._cfg["description"]

    @description.setter
    def description(self, val: str):
        self._cfg["description"] = val

    @property
    def sound_name(self) -> SoundName:
        return self._sound_name

    @sound_name.setter
    def sound_name(self, val: SoundName):
        self._sound_name = val
        self._cfg["soundName"] = val.value
