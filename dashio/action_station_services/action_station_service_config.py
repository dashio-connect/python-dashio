import shortuuid
from pydantic import BaseModel, Field


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

class ActionTask(BaseModel):
    objectType: str
    name: str
    uuid: str
    actions: list

class ActionReadControl(BaseModel):
    objectType: str
    deviceID: str
    controlType: str
    controlID: str

    def action(msg):
        pass

class ActionWriteControl(BaseModel):
    objectType: str
    deviceID: str
    controlType: str
    controlID: str

class ActionSendAlarm(BaseModel):
    objectType: str
    alarmID: str
    title: str
    body: str

class ActionWriteMem(BaseModel):
    objectType: str
    memoryID: str
    memType: str
    thing: str

class ActionReadMem(BaseModel):
    objectType: str
    memoryID: str
    memType: str

class ActionBitwise(BaseModel):
    objectType: str
    bw_or: str = Field(alias='or')
    bw_and: str = Field(alias='and')
    shiftRight: int

class ActionScale(BaseModel):
    objectType: str
    scale: float
    offset: float

class ActionIf(BaseModel):
    objectType: str
    value: float
    ifOperator: str
    ifTrue: list = []
    ifFalse: list = []


def task_parse(task: dict) -> ActionTask:
    action_tree = []

    def create_action(action: dict):
        match action['objectType']:
            case 'READ_CONTROL':
                return ActionReadControl(**action)
            case 'WRITE_CONTROL':
                return ActionWriteControl(**action)
            case 'SEND_ALARM':
                return ActionSendAlarm(**action)
            case 'WRITE_MEM':
                return ActionWriteMem(**action)
            case 'READ_MEM':
                return ActionReadMem(**action)
            case 'BITWISE':
                return ActionBitwise(**action)
            case 'SCALE':
                return ActionScale(**action)
            case 'IF':
                return ActionIf(**action)

    def parse_tree(tree: list, actions: list) -> str:
        if len(actions) > 0:
            action = actions.pop(0)
        else:
            return 'DONE'
        if action['objectType'] == 'ELSE':
            return 'ELSE'
        if action['objectType'] == 'ENDIF':
            return 'ENDIF'
        new_action = create_action(action)
        if new_action.objectType == 'IF':
            new_action.ifTrue = []
            result = parse_tree(new_action.ifTrue, actions)
            if result == 'ELSE':
                new_action.ifFalse = []
                result = parse_tree(new_action.ifFalse, actions)
        tree.append(new_action)
        result = ''
        while result not in ['DONE', 'ELSE', 'ENDIF']:
            result = parse_tree(tree, actions)
        return result

    new_actions = task['actions'].copy()
    parse_tree(action_tree, new_actions)

    new_task = task.copy()
    new_task['actions'] = action_tree
    return ActionTask(**new_task)
