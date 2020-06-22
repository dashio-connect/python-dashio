from .enums import Colour
from .control import Control


class Page(Control):
    """A Config only control"""

    def __init__(self,
                 control_id,
                 control_title='A page',
                 number_pages=1):
        super().__init__('PAGE', control_id)
        self.title = control_title
        self.number_pages = number_pages
        self._state_str = ''

    @property
    def number_pages(self) -> int:
        return self._cfg['numPages']

    @text.setter
    def number_pages(self, val: int):
        self._cfg['numPages'] = val
