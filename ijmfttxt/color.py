from typing import Tuple, List


COLORS = {
    "Rot1": (340, 360),
    "Grün": (70, 160),
    "Blau": (195, 265),
    "Gelb": (40, 70),
    "Türkis": (160, 195),
    "Magenta": (285, 340),
    "Red2": (0, 15),
    "Orange": (15, 40),
    "Violett": (265, 285),
}


class Color:
    """Klasse zum speichern verschiedenster Farbwerte"""

    def __init__(self, raw_clear, raw_red, raw_green, raw_blue):
        # raw color datat
        self._rc = raw_clear
        self._rr = raw_red
        self._rg = raw_green
        self._rb = raw_blue

        # rgb color data
        self._r, self._g, self._b = self.raw_to_rgb()

        # hsv color data
        self._h, self._s, self._v = self.rgb_to_hsv()

        # hls colo data
        self._s2, self._l = self._rgb_to_hls()

        # display color data
        self._dr, self._dg, self._db = self.rgb_to_dis()

    @property
    def raw(self) -> Tuple[int]:
        """Raw-RGB-Color-Daten

        Returns:
            Tuple[float]: Zahlen zwischen 0 und 37889
        """
        return self._rr, self._rg, self._rb

    @property
    def rawc(self) -> Tuple[float]:
        """Raw-RGBC-Color-Daten

        Returns:
            Tuple[float]: Zahlen zwischen 0 und 37889
        """
        return self._rc, self._rr, self._rg, self._rb

    @property
    def rgb(self) -> Tuple[float]:
        """RGB-Color-Daten

        Returns:
            Tuple[float]: Zahlen zwischen 0 und 1
        """
        return self._r, self._g, self._b

    @property
    def hsv(self) -> Tuple[float]:
        """HSV-Color-Daten

        Returns:
            Tuple[float]: Zahl zwischen 0 und 360, Zahlen zwischen 0 und 1
        """
        return self._h, self._s, self._v

    @property
    def hsl(self) -> Tuple[float]:
        """HSL-Color-Daten

        Returns:
            Tuple[float]: Zahl zwischen 0 und 360, Zahlen zwischen 0 und 1
        """
        return self._h, self._s2, self._l

    @property
    def drgb(self) -> Tuple[int]:
        """Display-RGB-Color-Daten

        Returns:
            Tuple[int]: Zahlen zwischen 0 und 255
        """
        return self._dr, self._dg, self._db

    @property
    def r(self) -> float:
        """RGB-Red-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._r

    @property
    def g(self) -> float:
        """RGB-Green-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._g

    @property
    def b(self) -> float:
        """RGB-Blue-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._b

    @property
    def dr(self) -> int:
        """Display-RGB-Red-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._dr

    @property
    def dg(self) -> int:
        """Display-RGB-Green-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._dg

    @property
    def db(self) -> int:
        """Display-RGB-Blue-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._db

    @property
    def h(self) -> float:
        """HSV/HSL-Hue-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._h

    @property
    def sv(self) -> float:
        """HSV-Saturation-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._s

    def sl(self) -> float:
        """HSL-Saturation-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._s2

    @property
    def v(self) -> float:
        """HSV-Value-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._v

    def l(self) -> float:
        """HSL-Lightness-Wert

        Returns:
            float: Zahl zwischen 0 und 1
        """
        return self._l

    @property
    def name(self) -> str:
        """Gibt bestüberinstimmenden Farbenname zurück

        Returns:
            str: Möglich: "Schwarz", "Weiß", "Grau", "Rot", "Grün", "Blau", "Orange", "Gelb", "Türkis", "Violett, "Magenta"
        """
        if self._v <= 0.2:
            return "Schwarz"
        if self._s <= 0.15:
            if self._v >= 0.7:
                return "Weiß"
            elif self._v >= 0.2:
                return "Grau"
            else:
                return "black"
        for k, r in COLORS.items():
            if self._h >= r[0] and self._h <= r[1]:
                if k == "Rot1" or k == "Rot2":
                    return "Rot"
                else:
                    return k

    def _raw_to_rgb(self) -> Tuple[float]:
        max_color = max(self.raw)
        return self._rr / max_color, self._rg / max_color, self._rb / max_color

    def _rgb_to_hsv(self) -> Tuple[float]:
        max_color = max(self._r, self._g, self._b)
        min_color = min(self._r, self._g, self._b)
        if max_color == min_color:
            hue = 0
        elif max_color == self._r:
            hue = 60 * (self._g - self._b) / (max_color - min_color)
        elif max_color == self._g:
            hue = 60 * (2 + (self._b - self._r) / (max_color - min_color))
        elif max_color == self._b:
            hue = 60 * (4 + (self._r - self._g) / (max_color - min_color))
        if hue < 0:
            hue += 360
        if max_color != 0:
            sat = (max_color - min_color) / (max_color)
        else:
            sat = 0
        value = max_color
        return hue, sat, value

    def _rgb_to_hls(self) -> Tuple[float]:
        max_color = max(self._r, self._g, self._b)
        min_color = min(self._r, self._g, self._b)
        if max_color == 0 or min_color == 1:
            sat = 0
        else:
            sat = (max_color - min_color) / (1 - abs(max_color + min_color - 1))
        lum = (max_color + min_color) / 2
        return sat, lum

    def _rgb_to_dis(self) -> Tuple[int]:
        return int(self._r * 255), int(self._g * 255), int(self._b * 255)

    def __repr__(self) -> str:
        return f"Color(raw_clear: {self._rc}; raw_red: {self._rr}; raw_green: {self._rg}; raw_blue: {self._rb})"
