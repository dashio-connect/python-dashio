from .control import Control


class MQTT(Control):
    """A connection only control"""

    def get_state(self):
        return ""

    def __init__(self, control_id, username="", servername=""):
        super().__init__("MQTT", control_id)
        self.message_rx_event += self.__set_mqtt
        self.username = username
        self.servername = servername

    def __set_mqtt(self, msg):
        self.username = msg[3]
        self.servername = msg[4]

    def set_mqtt(self, username, servername):
        self.username = username
        self.servername = servername

    @property
    def username(self) -> str:
        return self._cfg["userName"]

    @username.setter
    def username(self, val: str):
        self._cfg["userName"] = val

    @property
    def servername(self) -> str:
        return self._cfg["hostURL"]

    @servername.setter
    def servername(self, val: str):
        self._cfg["hostURL"] = val
