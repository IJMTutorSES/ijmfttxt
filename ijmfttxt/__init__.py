from .txt import TXT
from .keyboard import Keyboard, Mouse
from .clock import Clock

__version__ = "1.9.6"
print(f"using ijmfttxt {__version__}")

sleep = Clock.sleep
wait = Clock.wait
