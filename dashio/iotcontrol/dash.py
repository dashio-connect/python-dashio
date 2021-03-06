from .control import Control
from .event import Event

class Dash(Control):
    """A connection only control"""

    def __init__(self, control_id, username="", servername=""):
        super().__init__("DASH", control_id)
        self.message_rx_event += self.__set_dash
        self.username = username
        self.servername = servername
        self.state_str = self._state_str + "\t{}\t{}\n".format(self.username, self.servername)

    def __set_dash(self, msg):
        self.username = msg[3]
        self.servername = msg[4]
        self.state_str = self._state_str + "\t{}\t{}\n".format(self.username, self.servername)

    def set_mqtt(self, username, servername):
        self.username = username
        self.servername = servername
        self.state_str = self._state_str + "\t{}\t{}\n".format(self.username, self.servername)

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