import time


class Clock:
    _waiting = False
    _waited = 0
    _started = 0

    @classmethod
    def sleep(cls, secs: float):
        time.sleep(secs)

    @classmethod
    def wait(cls, secs: float):
        if cls._waiting:
            cls._waited = time.time() - cls._started
            if cls._waited >= secs:
                cls._waiting = False
                return False
        else:
            cls._waited = 0
            cls._started = time.time()
            cls._waiting = True
        return True
