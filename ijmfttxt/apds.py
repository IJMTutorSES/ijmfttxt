import struct
import time

from typing import Tuple, Union, ByteString


from . import ftrobopy
from .constants import *


class Apds:
    _TXT: ftrobopy.ftTXT = None
    gesdata_up = [0 for _ in range(32)]
    gesdata_down = [0 for _ in range(32)]
    gesdata_left = [0 for _ in range(32)]
    gesdata_right = [0 for _ in range(32)]
    gesdata_index = 0
    gesdata_total = 0
    gesmotion = None
    ud_delta = 0
    lr_delta = 0
    ud_count = 0
    lr_count = 0
    near_count = 0
    far_count = 0
    state = 0
    THRESHOLD = 10
    SENS1 = 15
    SENS2 = 50

    @classmethod
    def _write(cls, register:int, data:int, debug=False)-> bool:
        if cls._TXT.i2c_write(ADR, register, data, debug):
            return True
        else:
            return False


    @classmethod
    def _read(cls, register:int, register_len:int = 1, data_len:int = 1, debug = False)-> Union[Tuple[int], ByteString]:
        buffer = cls._TXT.i2c_read(ADR, register, data_len=data_len, debug=debug)
        if register_len == 1:
            return struct.unpack('<'+'B'*data_len, buffer)
        elif register_len == 2:
            return struct.unpack('<'+'H'*(data_len//2), buffer)
        else:
            return buffer


    @classmethod
    def _set(cls, register:int, data:int, mask:int=0, enable:bool=True):
        if mask != 0:
            res = cls._read(register)[0]
            val = (res&mask) | data
            return cls._write(register, val)
        else:
            res = cls._read(register)[0]
            bit = res & data
            if bit != 0 and enable == False:
                val = res ^ data
            elif bit == 0 and enable == True:
                val = res | data
            else:
                return False 
            print(res, data, val)
            return cls._write(register, val)

    @classmethod
    def init(cls):
        if cls._read(ID)[0] != ID_VALUE:
            return False
        print("init")
        cls._write(ENABLE, OFF)
        cls._write(ATIME, ATIME_DEFAULT)
        cls._write(WTIME, WTIME_DEFAULT)
        cls._write(PPULSE, PPULSE_DEFAULT)
        cls._write(CONFIG1, CONFIG1_DEFAULT)
        cls._write(CONTROL, LDRIVE_DEFAULT|PGAIN_DEFAULT|AGAIN_DEFAULT)
        cls._write(PILT, PILT_DEFAULT)
        cls._write(PIHT, PIHT_DEFAULT)
        cls._write(AILTL, AILT_DEFAULT)
        cls._write(AIHTL, AIHT_DEFAULT)
        cls._write(PERS, PERS_DEFAULT)
        cls._write(CONFIG2, CONFIG2_DEFAULT)
        cls._write(CONFIG3, CONFIG3_DEFAULT)
        cls._write(GPENTH, GPENTH_DEFAULT)
        cls._write(GEXTH, GEXTH_DEFAULT)
        cls._write(GCONF1, GCONF1_DEFAULT)
        cls._write(GCONF2, GGAIN_DEFAULT|GLDRIVE_DEFAULT|GWTIME_DEFAULT)
        cls._write(GPULSE, GPULSE_DEFAULT)
        cls._write(GCONF3, GCONF3_DEFAULT)
        return True
    

    @classmethod
    def enable_proximity(cls, interrupt=False):
        cls._set(CONTROL, PGAIN_DEFAULT, mask=PGAIN_MASK)
        cls._set(CONTROL, LDRIVE_DEFAULT, mask=LDRIVE_MASK)
        cls._set(ENABLE, ENABLE_PIEN, enable=interrupt)
        cls._set(ENABLE, ENABLE_PON, enable=True)
        cls._set(ENABLE, ENABLE_PEN, enable=True)
    

    @classmethod
    def disable_proximity(cls, interrupt=False):
        if interrupt:
            cls._set(ENABLE, ENABLE_PIEN, False)
        cls._set(ENABLE, ENABLE_PEN, False)
    

    @classmethod
    def get_proximity(cls):
        return cls._read(PDATA)
    
    
    @classmethod
    def enable_light(cls, interrupt=False):
        cls._set(CONTROL, AGAIN_DEFAULT, mask=AGAIN_MASK)
        cls._set(ENABLE, ENABLE_AIEN, enable=interrupt)
        cls._set(ENABLE, ENABLE_PON, enable=True)
        cls._set(ENABLE, ENABLE_AEN, enable=True)


    @classmethod
    def disable_light(cls, interrupt=False):
        if interrupt:
            cls._set(ENABLE, ENABLE_AIEN, False)
        cls._set(ENABLE, ENABLE_AEN, False)
    

    @classmethod
    def get_rgbc(cls):
        return cls._read(CDATAL, register_len=2, data_len=8)


    @classmethod
    def enable_gesture(cls, interrupt=False):
        cls.reset_gesture_param()
        cls._write(WTIME, WTIME_RESET)
        cls._write(PPULSE, G_PPULSE_DEFAULT)
        cls._set(CONFIG2, LEDBOOST_200, mask=LEDBOOST_MASK)
        cls._set(GCONF4, GCONF4_GIEN, enable=interrupt)
        cls._set(GCONF4, GCONF4_GMODE, enable=True)
        cls._set(ENABLE, ENABLE_PON, enable=True)
        cls._set(ENABLE, ENABLE_WEN, enable=True)
        cls._set(ENABLE, ENABLE_PEN, enable=True)
        cls._set(ENABLE, ENABLE_GEN, enable=True)


    @classmethod
    def disable_gesture(cls, interrupt = False):
        cls.reset_gesture_param()
        if interrupt:
            cls._set(GCONF4, GCONF4_GIEN, enable=False)
        cls._set(GCONF4, GCONF4_GMODE, enable=False)
        cls._set(ENABLE, ENABLE_GEN, enable=False)


    @classmethod
    def is_gesture_available(cls):
        res = cls._read(GSTATUS)[0]
        val = res & GSTATUS_GVALID
        if val == 0:
            return False
        else:
            return True
    

    @classmethod
    def reset_gesture_param(cls):
        cls.gesdata_index = 0
        cls.gesdata_total = 0
        cls.ud_delta = 0
        cls.lr_delta = 0
        cls.ud_count = 0
        cls.lr_count = 0
        cls.near_count = 0
        cls.far_count = 0
        cls.state = 0
        cls.gesmotion = None

    @classmethod
    def get_gesture(cls):
        fifo_level = 0
        fifo_data = None
        motion = "None"

        if not cls.is_gesture_available() or cls._read(ENABLE)[0] & ENABLE_PON == 0:
            return False
        
        while True:
            time.sleep(0.03)
            gstatus = cls._read(GSTATUS)[0]
            if (gstatus & GSTATUS_GVALID) == GSTATUS_GVALID:
                fifo_level = cls._read(GFLVL)[0]
                print(f"{fifo_level=}")
                if fifo_level > 0:
                    fifo_data = cls._read(GFIFO, data_len=4*fifo_level)
                    bytes_read = len(fifo_data)
                    if bytes_read >= 4:
                        for i in range(0, bytes_read, 4):
                            cls.gesdata_up[cls.gesdata_index] = fifo_data[i+0]
                            cls.gesdata_down[cls.gesdata_index] = fifo_data[i+1]
                            cls.gesdata_left[cls.gesdata_index] = fifo_data[i+2]
                            cls.gesdata_right[cls.gesdata_index] = fifo_data[i+3]
                            cls.gesdata_index += 1
                            cls.gesdata_total += 1
                        if cls.process_data():
                            if cls.decode_gesture():
                                print(cls.gesmotion)
                        cls.gesdata_index = 0
                        cls.gesdata_total = 0
            else:
                time.sleep(0.03)
                cls.decode_gesture()
                motion = cls.gesmotion
                print(cls.gesmotion)
                cls.reset_gesture_param()
                return motion


    @classmethod
    def process_data(cls):
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
        if cls.gesdata_total <= 4:
            return False
        if cls.gesdata_total <= 32 and cls.gesdata_total > 0:
            for i in range(cls.gesdata_total):
                if cls.gesdata_up[i] > cls.THRESHOLD and cls.gesdata_down[i] > cls.THRESHOLD and cls.gesdata_left[i] > cls.THRESHOLD and cls.gesdata_right[i] > cls.THRESHOLD:
                    u_first = cls.gesdata_up[i]
                    d_first = cls.gesdata_down[i]
                    l_first = cls.gesdata_left[i]
                    r_first = cls.gesdata_right[i]
                    break
            if u_first == 0 or d_first == 0 or l_first == 0 or r_first == 0:
                return False 
            for i in range(cls.gesdata_total-1, 0, -1):
                if cls.gesdata_up[i] > cls.THRESHOLD and cls.gesdata_down[i] > cls.THRESHOLD and cls.gesdata_left[i] > cls.THRESHOLD and cls.gesdata_right[i] > cls.THRESHOLD:
                    u_last = cls.gesdata_up[i]
                    d_last = cls.gesdata_down[i]
                    l_last = cls.gesdata_left[i]
                    r_last = cls.gesdata_right[i]
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
        cls.ud_delta += ud_delta
        cls.lr_delta += lr_delta
        if cls.ud_delta >= cls.SENS1:
            cls.ud_count = 1
        elif cls.ud_delta <= -cls.SENS1:
            cls.ud_count = -1
        else:
            cls.ud_count = 0
        if cls.lr_delta >= cls.SENS1:
            cls.lr_count = 1
        elif cls.lr_delta <= -cls.SENS1:
            cls.lr_count = -1
        else:
            cls.lr_count = 0
        if cls.ud_count == 0 and cls.lr_count == 0:
            if abs(ud_delta) < cls.SENS2 and abs(lr_delta) < cls.SENS2:
                if ud_delta == 0 and lr_delta == 0:
                    cls.near_count += 1
                elif ud_delta != 0 or lr_delta != 0:
                    cls.far_count += 1
                if cls.near_count >= 10 and cls.far_count >= 2:
                    if ud_delta == 0 and lr_delta == 0:
                        cls.state = "near"
                    elif ud_delta != 0 and lr_delta != 0:
                        cls.state = "far"
                    return True
        else:
            if abs(ud_delta) < cls.SENS2 and abs(lr_delta) < cls.SENS2:
                if ud_delta == 0 and lr_delta == 0:
                    cls.near_count += 1
                if cls.near_count >= 10:
                    cls.ud_count = 0
                    cls.lr_count = 0
                    cls.ud_delta = 0
                    cls.lr_delta = 0
        return False
    

    @classmethod
    def decode_gesture(cls):
        if cls.state == "near":
            cls.gesmotion = "NEAR"
            return True
        elif cls.state == "far":
            cls.gesmotion = "FAR"
            return True
        print(f"{cls.ud_count=}; {cls.lr_count=}")
        if cls.ud_count == -1 and cls.lr_count == 0:
            cls.gesmotion = "UP"
        elif cls.ud_count == 1 and cls.lr_count == 0:
            cls.gesmotion = "DOWN"
        elif cls.ud_count == 0 and cls.lr_count == 1:
            cls.gesmotion == "RIGHT"
        elif cls.ud_count == 0 and cls.lr_count == -1:
            cls.gesmotion == "LEFT"
        elif cls.ud_count == -1 and cls.lr_count == 1:
            if abs(cls.ud_delta) > abs(cls.lr_delta):
                cls.gesmotion = "UP"
            else:
                cls.gesmotion = "RIGHT"
        elif cls.ud_count == 1 and cls.lr_count == -1:
            if abs(cls.ud_delta) > abs(cls.lr_delta):
                cls.gesmotion = "DOWN"
            else:
                cls.gesmotion = "LEFT"
        elif cls.ud_count == -1 and cls.lr_count == -1:
            if abs(cls.ud_delta) > abs(cls.lr_delta):
                cls.gesmotion = "UP"
            else:
                cls.gesmotion = "LEFT"
        elif cls.ud_count == 1 and cls.lr_count == 1:
            if abs(cls.ud_delta) > abs(cls.lr_delta):
                cls.gesmotion = "DOWN"
            else:
                cls.gesmotion = "RIGHT"
        else:
            return False
        return True       
