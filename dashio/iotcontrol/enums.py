from enum import Enum


class Icon(Enum):
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


class LabelStyle(Enum):
    BASIC = "BASIC"
    GROUP = "GROUP"

class KnobStyle(Enum):
    NORMAL = "NORMAL"
    PAN = "PAN"

class Precision(Enum):
    OFF = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class TitlePosition(Enum):
    NONE = "None"
    TOP = "Top"
    BOTTOM = "Bottom"


class ButtonState(Enum):
    ON = "ON"
    OFF = "OFF"
    FLASH = "FLASH"


class Keyboard(Enum):
    NONE = "NONE"
    ALL_CHARS = "ALL"
    NUMERIC = "NUM"
    HEX = "HEX"


class TextAlignment(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class SliderBarType(Enum):
    SEGMENTED = "seg"
    SOLID = "solid"


class DialPosition(Enum):
    OFF = "off"
    LEFT = "left"
    RIGHT = "right"


class DialStyle(Enum):
    STD = "upright"
    INVERTED = "inverted"


class GraphLineType(Enum):
    LINE = "LINE"
    BAR = "BAR"
    SEGBAR = "SEGBAR"
    PEAKBAR = "PEAKBAR"
    DELETE = "DEL"


class GraphXAxisLabelsStyle(Enum):
    ON = "on"
    BETWEEN = "between"


class TimeGraphLineType(Enum):
    LINE = "LINE"
    BAR = "BAR"
    BOOL = "BOOL"
    DEL = "DEL"


class MapType(Enum):
    STANDARD = "Standard"
    SATELLITE = "Satellite"
    HYBRID = "Hybrid"


class TimeGraphTimeScale(Enum):
    FIVEMINUTES = "5 minutes"
    FIFTEENMINS = "15 minutes"
    THIRTYMINS = "30 minutes"
    ONEHOUR = "1 hour"
    THREEHOURS = "3 hours"
    SIXHOURS = "6 hours"
    TWELVEHOURS = "12 hours"
    ONEDAY = "1 day"
    TWODAYS = "2 days"
    THREEDAYS = "3 days"
    ONEWEEK = "1 week"
    TWOWEEKS = "2 weeks"
    ONEMONTH = "1 month"
    THREEMONTHS = "3 months"
    SIXMONTHS = "6 months"
    ONEYEAR = "1 year"


class TimeGraphPositionOfKey(Enum):
    TOPLEFT = "Top Left"
    TOPRIGHT = "Top Right"


class Color(Enum):
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
