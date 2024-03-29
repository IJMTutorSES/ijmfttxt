import pynput
from typing import Union, List

from ijmfttxt.errors import type_checker, UserValueError, error_handler


class Keyboard:
    """Klasse für Keyboardlistener Funktionen"""

    @error_handler
    def __init__(self):
        self._keys = {}
        self._listener = pynput.keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release, suppress=True
        )
        self._listener.start()

    @error_handler
    def __del__(self):
        self.stop()

    @type_checker([str], {"count": int})
    @error_handler
    def isPressed(self, key: str, count: int = -1) -> bool:
        """Prüft ob gegebene taste oder gegebene Tastenkombination gedrückt ist

        Args:
            key (str): Tastenbezeichnungen auf englisch("space", "up", ..); mehrere Tasten werden mit einem '+' getrennt

        Returns:
            bool: True für derzeit gedrückt und False für derzeit nicht gedrückt
        """
        k = self._extract_keys(key)
        try:
            result = 0
            for n in k:
                if n in self._keys and self._keys[n] != -1:
                    if self._keys[n] <= count or count == -1:
                        result += 1
                    if self._keys[n] <= count:
                        self._keys[n] += 1
                else:
                    return False
            return result == len(k)
        except KeyError:
            return UserValueError

    @error_handler
    def keys_pressed(self) -> List[str]:
        """Gibt alle derzeit gedrückten Tasten

        Returns:
            Set[str]: Tastennamen in englisch und in Kleinbuchstaben
        """
        return [k for k in self._keys.keys() if self._keys[k] != -1]

    @error_handler
    def stop(self):
        """Stoppt den Listener"""
        self._listener.stop()

    @staticmethod
    def _convert_to_char(key: Union[str, pynput.keyboard.KeyCode]) -> str:
        try:
            return key.char
        except AttributeError:
            return str(key)[4:]

    @staticmethod
    def _extract_keys(keykombo: str) -> List[str]:
        return keykombo.replace(" ", "").split("+")

    @error_handler
    def _on_press(self, key):
        if not self._convert_to_char(key) in self._keys.keys():
            self._keys[self._convert_to_char(key)] = 1
        elif self._keys[self._convert_to_char(key)] == -1:
            self._keys[self._convert_to_char(key)] = 1

    @error_handler
    def _on_release(self, key):
        self._keys[self._convert_to_char(key)] = -1

    def _win32_event_filter(self, msg, data):
        return True


class Mouse:
    """Klasse für Mouselistener Funktionen"""

    @error_handler
    def __init__(self):
        self._buttons = {}
        self._listener = pynput.mouse.Listener(on_click=self._on_click)
        self._listener.start()

    @error_handler
    def __del__(self):
        self.stop()

    @error_handler
    def _on_click(self, *args):
        self._buttons[str(args[2])[7:]] = args[3]

    @type_checker([str])
    @error_handler
    def is_pressed(self, button: str) -> bool:
        """Prüft ob gegebene Mausttaste gedrückt ist

        Args:
            button (str): möglich "left" oder "right"

        Returns:
            bool: True für derzeit gedrückt und False für derzeit nicht gedrückt
        """
        try:
            return self._buttons[button]
        except KeyError:
            raise UserValueError

    @error_handler
    def stop(self):
        """Stoppt den Listener"""
        self._listener.stop()


def _test():
    print("Starting")
    keyboard = Keyboard()
    running = True
    while running:
        print("Testing")
        if keyboard.isPressed("e", count=10):
            print("Stopping")
            running = False
    keyboard.stop()


if __name__ == "__main__":
    _test()
