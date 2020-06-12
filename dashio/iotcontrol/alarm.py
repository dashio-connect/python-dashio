from .control import Control


class Alarm(Control):

    def __init__(self,
                 control_id,
                 control_title='Title',
                 body='Body',
                 header='Header',
                 description='An Alarm'):
        super().__init__('ALM', control_id)
        self.title = control_title
        self.body = body
        self.header = header
        self.description = description

    def send(self):
        self.message_tx_event(self.control_id, self._cfg['header'], self._cfg['body'])

    def get_state(self):
        pass

    @property
    def body(self):
        return self._cfg['body']

    @body.setter
    def body(self, val):
        self._cfg['body'] = val

    @property
    def description(self):
        return self._cfg['description']

    @description.setter
    def description(self, val):
        self._cfg['description'] = val

    @property
    def header(self):
        return self._cfg['header']

    @header.setter
    def header(self, val):
        self._cfg['header'] = val
