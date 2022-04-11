from typing import Union

from . import ftrobopy
from .apds import Apds
from . import color

from .errors import error_handler


class TXT(ftrobopy.ftrobopy):
    """Klassen-Wrapper für ftrobopy Klasse von ftrobopy mit zusätzlicher Unterstützung des Fischertechnik RGB Gesture Sensors"""

    @error_handler
    def __init__(self):
        super().__init__("auto")

    @error_handler
    def proximitySensor(self):
        """Erzeugt neuen Abstandsensor

        Returns:
            prox: Objekt durch das mit dem Abstandsensor kommuniziert werden kann
        """

        class prox:
            """Klassenwrapper für Abstandssensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            @error_handler
            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_proximity()

            @error_handler
            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_proximity()

            @error_handler
            def getDistance(self) -> int:
                """Gibt den gemessen Abstand zurück

                Returns:
                    int: Zahl zwischen 0 und 255
                """
                return self.apds.get_proximity()

        return prox(self)

    @error_handler
    def lightSensor(self):
        """Erzeugt neuen Lichtsensor

        Returns:
            light: Objekt durch das mit dem Lichtsensor kommuniziert werden kann
        """

        class light:
            """Klassenwrapper für Lichtsensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            @error_handler
            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_light()

            @error_handler
            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_light()

            @error_handler
            def getBrightness(self) -> int:
                """Gibt gemessene Helligkeit zurück

                Returns:
                    int: Zahl zwischen 0 und 65536
                """
                try:
                    return self.apds.get_rgbc()[0]
                except TypeError:
                    return -1

        return light(self)

    @error_handler
    def colorSensor(self):
        """Erzeugt neuen Farbsensor

        Returns:
            col: Objekt durch das mit dem Farbsensor kommuniziert werden kann
        """

        class col:
            """Klassenwrapper für Farbsensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            @error_handler
            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_light()

            @error_handler
            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_light()

            @error_handler
            def getColor(self) -> color.Color:
                """Gibt gemessene Farbwerte zurück

                Returns:
                    color.Color: Objekt in dem sämtliche Farbwerte gespeichet sind
                """
                return color.Color(*self.apds.get_rgbc())

        return col(self)

    @error_handler
    def gestureSensor(self):
        """Erzeugt neuen Gestensensor

        Returns:
            ges: Objekt durch das mit dem Gestensensor kommuniziert werden kann
        """

        class ges:
            """Klassenwrapper für Gestensensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            @error_handler
            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_gesture()

            @error_handler
            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_gesture()

            @error_handler
            def getGesture(self) -> Union[str, bool]:
                """Gibt erkannte Geste zurück

                Returns:
                    str: mögliche Gesten sind ["NONE", "UP", "DOWN", "LEFT", "RIGHT"]
                """
                if self.apds.is_gesture_interrupt():
                    gesture = self.apds.get_gesture()
                else:
                    gesture = "NONE"
                return gesture

        return ges(self)
