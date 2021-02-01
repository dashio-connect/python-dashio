from .control import Control


class DeviceSetup(Control):
    """A Config only control"""

    def __set_devicesetup(self):
        device_setup = ""
        if self._set_dashio:
            device_setup += "dashio"
        if self._set_name:
            if self._set_dashio:
                device_setup += ",name"
            else:
                device_setup += "name"
        if self._set_wifi:
            if self._set_dashio or self._set_name:
                device_setup += ",wifi"
            else:
                device_setup += "wifi"
        self._cfg["deviceSetup"] = device_setup

    def __init__(
        self,
        control_id,
        number_pages=0,
        edit_lock=True,
        set_name=False,
        set_wifi=False,
        set_dashio=False
    ):
        super().__init__("DVCE", control_id)
        self._state_str = ""
        self.number_pages = number_pages
        self.edit_lock = edit_lock
        self._set_name = set_name
        self._set_wifi = set_wifi
        self._set_dashio = set_dashio
        self.__set_devicesetup()

    @property
    def number_pages(self) -> int:
        return self._cfg["numPages"]

    @number_pages.setter
    def number_pages(self, val: int):
        self._cfg["numPages"] = val

    @property
    def edit_lock(self) -> bool:
        return self._cfg["editLock"]

    @edit_lock.setter
    def edit_lock(self, val: bool):
        self._cfg["editLock"] = val

    @property
    def set_name(self) -> bool:
        return self._set_name

    @set_name.setter
    def set_name(self, val: bool):
        self._set_name = val
        self.__set_devicesetup()

    @property
    def set_wifi(self) -> bool:
        return self._set_wifi

    @set_wifi.setter
    def set_wifi(self, val: bool):
        self._set_wifi = val
        self.__set_devicesetup()

    @property
    def set_dashio(self) -> bool:
        return self._set_dashio

    @set_dashio.setter
    def set_dashio(self, val: bool):
        self._set_dashio = val
        self.__set_devicesetup()
