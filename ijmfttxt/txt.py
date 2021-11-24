from . import ftrobopy
from .apds import Apds
from . import color

class TXT(ftrobopy.ftrobopy):

    def __init__(self, mode):
        super().__init__(mode)
        Apds._TXT = self

    @staticmethod
    def proximitySensor():
        class _prox:
            @staticmethod
            def turnOn():
                Apds.enable_proximity()

            @staticmethod
            def turnOff():
                Apds.disable_proximity()

            @staticmethod
            def getDistance():
                Apds.get_proximity()
        return _prox

    @staticmethod
    def lightSensor():
        class _light:
            @staticmethod
            def turnOn():
                Apds.enable_light()

            @staticmethod
            def turnOff():
                Apds.disable_light()

            @staticmethod
            def getBrightness():
                try:
                    return Apds.get_rgbc()[0]
                except TypeError:
                    return -1
        return _light

    @staticmethod
    def rgbSensor():
        class _rgb:
            @staticmethod
            def turnOn():
                Apds.enable_light()

            @staticmethod
            def turnOff():
                Apds.disable_light()

            @staticmethod
            def getColor():
                return color.Color(*Apds.get_rgbc())
            
        return _rgb

    @staticmethod
    def gestureSensor():
        class _ges:
            @staticmethod
            def turnOn():
                Apds.enable_gesture()

            @staticmethod
            def turnOff():
                Apds.disable_gesture()

            @staticmethod
            def getGesture():
                if Apds.is_gesture_interrupt():
                    gesture = Apds.get_gesture()
                else:
                    gesture = "NONE"
                return gesture
        return _ges
