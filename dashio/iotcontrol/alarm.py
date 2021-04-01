from .control import Control


class Alarm(Control):

    def __init__(self, control_id, header="Header", body="Body"):
        super().__init__("ALM", control_id)
        self.body = body
        self.header = header

    def send(self):
        self.message_tx_event(self.control_id, self.header, self.body)

    def get_state(self):
        pass

    @property
    def description(self) -> str:
        return self._cfg["description"]

    @description.setter
    def description(self, val: str):
        self._cfg["description"] = val

    @property
    def sound_name(self) -> str:
        return self._cfg["soundName"]

    @sound_name.setter
    def sound_name(self, val: str):
        self._cfg["soundName"] = val
