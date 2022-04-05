import struct
import time
from typing import List, Union

from . import ftrobopy
from .constants import *


class Apds:
    _singelton: "Apds"

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_singelton"):
            cls._singelton = super().__new__(cls)
        return cls._singelton

    def __init__(self, outer):
        self._TXT: ftrobopy.ftTXT = outer
        self.gesdata_up = [0 for _ in range(32)]
        self.gesdata_down = [0 for _ in range(32)]
        self.gesdata_left = [0 for _ in range(32)]
        self.gesdata_right = [0 for _ in range(32)]
        self.gesdata_index = 0
        self.gesdata_total = 0
        self.gesmotion = "None"
        self.ud_delta = 0
        self.lr_delta = 0
        self.ud_count = 0
        self.lr_count = 0
        self.near_count = 0
        self.far_count = 0
        self.state = 0
        self.THRESHOLD = 10
        self.SENS1 = 15
        self.SENS2 = 50

        self.reset()

    def reset(self) -> bool:
        if self._read(ID)[0] != ID_VALUE:
            return False
        self._write(ENABLE, OFF)
        self._write(ATIME, ATIME_DEFAULT)
        self._write(WTIME, WTIME_DEFAULT)
        self._write(PPULSE, PPULSE_DEFAULT)
        self._write(CONFIG1, CONFIG1_DEFAULT)
        self._write(CONTROL, LDRIVE_DEFAULT | PGAIN_DEFAULT | AGAIN_DEFAULT)
        self._write(PILT, PILT_DEFAULT)
        self._write(PIHT, PIHT_DEFAULT)
        self._write(AILTL, AILT_DEFAULT)
        self._write(AIHTL, AIHT_DEFAULT)
        self._write(PERS, PERS_DEFAULT)
        self._write(CONFIG2, CONFIG2_DEFAULT)
        self._write(CONFIG3, CONFIG3_DEFAULT)
        self._write(GPENTH, GPENTH_DEFAULT)
        self._write(GEXTH, GEXTH_DEFAULT)
        self._write(GCONF1, GCONF1_DEFAULT)
        self._write(GCONF2, GGAIN_DEFAULT | GLDRIVE_DEFAULT | GWTIME_DEFAULT)
        self._write(GPULSE, GPULSE_DEFAULT)
        self._write(GCONF3, GCONF3_DEFAULT)
        return True

    def __del__(self):
        self.disable_gesture()
        self.disable_light()
        self.disable_proximity()

    def _set(self, register: int, data: int, mask: int = 0, enable: bool = True):
        if mask != 0:
            res = self._read(register)[0]
            val = (res & mask) | data
            return self._write(register, val)
        else:
            res = self._read(register)[0]
            bit = res & data
            if bit != 0 and enable == False:
                val = res ^ data
            elif bit == 0 and enable == True:
                val = res | data
            else:
                return False
            return self._write(register, val)

    def enable_proximity(self):
        self._set(CONTROL, PGAIN_DEFAULT, mask=PGAIN_MASK)
        self._set(CONTROL, LDRIVE_DEFAULT, mask=LDRIVE_MASK)
        self._set(ENABLE, ENABLE_PON, enable=True)
        self._set(ENABLE, ENABLE_PEN, enable=True)

    def disable_proximity(self):
        self._set(ENABLE, ENABLE_PEN, False)

    def get_proximity(self) -> int:
        return self._read(PDATA)[0]

    def enable_light(self):
        self._set(CONTROL, AGAIN_DEFAULT, mask=AGAIN_MASK)
        self._set(ENABLE, ENABLE_PON, enable=True)
        self._set(ENABLE, ENABLE_AEN, enable=True)

    def disable_light(self):
        self._set(ENABLE, ENABLE_AEN, False)

    def get_rgbc(self) -> List[int]:
        return self._read(CDATAL, register_len=2, data_len=8)

    def enable_gesture(self):
        self.reset_gesture_param()
        self._write(WTIME, WTIME_RESET)
        self._write(PPULSE, G_PPULSE_DEFAULT)
        self._set(CONFIG2, LEDBOOST_200, mask=LEDBOOST_MASK)
        self._set(GCONF4, GCONF4_GIEN, True)
        self._set(GCONF4, GCONF4_GMODE, enable=True)
        self._set(ENABLE, ENABLE_PON, enable=True)
        self._set(ENABLE, ENABLE_WEN, enable=True)
        self._set(ENABLE, ENABLE_PEN, enable=True)
        self._set(ENABLE, ENABLE_GEN, enable=True)

    def disable_gesture(self):
        self.reset_gesture_param()
        self._set(GCONF4, GCONF4_GIEN, enable=False)
        self._set(GCONF4, GCONF4_GMODE, enable=False)
        self._set(ENABLE, ENABLE_GEN, enable=False)

    def is_gesture_available(self) -> bool:
        res = self._read(GSTATUS)[0]
        val = res & GSTATUS_GVALID
        if val == 0:
            return False
        else:
            return True

    def is_gesture_interrupt(self) -> bool:
        res = self._read(STATUS)[0]
        val = res & STATUS_GINT
        if val == 0:
            return False
        else:
            return True

    def reset_gesture_param(self):
        self.gesdata_index = 0
        self.gesdata_total = 0
        self.ud_delta = 0
        self.lr_delta = 0
        self.ud_count = 0
        self.lr_count = 0
        self.near_count = 0
        self.far_count = 0
        self.state = 0
        self.gesmotion = "None"

    def get_gesture(self) -> Union[bool, str]:
        fifo_level = 0
        fifo_data = None
        motion = "None"

        if not self.is_gesture_available() or self._read(ENABLE)[0] & ENABLE_PON == 0:
            return False

        while True:
            time.sleep(0.03)
            gstatus = self._read(GSTATUS)[0]
            if (gstatus & GSTATUS_GVALID) == GSTATUS_GVALID:
                fifo_level = self._read(GFLVL)[0]
                if fifo_level > 0:
                    fifo_data = self._read(GFIFO, data_len=4 * fifo_level)
                    bytes_read = len(fifo_data)
                    if bytes_read >= 4:
                        for i in range(0, bytes_read, 4):
                            self.gesdata_up[self.gesdata_index] = fifo_data[i + 0]
                            self.gesdata_down[self.gesdata_index] = fifo_data[i + 1]
                            self.gesdata_left[self.gesdata_index] = fifo_data[i + 2]
                            self.gesdata_right[self.gesdata_index] = fifo_data[i + 3]
                            self.gesdata_index += 1
                            self.gesdata_total += 1
                        if self.process_data():
                            self.decode_gesture()
                        self.gesdata_index = 0
                        self.gesdata_total = 0
            else:
                time.sleep(0.03)
                self.decode_gesture()
                motion = self.gesmotion
                self.reset_gesture_param()
                return motion

    def process_data(self) -> bool:
        u_first = 0
        d_first = 0
        l_first = 0
        r_first = 0
        u_last = 0
        d_last = 0
        l_last = 0
        r_last = 0
        ud_ratio_first = 0
        lr_ratio_first = 0
        ud_ratio_last = 0
        lr_ratio_last = 0
        ud_delta = 0
        lr_delta = 0
        if self.gesdata_total <= 4:
            return False
        if self.gesdata_total <= 32 and self.gesdata_total > 0:
            for i in range(self.gesdata_total):
                if (
                    self.gesdata_up[i] > self.THRESHOLD
                    and self.gesdata_down[i] > self.THRESHOLD
                    and self.gesdata_left[i] > self.THRESHOLD
                    and self.gesdata_right[i] > self.THRESHOLD
                ):
                    u_first = self.gesdata_up[i]
                    d_first = self.gesdata_down[i]
                    l_first = self.gesdata_left[i]
                    r_first = self.gesdata_right[i]
                    break
            if u_first == 0 or d_first == 0 or l_first == 0 or r_first == 0:
                return False
            for i in range(self.gesdata_total - 1, 0, -1):
                if (
                    self.gesdata_up[i] > self.THRESHOLD
                    and self.gesdata_down[i] > self.THRESHOLD
                    and self.gesdata_left[i] > self.THRESHOLD
                    and self.gesdata_right[i] > self.THRESHOLD
                ):
                    u_last = self.gesdata_up[i]
                    d_last = self.gesdata_down[i]
                    l_last = self.gesdata_left[i]
                    r_last = self.gesdata_right[i]
                    break
        try:
            ud_ratio_first = ((u_first - d_first) * 100) / (u_first + d_first)
            lr_ratio_first = ((l_first - r_first) * 100) / (l_first + r_first)
            ud_ratio_last = ((u_last - d_last) * 100) / (u_last + d_last)
            lr_ratio_last = ((l_last - r_last) * 100) / (l_last + r_last)
        except ZeroDivisionError:
            return False
        ud_delta = ud_ratio_last - ud_ratio_first
        lr_delta = lr_ratio_last - lr_ratio_first
        self.ud_delta += ud_delta
        self.lr_delta += lr_delta
        if self.ud_delta >= self.SENS1:
            self.ud_count = 1
        elif self.ud_delta <= -self.SENS1:
            self.ud_count = -1
        else:
            self.ud_count = 0
        if self.lr_delta >= self.SENS1:
            self.lr_count = 1
        elif self.lr_delta <= -self.SENS1:
            self.lr_count = -1
        else:
            self.lr_count = 0
        if self.ud_count == 0 and self.lr_count == 0:
            if abs(ud_delta) < self.SENS2 and abs(lr_delta) < self.SENS2:
                if ud_delta == 0 and lr_delta == 0:
                    self.near_count += 1
                elif ud_delta != 0 or lr_delta != 0:
                    self.far_count += 1
                if self.near_count >= 10 and self.far_count >= 2:
                    if ud_delta == 0 and lr_delta == 0:
                        self.state = "near"
                    elif ud_delta != 0 and lr_delta != 0:
                        self.state = "far"
                    return True
        else:
            if abs(ud_delta) < self.SENS2 and abs(lr_delta) < self.SENS2:
                if ud_delta == 0 and lr_delta == 0:
                    self.near_count += 1
                if self.near_count >= 10:
                    self.ud_count = 0
                    self.lr_count = 0
                    self.ud_delta = 0
                    self.lr_delta = 0
        return False

    def decode_gesture(self) -> bool:
        if self.state == "near":
            self.gesmotion = "NEAR"
            return True
        elif self.state == "far":
            self.gesmotion = "FAR"
            return True
        print(f"{self.ud_count=}; {self.lr_count=}")
        if self.ud_count == -1 and self.lr_count == 0:
            self.gesmotion = "UP"
        elif self.ud_count == 1 and self.lr_count == 0:
            self.gesmotion = "DOWN"
        elif self.ud_count == 0 and self.lr_count == 1:
            self.gesmotion == "RIGHT"
        elif self.ud_count == 0 and self.lr_count == -1:
            self.gesmotion == "LEFT"
        elif self.ud_count == -1 and self.lr_count == 1:
            if abs(self.ud_delta) > abs(self.lr_delta):
                self.gesmotion = "UP"
            else:
                self.gesmotion = "RIGHT"
        elif self.ud_count == 1 and self.lr_count == -1:
            if abs(self.ud_delta) > abs(self.lr_delta):
                self.gesmotion = "DOWN"
            else:
                self.gesmotion = "LEFT"
        elif self.ud_count == -1 and self.lr_count == -1:
            if abs(self.ud_delta) > abs(self.lr_delta):
                self.gesmotion = "UP"
            else:
                self.gesmotion = "LEFT"
        elif self.ud_count == 1 and self.lr_count == 1:
            if abs(self.ud_delta) > abs(self.lr_delta):
                self.gesmotion = "DOWN"
            else:
                self.gesmotion = "RIGHT"
        else:
            return False
        return True

    def _write(self, register: int, data: int, debug=False) -> bool:
        if self._TXT.i2c_write(ADR, register, data, debug):
            return True
        else:
            return False

    def _read(
        self, register: int, register_len: int = 1, data_len: int = 1, debug=False
    ) -> List[int]:
        buffer = self._TXT.i2c_read(ADR, register, data_len=data_len, debug=debug)
        if register_len == 1:
            return list(struct.unpack("<" + "B" * data_len, buffer))
        elif register_len == 2:
            return list(struct.unpack("<" + "H" * (data_len // 2), buffer))
        return [0] * (data_len // 2)



