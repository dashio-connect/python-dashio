
# Step: 1
# create the patch
from json import JSONEncoder

import shortuuid

def wrapped_default(self, obj):
    """Badness"""
    return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)
wrapped_default.default = JSONEncoder().default

# apply the patch
JSONEncoder.original_default = JSONEncoder.default
JSONEncoder.default = wrapped_default

class BaseParameter:
    """Base class for Parameter"""
    def __init__(self, param_type: str, name: str):
        self._param = {
            'objectType': param_type,
            'name': name,
            'uuid': shortuuid.uuid()
        }

    def __json__(self, **options):
        return self._param

class ListParameterSpec(BaseParameter):
    """List Parameter"""
    def __init__(self, name: str, text: str, param_list: list):
        super().__init__("LIST_PARAM", name)
        self._param['text'] = text
        self._param["list"] = param_list

class StringParameterSpec(BaseParameter):
    """String Parameter"""
    def __init__(self, name: str, existing_value: int):
        super().__init__("STRING_PARAM", name)
        self._param['value'] = existing_value


class FloatParameterSpec(BaseParameter):
    """Float Parameter"""
    def __init__(self, name: str, param_min: float, param_max: float, units: str, existing_value: float):
        super().__init__("FLOAT_PARAM", name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['units'] = units
        self._param['value'] = existing_value

class IntParameterSpec(BaseParameter):
    """Int Parameter"""
    def __init__(self, name: str, param_min: int, param_max: int, units: str, existing_value: int):
        super().__init__("INT_PARAM", name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['units'] = units
        self._param['value'] = existing_value

class BoolParameterSpec(BaseParameter):
    """Bool Parameter"""
    def __init__(self, name: str, existing_value: bool):
        super().__init__("BOOL_PARAM", name)
        self._param['value'] = existing_value

class SelectorParameterSpec(BaseParameter):
    """Selection Parameter"""
    def __init__(self, name: str, selection: list, existing_value: str):
        super().__init__("SELECTION_PARAM", name)
        self._param['selection'] = selection
        self._param['value'] = existing_value

class SliderParameterSpec(BaseParameter):
    """Slider Parameter"""
    def __init__(self, name: str, param_min: float, param_max: float, step: float, existing_value: str):
        super().__init__("SLIDER_PARAM", name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['step'] = step
        self._param['value'] = existing_value

class ActionServiceCFG:
    """Action Control CFG"""
    def __init__(self, control_type: str, name: str, text: str, control_id: str, num_avail: int, is_trigger: bool, is_io: bool, provisioning_list: list, param_in_list: list, revision=1) -> None:
        self.uuid = shortuuid.uuid()
        self._config_def = {
            'objectType': "CONFIG",
            'objectName': control_type,
            'revision': revision,
            'uuid': self.uuid,
            'name': name,
            'text': text,
            'controlID': control_id,
            'numAvail': num_avail,
            'isTrigger': is_trigger,
            'isIO': is_io,
            'provisioning': provisioning_list,
            'parameters': param_in_list,
            #'parametersOut': param_out_list
        }

    def __json__(self, **options):
        return self._config_def
