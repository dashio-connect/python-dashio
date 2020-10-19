from .control import Control


class TCP(Control):
    """A connection only control"""

    def get_state(self):
        return ""

    def __init__(self, control_id, ip_address="", port="5000"):
        super().__init__("TCP", control_id)
        self.message_rx_event += self.__set_tcp
        self.ip_address = ip_address
        self.port = port

    def __set_tcp(self, msg):
        self.ip_address = msg[0]
        self.port = msg[1]

    def set_tcp(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

    @property
    def ip_address(self):
        return self._cfg["ipAddress"]

    @ip_address.setter
    def ip_address(self, val):
        self._cfg["ipAddress"] = val

    @property
    def port(self):
        return self._cfg["port"]

    @port.setter
    def port(self, val):
        self._cfg["port"] = val
