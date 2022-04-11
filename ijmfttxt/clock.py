import time
from typing import Union, overload

from .errors import error_handler, type_checker


class Clock:
    _waiting = False
    _waited = 0
    _started = 0

    @overload
    @classmethod
    def sleep(cls, secs: str):
        ...

    @overload
    @classmethod
    def sleep(cls, secs: float):
        ...

    @overload
    @classmethod
    def sleep(cls, secs: int):
        ...

    @classmethod
    @type_checker(["NUMBER"])
    @error_handler
    def sleep(cls, secs: Union[str, float, int]):
        time.sleep(float(secs))

    @overload
    @classmethod
    def wait(cls, secs: str) -> bool:
        ...

    @overload
    @classmethod
    def wait(cls, secs: float) -> bool:
        ...

    @overload
    @classmethod
    def wait(cls, secs: int) -> bool:
        ...

    @classmethod
    @type_checker(["NUMBER"])
    @error_handler
    def wait(cls, secs: Union[str, float, int]) -> bool:
        if cls._waiting:
            cls._waited = time.time() - cls._started
            if cls._waited >= float(secs):
                cls._waiting = False
                return False
        else:
            cls._waited = 0
            cls._started = time.time()
            cls._waiting = True
        return True
