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


class Color:
    def __init__(self, raw_clear, raw_red, raw_green, raw_blue):
        #raw color datat
        self._rc = raw_clear
        self._rr = raw_red
        self._rg = raw_green
        self._rb = raw_blue
        
        #rgb color data
        self._r, self._g, self._b = self._to_rgb()

        #hsv color data
        self._h, self._s, self._v = self._to_hsv()

        #display color data
        self._dr, self._dg, self._db = self._to_dis()

    @property
    def raw(self):
        return [self._rr, self._rg, self._rb]
    
    @property
    def rawc(self):
        return [self._rc, self._rr, self._rg, self._rb]
    
    @property
    def rgb(self):
        return [self._r, self._g, self._b]
    
    @property
    def hsv(self):
        return [self._h, self._s, self._v]
    
    @property
    def drgb(self):
        return [self._dr, self._dg, self._db]

    @property
    def r(self):
        return self._r
    
    @property
    def g(self):
        return self._g

    @property
    def b(self):
        return self._b
    
    @property
    def dr(self):
        return self._dr
    
    @property
    def dg(self):
        return self._dg
    
    @property
    def db(self):
        return self._db

    @property
    def h(self):
        return self._h
    
    @property
    def s(self):
        return self._s
    
    @property
    def v(self):
        return self._v

    @property
    def color(self):
        if self._v <= 0.2:
            return "black"
        if self._s <= 0.15:
            if self._v >= 0.7:
                return "white"
            elif self._v >= 0.2:
                return "grey"
            else:
                return "black"
        for k, r in COLORS.items():
            if self._h >= r[0] and self._h <= r[1]:
                if k == "red1" or k == "red2":
                    return "red"
                else:
                    return k

    def _to_rgb(self):
        max_color = max(self.raw)
        return self._rr/max_color, self._rg/max_color, self._rb/max_color

    def _to_hsv(self):
        max_color = max(self._r,self._g,self._b)
        min_color = min(self._r,self._g,self._b)
        if max_color == min_color:
            hue = 0
        elif max_color == self._r:
            hue = 60 * (self._g-self._b)/(max_color-min_color)
        elif max_color == self._g:
            hue = 60 * (2+(self._b-self._r)/(max_color-min_color))
        elif max_color == self._b:
            hue = 60 * (4+(self._r-self._g)/(max_color-min_color))
        if hue < 0:
            hue += 360
        if max_color != 0:
            sat = (max_color-min_color)/(max_color)
        else:
            sat = 0
        value = max_color
        return hue,sat,value

    def _to_dis(self):
        return int(self._r*255), int(self._g*255), int(self._b*255)

    def __repr__(self) -> str:
        return f"Color(raw_clear: {self._rc}; raw_red: {self._rr}; raw_green: {self._rg}; raw_blue: {self._rb})"

