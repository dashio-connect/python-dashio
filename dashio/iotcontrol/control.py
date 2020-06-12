from .event import Event
import json


class Control:
    def get_state(self):
        return self.state_str

    def get_cfg(self):
        cfg_str = '\tCFG\t' + self.msg_type + '\t' + json.dumps(self._cfg) + '\n'
        return cfg_str

    def __init__(self, msg_type, control_id):
        # Dictionary to store CFG json
        self._cfg = {}
        self.title = ''
        self.msg_type = msg_type
        self.control_id = control_id
        self.message_rx_event = Event()
        self.message_tx_event = Event()
        self._state_str = '\t{}\t{}\n'.format(self.msg_type, self.control_id)

    @property
    def state_str(self):
        return self._state_str

    @state_str.setter
    def state_str(self, val):
        self._state_str = val
        self.message_tx_event(val)

    # Use getter, setter properties to store the settings in the config dictionary
    @property
    def control_id(self):
        return self._cfg['identifier']

    @control_id.setter
    def control_id(self, val):
        self._cfg['identifier'] = val

    @property
    def title(self):
        return self._cfg['title']

    @title.setter
    def title(self, val):
        self._cfg['title'] = val
