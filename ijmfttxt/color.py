from math import sqrt
from typing import NewType, Tuple

COLOR_CUTOFF = 180

COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
}

def guessColor(red: float, green: float, blue: float) -> str:
    chi_values = []
    for c in COLORS.keys():
        chi_value = 0
        for v1, v2 in zip(COLORS[c], (red, green, blue)):
            chi = ((v1-v2)**2)
            chi_value += chi
        chi_values.append((c, sqrt(chi_value)))
    color, lowest_value = min(chi_values, key=lambda n: n[1])
    if lowest_value < COLOR_CUTOFF:
        return color
    else:
        return "Null"

def correctedColor(red: int, green: int, blue: int) -> Tuple[float]:
    max_color = max((red, green, blue))
    if max_color != 0:
        new_red = red/max_color*255
        new_green = green/max_color*255
        new_blue = blue/max_color*255
    else:
        new_red = new_green = new_blue = 0
    return new_red, new_green, new_blue

