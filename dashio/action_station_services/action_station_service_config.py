from pydantic import BaseModel, Field
from typing import Optional


class BaseParameter(BaseModel):
    objectType: str
    name: str
    uuid: str


class ListParameterSpec(BaseParameter):
    """List Parameter"""
    text: str
    param_list: list
    objectType: str = "LIST_PARAM"


class StringParameterSpec(BaseParameter):
    """String Parameter"""
    objectType: str = "STRING_PARAM"
    value: str


class FloatParameterSpec(BaseParameter):
    """Float Parameter"""
    objectType: str = "FLOAT_PARAM"
    min: float
    max: float
    units: str
    value: float


class IntParameterSpec(BaseParameter):
    """Int Parameter"""
    objectType: str = "INT_PARAM"
    min: int
    max: int
    units: str
    value: int


class BoolParameterSpec(BaseParameter):
    """Bool Parameter"""
    objectType: str = "BOOL_PARAM"
    value: bool


class SelectorParameterSpec(BaseParameter):
    """Selection Parameter"""
    objectType: str = "SELECTION_PARAM"
    selection: list
    value: str


class SliderParameterSpec(BaseParameter):
    """Slider Parameter"""
    objectType: str = "SLIDER_PARAM"
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
    bw_or: Optional[int] = Field(alias='or')
    bw_and: Optional[int] = Field(alias='and')
    shiftRight: Optional[int]


class ActionScale(BaseModel):
    objectType: str
    scale: float
    offset: float


class ActionIf(BaseModel):
    objectType: str
    value: str
    fieldNo: int = 0
    fieldType: str = 'float'
    ifOperator: str
    ifTrue: list = []
    ifFalse: list = []


MAP_ACTION_DICT = {
    'READ_CONTROL': lambda action: ActionReadControl(**action),
    'WRITE_CONTROL': lambda action: ActionWriteControl(**action),
    'SEND_ALARM': lambda action: ActionSendAlarm(**action),
    'WRITE_MEM': lambda action: ActionWriteMem(**action),
    'READ_MEM': lambda action: ActionReadMem(**action),
    'BITWISE': lambda action: ActionBitwise(**action),
    'SCALE': lambda action: ActionScale(**action),
    'IF': lambda action: ActionIf(**action)
}


def task_parse(task: dict) -> ActionTask:
    action_tree = []

    def parse_tree(tree: list, actions: list) -> str:
        if len(actions) > 0:
            action = actions.pop(0)
        else:
            return 'DONE'
        if action['objectType'] == 'ELSE':
            return 'ELSE'
        if action['objectType'] == 'ENDIF':
            return 'ENDIF'
        new_action = MAP_ACTION_DICT[action['objectType']](action)
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
