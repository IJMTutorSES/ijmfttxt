from . import ftrobopy
from .apds import Apds
from . import color

import time
import struct


def wait(sec: int):
    """halte das Programm für eine gewisse Zeit an

    Args:
        sec (int): Zeit die das Programm pausiert in Sekunden
    """
    time.sleep(sec)


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
            def getRed():
                try:
                    return Apds.get_rgbc()[1]
                except TypeError:
                    return -1

            @staticmethod
            def getGreen():
                try:
                    return Apds.get_rgbc()[2]
                except TypeError:
                    return -1

            @staticmethod
            def getBlue():
                try:
                    return Apds.get_rgbc()[3]
                except TypeError:
                    return -1

            @staticmethod
            def getRGB():
                try:
                    return Apds.get_rgbc()[1:]
                except TypeError:
                    return (-1, -1, -1)
            
            @staticmethod
            def getColor():
                values = Apds.get_rgbc()[1:]
                c_color = color.corrctedColor(*values)
                return color.guessColor(c_color)
            
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
