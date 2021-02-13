from .control import Control
import json

class TCP(object):

    """A connection only control"""
    def get_state(self) -> str:
        return ""

    def get_cfg(self, page_size_x, page_size_y):
        cfg_str = "\tCFG\t" + self.msg_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, control_id, ip_address="", port=5650):
        self._cfg = {}
        self.msg_type = "TCP"
        self.control_id = control_id
        self.ip_address = ip_address
        self.port = port

    @property
    def ip_address(self) -> str:
        return self._cfg["ipAddress"]

    @ip_address.setter
    def ip_address(self, val: str):
        self._cfg["ipAddress"] = val

    @property
    def port(self) -> int:
        return self._cfg["port"]

    @port.setter
    def port(self, val: int):
        self._cfg["port"] = val
