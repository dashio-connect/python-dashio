from .control import Control
from .event import Event

class Dash():
    """A connection only control"""

    def __init__(self, username="", password=""):
        self.message_rx_event = Event()
        self.username = username
        self.password = password
        self.message_rx_event += self.__set_username_password


    def __set_username_password(self, msg):
        self.username = msg[0]
        self.password = msg[1]
