from .control import Control
from .enums import SoundName

class Alarm(Control):

    def __init__(self, control_id, description="Alarm Descritption", sound_name=SoundName.DEFAULT):
        super().__init__("ALM", control_id)
        self.description = description
        self.sound_name = sound_name

    def send(self, header, body):
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
