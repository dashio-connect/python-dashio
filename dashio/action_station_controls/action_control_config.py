
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
    def __init__(self, param_type: str, param_id: str, name: str):
        self._param = {
            'objectType': param_type,
            'name': name,
            'paramID': param_id
        }

    def __json__(self, **options):
        return self._param

class StringParameter(BaseParameter):
    """String Parameter"""
    def __init__(self, param_id: str, name: str, existing_value: str):
        super().__init__("STRING_PARAM", param_id, name)
        self._param['existingValue'] = existing_value

class FloatParameter(BaseParameter):
    """Float Parameter"""
    def __init__(self, param_id: str, name: str, param_min: float, param_max: float, units: str, existing_value: float):
        super().__init__("FLOAT_PARAM", param_id, name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['units'] = units
        self._param['existingValue'] = existing_value

class IntParameter(BaseParameter):
    """Int Parameter"""
    def __init__(self, param_id: str, name: str, param_min: int, param_max: int, units: str, existing_value: int):
        super().__init__("FLOAT_PARAM", param_id, name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['units'] = units
        self._param['existingValue'] = existing_value

class BoolParameter(BaseParameter):
    """Bool Parameter"""
    def __init__(self, param_id: str, name: str, existing_value: bool):
        super().__init__("BOOL_PARAM", param_id, name)
        self._param['existingValue'] = existing_value

class SelectionParameter(BaseParameter):
    """Selection Parameter"""
    def __init__(self, param_id: str, name: str, selection: str, existing_value: str):
        super().__init__("SELECTION_PARAM", param_id, name)
        self._param['selection'] = selection
        self._param['existingValue'] = existing_value

class SliderParameter(BaseParameter):
    """Slider Parameter"""
    def __init__(self, param_id: str, name: str, param_min: float, param_max: float, step: float, existing_value: str):
        super().__init__("SLIDER_PARAM", param_id, name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['step'] = step
        self._param['existingValue'] = existing_value

class ActionControlCFG:
    """Action Control CFG"""
    def __init__(self, control_type: str, name: str, text: str, control_id: str, num_avail: int, is_persistent: bool, is_trigger: bool, is_io: bool, provisioning_list: list, param_list: list) -> None:
        self._param = {
            'objectType': f"{control_type}_CFG",
            'uuid': shortuuid.uuid(),
            'name': name,
            'text': text,
            'controlID': control_id,
            'numAvail': num_avail,
            'isPersistent': is_persistent,
            'isTrigger': is_trigger,
            'isIO': is_io,
            'provisioning': provisioning_list,
            'parameters': param_list
        }

    def __json__(self, **options):
        return self._param
