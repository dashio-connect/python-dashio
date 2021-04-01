import logging
from .event import Event
from .enums import TitlePosition
import json
import copy


class ControlPosition:
    def __init__(self, x_position_ratio, y_position_ratio, width_ratio, height_ratio):
        self.x_position_ratio = x_position_ratio
        self.y_position_ratio = y_position_ratio
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio

    def _set_size(self, page_size_x, page_size_y):
        logging.debug("Page X: {x}, Page Y: {y}".format(x=page_size_x, y=page_size_y))


class Control:
    def get_state(self) -> str:
        return ""

    def get_cfg(self, page_size_x, page_size_y):
        if self.control_position:
            self.control_position._set_size(page_size_x, page_size_y)
        cfg_str = "\tCFG\t" + self.msg_type + "\t" + json.dumps(self._cfg) + "\n"
        return cfg_str

    def __init__(self, msg_type, control_id, title=None, control_position=None, title_position=None):
        # Dictionary to store CFG json
        self._cfg = {}
        self._title = None
        if title is not None:
            self.title = title
        self._title_position = None
        if title_position is not None:
            self.title_position = title_position
        self.msg_type = msg_type
        self.control_id = control_id
        self.message_rx_event = Event()
        self.message_tx_event = Event()
        self._state_str = "\t{{device_id}}\t{control_type}\t{control_id}\t".format(control_type=self.msg_type, control_id=self.control_id)
        self._control_position = None
        if control_position is not None:
            self.control_position = control_position

    @property
    def state_str(self):
        return self._state_str

    @state_str.setter
    def state_str(self, val):
        self.message_tx_event(val)

    # Use getter, setter properties to store the settings in the config dictionary
    @property
    def parent_id(self) -> str:
        return self._cfg["parentID"]

    @parent_id.setter
    def parent_id(self, val: str):
        self._cfg["parentID"] = val

    @property
    def control_id(self) -> str:
        return self._cfg["controlID"]

    @control_id.setter
    def control_id(self, val: str):
        self._cfg["controlID"] = val

    @property
    def title(self) -> str:
        return self._cfg["title"]

    @title.setter
    def title(self, val: str):
        self._cfg["title"] = val

    @property
    def control_position(self) -> ControlPosition:
        return self._control_position

    @control_position.setter
    def control_position(self, val: ControlPosition):
        self._control_position = copy.copy(val)
        self._cfg["xPositionRatio"] = val.x_position_ratio
        self._cfg["yPositionRatio"] = val.y_position_ratio
        self._cfg["widthRatio"] = val.width_ratio
        self._cfg["heightRatio"] = val.height_ratio

    @property
    def title_position(self) -> TitlePosition:
        return self._title_position

    @title_position.setter
    def title_position(self, val: TitlePosition):
        self._title_position = val
        self._cfg["titlePosition"] = val.value
