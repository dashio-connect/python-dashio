from .control import Control
from .event import Event

class Dash(Control):
    """A connection only control"""

    def __init__(self, control_id, username="", servername=""):
        super().__init__("DASH", control_id)
        self.message_rx_event += self.__set_dash
        self.username = username
        self.servername = servername
        self.state_str = "\t{}\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self.username, self.servername)

    def __set_dash(self, msg):
        self.username = msg[0]
        self.servername = msg[1]
        self.state_str = "\t{}\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self.username, self.servername)

    def set_mqtt(self, username, servername):
        self.username = username
        self.servername = servername
        self.state_str = "\t{}\t{}\t{}\t{}\n".format(self.msg_type, self.control_id, self.username, self.servername)

    @property
    def username(self):
        return self._cfg["userName"]

    @username.setter
    def username(self, val):
        self._cfg["userName"] = val

    @property
    def servername(self):
        return self._cfg["hostURL"]

    @servername.setter
    def servername(self, val):
        self._cfg["hostURL"] = val