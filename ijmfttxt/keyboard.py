import pynput
from typing import Set, Union

class Keyboard:
    def __init__(self):
        self._keys = {}
        self._listener = pynput.keyboard.Listener(on_press = self._on_press, on_release=self._on_release)
        self._listener.start()
    
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
        k = key.replace(" ", "").split("+")
        try:
            return all(map(lambda n: self._keys[n], k))
        except KeyError:
            return False

    def keys_pressed(self) -> Set[str]:
        return self._keys.keys()

    def stop(self):
        self._listener.stop()

class Mouse:
    def __init__(self):
        self._buttons = {}
        self._listener = pynput.mouse.Listener(on_click = self._on_click)
        self._listener.start()
    
    def _on_click(self, *args):
        self._buttons[str(args[2])[7:]] = args[3]

    def is_pressed(self, button):
        try:
            return self._buttons[button]
        except KeyError:
            return False

    def stop(self):
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