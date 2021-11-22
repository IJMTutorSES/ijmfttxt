from typing import Tuple


COLORS = {
    "red1": (340, 360),
    "green": (70, 160),
    "blue": (195, 265),
    "yellow": (40, 70),
    "cyan": (160, 195),
    "magenta": (285, 340),
    "red2": (0, 15),
    "orange": (15,40),
    "purple": (265, 285)
}

def guessColor(hue: float, sat: float, value: float) -> str:
    if value <= 0.2:
        return "black"
    if sat <= 0.15:
        if value >= 0.7:
            return "white"
        elif value >= 0.2:
            return "grey"
        else:
            return "black"
    for k, r in COLORS.items():
        if hue >= r[0] and hue <= r[1]:
            if k == "red1" or k == "red2":
                return "red"
            else:
                return k

def correctedColor(red: int, green: int, blue: int, limit: int = 1) -> Tuple[float]:
    max_color = max((red, green, blue))
    if max_color != 0:
        new_red = red/max_color*limit
        new_green = green/max_color*limit
        new_blue = blue/max_color*limit
    else:
        new_red = new_green = new_blue = 0
    return new_red, new_green, new_blue

def toHSV(red: int, green: int, blue: int) -> Tuple[float]:
    MAX = max(red,green,blue)
    MIN = min(red,green,blue)
    if MAX == MIN:
        hue = 0
    elif MAX == red:
        hue = 60 * (green-blue)/(MAX-MIN)
    elif MAX == green:
        hue = 60 * (2+(blue-red)/(MAX-MIN))
    elif MAX == blue:
        hue = 60 * (4+(red-green)/(MAX-MIN))
    if hue < 0:
        hue += 360
    if MAX != 0:
        sat = (MAX-MIN)/(MAX)
    else:
        sat = 0
    value = MAX
    return [hue,sat,value]
