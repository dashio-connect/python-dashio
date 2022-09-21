"""
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
from enum import Enum


class Icon(Enum):
    """
    All the Icons
    """
    NONE = "None"
    DOT = "Dot"
    PAD = "Pad"
    UP = "Up"
    DOWN = "Down"
    LEFT = "Left"
    RIGHT = "Right"
    UP_LEFT = "Up Left"
    DOWN_LEFT = "Down Left"
    DOWN_RIGHT = "Down Right"
    UP_RIGHT = "Up Right"
    LEFT_DOUBLE = "Left Double"
    RIGHT_DOUBLE = "Right Double"
    BEGINNING = "Beginning"
    END = "End"
    PAUSE = "Pause"
    STOP = "Stop"
    PLAY = "Play"
    COG = "Cog"
    LIGHT_BULB = "Light Bulb"
    ON_OFF = "On Off"
    REFRESH = "Refresh"
    TRASH = "Trash"
    MUSIC = "Music"
    SOUND = "Sound"
    BELL = "Bell"
    ATTENTION_1 = "Attention 1"
    ATTENTION_2 = "Attention 2"
    CIRCLE = "Circle"
    SQUARE = "Square"
    TRIANGLE = "Triangle"
    MAIL = "Mail"
    BOAT = "Boat"
    SAILBOAT = "Sailboat"
    CAR = "Car"
    BRIGHTNESS = "Brightness"
    TEMPERATURE = "Temperature"
    CLOUD = "Cloud"
    WEATHER = "Weather"
    LIGHTNING = "Lightning"
    DOOROPEN = "Door Open"
    DOORCLOSED = "Door Closed"
    BEDROOM = "Bedroom"
    GARAGE = "Garage"
    HOUSE = "House"
    LED = "LED"
    PADLOCK = "Padlock"
    PROPELLER_1 = "Propeller 1"
    PROPELLER_2 = "Propeller 2"
    FAN = "Fan"
    MENU = "Menu"
    ZOOM_IN = "Zoom In"
    ZOOM_OUT = "Zoom Out"
    RIGHT_DOUBLE_2 = "Right Double 2"
    LOCATION = "Location"
    DIRECTION = "Direction"
    SWITCH = "Switch"


class SoundName(Enum):
    """Sound names"""
    DEFAULT = "Default"
    QUIET = "Quiet"
    BELL = "Bell"
    DOORBELL1 = "Door Bell 1"
    DOORBELL2 = "Door Bell 2"
    ALARM = "Alarm"
    COW = "Cow"
    OVERSPEED = "Overspeed"
    SADTRUMPED = "Sad Trumped"
    SHIPHORN = "Ship Horn"
    SQUEAKY = "Squeaky"
    SLAP = "Slap"
    WHIP1 = "Whip 1"
    WHIP2 = "Whip 2"
    PLOP = "Plop"
    PLOPPLIPPLIP = "Plop Plip Plip"
    SWITCH = "Switch"
    WHOOSH = "Whoosh"
    BOING = "Boing"


class DeviceViewStyle(Enum):
    """DeciveView Styles"""
    BASIC = "BASIC"
    BORDERS = "BORDERS"


class ColorPickerStyle(Enum):
    """Picker styles"""
    WHEEL = "Wheel"
    SPECTRUM = "Spectrum"


class LabelStyle(Enum):
    """Label styles"""
    BASIC = "BASIC"
    GROUP = "GROUP"
    BORDER = "BORDER"


class KnobStyle(Enum):
    """Knob styles"""
    NORMAL = "NORMAL"
    PAN = "PAN"


class Precision(Enum):
    """Precisions"""
    OFF = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class TitlePosition(Enum):
    """Title positions"""
    NONE = "None"
    TOP = "Top"
    BOTTOM = "Bottom"


class ButtonState(Enum):
    """Button states"""
    ON = "ON"
    OFF = "OFF"
    FLASH = "FLASH"


class Keyboard(Enum):
    """Keyboards"""
    NONE = "NONE"
    ALL = "ALL"
    NUMERIC = "NUM"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    INTERVAL = "INTVL"
    INT = "INT"
    HEX = "HEX"


class TextFormat(Enum):
    """Text formats"""
    NONE = "NONE"
    NUMBER = "NUM"
    DATETIME = "DATETIME"
    DATELONG = "DTLONG"
    INTERVAL = "INTVL"


class TextAlignment(Enum):
    """Text alignments"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class SliderBarStyle(Enum):
    """Slider bar types"""
    SEG = "seg"
    SOLID = "solid"


class DialNumberPosition(Enum):
    """Dial number positions"""
    OFF = "off"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class DialStyle(Enum):
    """Dial styles"""
    PIE = "pie"
    PIEINV = "pieinv"
    BAR = "bar"


class DirectionStyle(Enum):
    """Direction styles"""
    NSEW = "nsew"
    DEG = "deg"
    DEGPS = "degps"


class GraphLineType(Enum):
    """Graph line types"""
    LINE = "LINE"
    BAR = "BAR"
    SEGBAR = "SEGBAR"
    PEAKBAR = "PEAKBAR"
    DELETE = "DEL"


class GraphXAxisLabelsStyle(Enum):
    """Graph X axis label styles"""
    ON = "on"
    BETWEEN = "between"


class TimeGraphLineType(Enum):
    """Time grapgh line types"""
    LINE = "LINE"
    BAR = "BAR"
    BOOL = "BOOL"
    DEL = "DEL"


class TimeGraphPositionOfKey(Enum):
    """Time grapgh positions of key"""
    TOPLEFT = "Top Left"
    TOPRIGHT = "Top Right"


class Color(Enum):
    """Colors"""
    BLACK = 0
    WHITE = 1
    MAROON = 2
    SIENNA = 3
    RED = 4
    ORANGE_RED = 5
    DEEPPINK = 6
    ORANGE = 7
    GOLD = 8
    YELLOW = 9
    GREEN = 10
    SEA_GREEN = 11
    LIME = 12
    LIGHT_GREEN = 13
    SPRING_GREEN = 14
    OLIVE = 15
    MIDNIGHT_BLUE = 16
    NAVY_BLUE = 17
    BLUE = 18
    ROYAL_BLUE = 19
    STEEL_BLUE = 20
    SKY_BLUE = 21
    AQUA = 22
    TURQUOISE = 23
    TEAL = 24
    DARK_SLATE_GRAY = 25
    PURPLE = 26
    SLATE_BLUE = 27
    BLUE_VIOLET = 28
    FUSCIA = 29
    VIOLET = 30
    PINK = 31
    ROSY_BROWN = 32
    BISQUE = 33
    SEA_SHELL = 34
    LAVENDER = 35
    SLATE_GRAY = 36
    DIM_GRAY = 37
    GRAY = 38
    DARK_GRAY = 39
    SILVER = 40
    LIGHT_GRAY = 41
    GAINSBORO = 42
    GHOST_WHITE = 43
    WHITE_SMOKE = 44
    DARK_RED = 45
    BROWN = 46
    FIREBRICK = 47
    CRIMSON = 48
    TOMATO = 49
    CORAL = 50
    INDIAN = 51
    LIGHT_CORAL = 52
    DARK_SALMON = 53
    SALMON = 54
    LIGHT_SALMON = 55
    DARK_ORANGE = 56
    DARK_GOLDEN_ROD = 57
    GOLDEN_ROD = 58
    PALE_GOLDEN_ROD = 59
    DARK_KHAKI = 60
    KHAKI = 61
    YELLOW_GREEN = 62
    DARK_OLIVE_GREEN = 63
    OLIVE_DRAB = 64
    LAWN_GREEN = 65
    CHARTREUSE = 66
    GREEN_YELLOW = 67
    DARK_GREEN = 68
    FOREST_GREEN = 69
    LIME_GREEN = 70
    PALE_GREEN = 71
    DARK_SEA_GREEN = 72
    MEDIUM_SPRING_GREEN = 73
    MEDIUM_AQUAMARINE = 74
    MEDIUM_SEA_GREEN = 75
    LIGHT_SEA_GREEN = 76
    DARK_CYAN = 77
    LIGHT_CYAN = 78
    DARK_TURQUOISE = 79
    MEDIUM_TURQUOISE = 80
    PALE_TURQUOISE = 81
    AQUAMARINE = 82
    POWDER_BLUE = 83
    CADET_BLUE = 84
    CORNFLOWER_BLUE = 85
    DEEP_SKY_BLUE = 86
    DODGER_BLUE = 87
    LIGHT_BLUE = 88
    LIGHT_SKY_BLUE = 89
    DARK_BLUE = 90
    MEDIUM_BLUE = 91
    INDIGO = 92
    DARK_SLATE_BLUE = 93
    MEDIUM_SLATE_BLUE = 94
    MEDIUM_PURPLE = 95
    DARK_MAGENTA = 96
    DARK_VIOLET = 97
    DARK_ORCHID = 98
    MEDIUM_ORCHID = 99
    THISTLE = 100
    PLUM = 101
    ORCHID = 102
    MEDIUM_VIOLET_RED = 103
    PALE_VIOLET_RED = 104
    HOT_PINK = 105
    LIGHT_PINK = 106
    ANTIQUE_WHITE = 107
    BEIGE = 108
    BLANCHED_ALMOND = 109
    WHEAT = 110
    CORN_SILK = 111
    LEMON_CHIFFON = 112
    LIGHT_GOLDEN_ROD_YELLOW = 113
    LIGHT_YELLOW = 114
    SADDLE_BROWN = 115
    CHOCOLATE = 116
    PERU = 117
    SANDY_BROWN = 118
    BURLY_WOOD = 119
    TAN = 120
    MOCCASIN = 121
    NAVAJO_WHITE = 122
    PEACH_PUFF = 123
    MISTY_ROSE = 124
    LAVENDER_BLUSH = 125
    LINEN = 126
    OLD_LACE = 127
    PAPAYA_WHIP = 128
    MINT_CREAM = 129
    LIGHT_SLATE_GRAY = 130
    LIGHT_STEEL_BLUE = 131
    FLORAL_WHITE = 132
    ALICE_BLUE = 133
    HONEYDEW = 134
    IVORY = 135
    AZURE = 136
    SNOW = 137
