from . import ftrobopy
from .apds import Apds
from . import color


class TXT(ftrobopy.ftrobopy):
    def __init__(self, mode):
        super().__init__(mode)

    def proximitySensor(self):
        class prox:
            def __init__(self, outer):
                self.apds = Apds(outer)

            def turnOn(self):
                self.apds.enable_proximity()

            def turnOff(self):
                self.apds.disable_proximity()

            def getDistance(self) -> int:
                self.apds.get_proximity()

        return prox(self)

    def lightSensor(self):
        class light:
            def __init__(self, outer):
                self.apds = Apds(outer)

            def turnOn(self):
                self.apds.enable_light()

            def turnOff(self):
                self.apds.disable_light()

            def getBrightness(self) -> int:
                try:
                    return self.apds.get_rgbc()[0]
                except TypeError:
                    return -1

        return light(self)

    def rgbSensor(self):
        class rgb:
            def __init__(self, outer):
                self.apds = Apds(outer)

            @staticmethod
            def turnOn(self):
                self.apds.enable_light()

            @staticmethod
            def turnOff(self):
                self.apds.disable_light()

            @staticmethod
            def getColor(self) -> color.Color:
                return color.Color(*self.apds.get_rgbc())

        return rgb(self)

    def gestureSensor(self):
        class ges:
            def __init__(self, outer):
                self.apds = Apds(outer)

            def turnOn(self):
                self.apds.enable_gesture()

            def turnOff(self):
                self.apds.disable_gesture()

            def getGesture(self) -> str:
                if self.apds.is_gesture_interrupt():
                    gesture = self.apds.get_gesture()
                else:
                    gesture = "NONE"
                return gesture

        return ges(self)
