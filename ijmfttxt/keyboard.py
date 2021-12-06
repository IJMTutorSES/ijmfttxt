import pynput
from typing import Set, Union


class Keyboard:
    """Klasse für Keyboardlistener Funktionen"""

    def __init__(self):
        self._keys = {}
        self._listener = pynput.keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.start()

    def __del__(self):
        self.stop()

    @staticmethod
    def _convert_to_char(key: Union[str, pynput.keyboard.KeyCode]) -> str:
        try:
            return key.char
        except AttributeError:
            return str(key)[4:]

    def _on_press(self, key: str):
        self._keys[self._convert_to_char(key)] = True

    def _on_release(self, key: str):
        self._keys[self._convert_to_char(key)] = False

    def is_pressed(self, key: str) -> bool:
        """Prüft ob gegebene taste oder gegebene Tastenkombination gedrückt ist

        Args:
            key (str): Tastenbezeichnungen auf englisch("space", "up", ..); mehrere Tasten werden mit einem '+' getrennt

        Returns:
            bool: True für derzeit gedrückt und False für derzeit nicht gedrückt
        """
        k = key.replace(" ", "").split("+")
        try:
            return all(map(lambda n: self._keys[n], k))
        except KeyError:
            return False

    def keys_pressed(self) -> Set[str]:
        """Gibt alle derzeit gedrückten Tasten

        Returns:
            Set[str]: Tastennamen in englisch und in Kleinbuchstaben
        """
        return self._keys.keys()

    def stop(self):
        """Stoppt den Listener"""
        self._listener.stop()


class Mouse:
    """Klasse für Mouselistener Funktionen"""

    def __init__(self):
        self._buttons = {}
        self._listener = pynput.mouse.Listener(on_click=self._on_click)
        self._listener.start()

    def __del__(self):
        self.stop()

    def _on_click(self, *args):
        self._buttons[str(args[2])[7:]] = args[3]

    def is_pressed(self, button: str) -> bool:
        """Prüft ob gegebene Mausttaste gedrückt ist

        Args:
            button (str): möglich "left" oder "right"

        Returns:
            bool: True für derzei gedrückt und False für derzeit nicht gedrückt
        """
        try:
            return self._buttons[button]
        except KeyError:
            return False

    def stop(self):
        """Stoppt den Listener"""
        self._listener.stop()


def _test():
    keyboard = Keyboard()
    mouse = Mouse()
    running = True
    while running:
        if keyboard.is_pressed("e"):
            running = False
        elif keyboard.is_pressed("a"):
            print("Hello World!")
        if mouse.is_pressed("right"):
            print("Hello Peter")
    keyboard.stop()
    mouse.stop()


if __name__ == "__main__":
    _test()
