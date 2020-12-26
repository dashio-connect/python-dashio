from .control import Control


class Alarm(Control):
    def get_cfg(self):
        # Overide get_cfg as Alarms don't have a config setting.
        return ""

    def __init__(self, control_id, title="Title", body="Body", header="Header"):
        super().__init__("ALM", control_id)
        self.title = title
        self.body = body
        self.header = header

    def send(self):
        self.message_tx_event(self.control_id, self._cfg["header"], self._cfg["body"])

    def get_state(self):
        pass

    @property
    def body(self) -> str:
        return self._cfg["body"]

    @body.setter
    def body(self, val: str):
        self._cfg["body"] = val

    @property
    def header(self) -> str:
        return self._cfg["header"]

    @header.setter
    def header(self, val: str):
        self._cfg["header"] = val
