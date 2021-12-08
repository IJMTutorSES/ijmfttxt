from time import sleep

from . import ftrobopy
from .apds import Apds
from . import color


class TXT(ftrobopy.ftrobopy):
    """Klassen-Wrapper für ftrobopy Klasse von ftrobopy mit zusätzlicher Unterstützung des Fischertechnik RGB Gesture Sensors"""

    def __init__(self):
        super().__init__("auto")

    def sleep(self, secs: float):
        """Pausiert das Programm für gegebene Zeit

        Args:
            secs (float): Zeit in Sekunden
        """
        sleep(secs)

    def proximitySensor(self):
        """Erzeugt neuen Abstandsensor

        Returns:
            prox: Objekt durch das mit dem Abstandsensor kommuniziert werden kann
        """

        class prox:
            """Klassenwrapper für Abstandssensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_proximity()

            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_proximity()

            def getDistance(self) -> int:
                """Gibt den gemessen Abstand zurück

                Returns:
                    int: Zahl zwischen 0 und 255
                """
                return self.apds.get_proximity()

        return prox(self)

    def lightSensor(self):
        """Erzeugt neuen Lichtsensor

        Returns:
            light: Objekt durch das mit dem Lichtsensor kommuniziert werden kann
        """

        class light:
            """Klassenwrapper für Lichtsensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_light()

            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_light()

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

    def colorSensor(self):
        """Erzeugt neuen Farbsensor

        Returns:
            col: Objekt durch das mit dem Farbsensor kommuniziert werden kann
        """

        class col:
            """Klassenwrapper für Farbsensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            @staticmethod
            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_light()

            @staticmethod
            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_light()

            @staticmethod
            def getColor(self) -> color.Color:
                """Gibt gemessene Farbwerte zurück

                Returns:
                    color.Color: Objekt in dem sämtliche Farbwerte gespeichet sind
                """
                return color.Color(*self.apds.get_rgbc())

        return col(self)

    def gestureSensor(self):
        """Erzeugt neuen Gestensensor

        Returns:
            ges: Objekt durch das mit dem Gestensensor kommuniziert werden kann
        """

        class ges:
            """Klassenwrapper für Gestensensor-Funktionalitäten der Apds Klasse"""

            def __init__(self, outer):
                self.apds = Apds(outer)

            def turnOn(self):
                """Schaltet den Sensor an"""
                self.apds.enable_gesture()

            def turnOff(self):
                """Schaltet den Sensor aus"""
                self.apds.disable_gesture()

            def getGesture(self) -> str:
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
