from .control import Control


class Name(Control):
    """A connection only control"""

    def __init__(self, device_name=""):
        super().__init__("NAME", device_name)
        self.message_rx_event += self.__set_device_name

    def __set_device_name(self, msg):
        self.control_id = msg[3]
        self.state_str = "\t{{device_id}}\t{}\t{}\n".format(self.msg_type, msg[0])

    def set_device_name(self, device_name: str):
        self.control_id = device_name
        self.state_str = "\t{{device_id}}\t{}\t{}\n".format(self.msg_type, device_name)
