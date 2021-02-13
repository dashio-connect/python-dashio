from .control import Control
import json

class MQTT(object):

    """A connection only control"""
    def get_state(self):
        return ""
    
    def get_cfg(self, page_size_x, page_size_y):
        cfg_str = "\tCFG\t" + self.msg_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, username="", password="", servername="", use_ssl=False):
        self._cfg = {}
        self.msg_type = "MQTT"
        self.control_id = control_id
        self.username = username
        self.servername = servername

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
