from .control import Control


class Name(Control):
    """A connection only control"""

    def __init__(self, device_name=""):
        super().__init__("NAME", device_name)

        self.message_rx_event += self.__get_device_name

    def __get_device_name(self, msg):
        self.control_id = msg[1]
        self.state_str = "\t{}\t{}\n".format(self.msg_type, msg[1])

    def set_device_name(self, device_name):
        self.control_id = device_name
        self.state_str = "\t{}\t{}\n".format(self.msg_type, device_name)