import shortuuid
from pydantic import BaseModel


def to_camel(string: str) -> str:
    string_split = string.split("_")
    return string_split[0] + "".join(word.capitalize() for word in string_split[1:])

class BaseParameter(BaseModel):
    objectType: str
    name: str
    uuid: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class ListParameterSpec(BaseParameter):
    """List Parameter"""
    text: str
    param_list: list
    objectType = "LIST_PARAM"

class StringParameterSpec(BaseParameter):
    """String Parameter"""
    objectType = "STRING_PARAM"
    value: str

class FloatParameterSpec(BaseParameter):
    """Float Parameter"""
    objectType = "FLOAT_PARAM"
    min: float
    max: float
    units: str
    value: float

class IntParameterSpec(BaseParameter):
    """Int Parameter"""
    objectType = "INT_PARAM"
    min: int
    max: int
    units: str
    value: int

class BoolParameterSpec(BaseParameter):
    """Bool Parameter"""
    objectType = "BOOL_PARAM"
    value: bool

class SelectorParameterSpec(BaseParameter):
    """Selection Parameter"""
    objectType = "SELECTION_PARAM"
    selection: list[str]
    value: str


class SliderParameterSpec(BaseParameter):
    """Slider Parameter"""
    objectType = "SLIDER_PARAM"
    min: float
    max: float
    step: float
    value: float

class ActionServiceCFG(BaseModel):
    objectType: str = "CONFIG"
    objectName: str
    revision: int = 1
    uuid: str
    name: str
    text: str
    controlID: str
    numAvail: int
    isTrigger: bool
    isIO: bool
    provisioning: list
    parameters: list

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
