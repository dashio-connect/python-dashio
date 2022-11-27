
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

class StringParameterSpec(BaseParameter):
    """String Parameter"""
    def __init__(self, param_id: str, name: str, existing_value: str):
        super().__init__("STRING_PARAM", param_id, name)
        self._param['value'] = existing_value

class FloatParameterSpec(BaseParameter):
    """Float Parameter"""
    def __init__(self, param_id: str, name: str, param_min: float, param_max: float, units: str, existing_value: float):
        super().__init__("FLOAT_PARAM", param_id, name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['units'] = units
        self._param['value'] = existing_value

class IntParameterSpec(BaseParameter):
    """Int Parameter"""
    def __init__(self, param_id: str, name: str, param_min: int, param_max: int, units: str, existing_value: int):
        super().__init__("FLOAT_PARAM", param_id, name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['units'] = units
        self._param['value'] = existing_value

class BoolParameterSpec(BaseParameter):
    """Bool Parameter"""
    def __init__(self, param_id: str, name: str, existing_value: bool):
        super().__init__("BOOL_PARAM", param_id, name)
        self._param['value'] = existing_value

class SelectorParameterSpec(BaseParameter):
    """Selection Parameter"""
    def __init__(self, param_id: str, name: str, selection: list, existing_value: str):
        super().__init__("SELECTION_PARAM", param_id, name)
        self._param['selection'] = selection
        self._param['value'] = existing_value

class SliderParameterSpec(BaseParameter):
    """Slider Parameter"""
    def __init__(self, param_id: str, name: str, param_min: float, param_max: float, step: float, existing_value: str):
        super().__init__("SLIDER_PARAM", param_id, name)
        self._param['min'] = param_min
        self._param['max'] = param_max
        self._param['step'] = step
        self._param['value'] = existing_value

class BaseParamValue:
    """Base class for Parameter"""
    def __init__(self, param_type: str, param_id: str, param_value):
        self._param = {
            'objectType': param_type,
            'paramID': param_id,
            'value': param_value
        }

    def __json__(self, **options):
        return self._param

class StringParamValue(BaseParamValue):
    """StringParamValue"""
    def __init__(self, param_id: str, param_value: str):
        super().__init__("STRING_VALUE", param_id, param_value)

class FloatParamValue(BaseParamValue):
    """FloatParamValue"""
    def __init__(self, param_id: str, param_value: str):
        super().__init__("FLOAT_VALUE", param_id, param_value)

class IntParamValue(BaseParamValue):
    """IntParamValue"""
    def __init__(self, param_id: str, param_value: str):
        super().__init__("INT_VALUE", param_id, param_value)

class BoolParamValue(BaseParamValue):
    """BoolParamValue"""
    def __init__(self, param_id: str, param_value: str):
        super().__init__("BOOL_VALUE", param_id, param_value)

class SelectionParamValue(BaseParamValue):
    """SelectionParamValue"""
    def __init__(self, param_id: str, param_value: str):
        super().__init__("SELECTION_VALUE", param_id, param_value)

class SliderParamValue(BaseParamValue):
    """SliderParamValue"""
    def __init__(self, param_id: str, param_value: str):
        super().__init__("SLIDER_VALUE", param_id, param_value)

class ActionControlCFG:
    """Action Control CFG"""
    def __init__(self, control_type: str, name: str, text: str, control_id: str, num_avail: int, is_persistent: bool, is_trigger: bool, is_io: bool, provisioning_list: list, param_list: list) -> None:
        self.uuid = shortuuid.uuid()
        self._param = {
            'objectType': f"{control_type}_CFG",
            'uuid': self.uuid,
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
