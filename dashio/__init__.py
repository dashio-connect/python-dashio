"""
DashIO
------

[python-dashio](https://github.com/dashio-connect/python-dashio) -
Create beautiful mobile dashboards for your python project. The python-dashio
library allows easy setup of controls such as Dials, Text Boxes, Charts, Graphs,
and Notifications. You can define the look and layout of the controls on
your phone from your python code. There are three methods to connect to your
phone; Bluetooth Low Energy (BLE - on supported platforms), TCP, and MQTT via
the dash.dashio.io server.

MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from .device import Device
from .tcpconnection import TCPConnection
from .mqttconnection import MQTTConnection
from .zmqconnection import ZMQConnection
from .dashconnection import DashConnection
from .serialconnection import SerialConnection
from .schedular import Schedular
from .load_config import decode_cfg64, encode_cfg64, load_all_controls_from_config, get_control_dict_from_config, get_control_from_config
# from .bleconnection import BLEConnection
from .iotcontrol.enums import (
    Color,
    Icon,
    Precision,
    SoundName,
    Keyboard,
    TextAlignment,
    TitlePosition,
    SliderBarStyle,
    DialNumberPosition,
    DialStyle,
    ChartLineType,
    TimeGraphLineType,
    TimeGraphPositionOfKey,
    ButtonState,
    LabelStyle,
    KnobStyle,
    ChartXAxisLabelsStyle,
    TextFormat,
    DirectionStyle,
    ColorPickerStyle,
    ControlName,
    ButtonStyle,
    ButtonGroupStyle,
    MenuStyle,
    ConnectionState
)
from .iotcontrol.audio_visual_display import AudioVisualDisplay
from .iotcontrol.chart import Chart, ChartLine
from .iotcontrol.slider import Slider
from .iotcontrol.textbox import TextBox
from .iotcontrol.button import Button
from .iotcontrol.time_graph import TimeGraph, TimeGraphLine, DataPoint, DataPointArray
from .iotcontrol.knob import Knob
from .iotcontrol.dial import Dial
from .iotcontrol.direction import Direction
from .iotcontrol.map import Map, MapLocation
from .iotcontrol.alarm import Alarm
from .iotcontrol.menu import Menu
from .iotcontrol.selector import Selector
from .iotcontrol.label import Label
from .iotcontrol.device_view import DeviceView
from .iotcontrol.control import Control, ControlPosition
from .iotcontrol.button_group import ButtonGroup
from .iotcontrol.event_log import EventData, EventLog
from .iotcontrol.color_picker import ColorPicker

__all__ = [
    'Device',
    'TCPConnection',
    'MQTTConnection',
    'ZMQConnection',
    'DashConnection',
    'ConnectionState',
    'SerialConnection',
    'Schedular',
    'decode_cfg64',
    'encode_cfg64',
    'load_all_controls_from_config',
    'get_control_dict_from_config',
    'get_control_from_config',
    'Color',
    'Icon',
    'Precision',
    'SoundName',
    'Keyboard',
    'TextAlignment',
    'TitlePosition',
    'SliderBarStyle',
    'DialNumberPosition',
    'DialStyle',
    'ChartLineType',
    'TimeGraphLineType',
    'TimeGraphPositionOfKey',
    'ButtonState',
    'LabelStyle',
    'KnobStyle',
    'ChartXAxisLabelsStyle',
    'TextFormat',
    'DirectionStyle',
    'ColorPickerStyle',
    'ControlName',
    'ButtonStyle',
    'ButtonGroupStyle',
    'MenuStyle',
    'AudioVisualDisplay',
    'Chart',
    'ChartLine',
    'Slider',
    'TextBox',
    'Button',
    'TimeGraph',
    'TimeGraphLine',
    'DataPoint',
    'DataPointArray',
    'Knob',
    'Dial',
    'Direction',
    'Map',
    'MapLocation',
    'Alarm',
    'Menu',
    'Selector',
    'Label',
    'DeviceView',
    'Control',
    'ControlPosition',
    'ButtonGroup',
    'EventData',
    'EventLog',
    'ColorPicker'
]
