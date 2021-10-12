import struct
from typing import Tuple, Union, ByteString

from . import ftrobopy
from .constants import *


class Apds:
    _TXT: ftrobopy.ftTXT

    @classmethod
    def _write(cls, register:int, data:int, debug=False)-> bool:
        if cls._TXT.i2c_write(ADR, register, data, debug):
            return True
        else:
            return False


    @classmethod
    def _read(cls, register:int, register_len:int = 1, data_len:int = 1, debug = False)-> Union[Tuple[int], ByteString]:
        buffer = cls._TXT.i2c_read(ADR, register, register_len, data_len, debug)
        if register_len == 1:
            return struct.unpack('<'+'B'*data_len, buffer)
        elif register_len == 2:
            return struct.unpack('<'+'H'*data_len, buffer)
        else:
            return buffer


    @classmethod
    def _set(cls, register:int, data:int, mask:int=0, enable:bool=True):
        if mask != 0:
            res = cls._read(register)
            val = (res&mask) | data
            return cls._write(register, val)
        elif enable:
            res = cls._read(register)
            val = res|data
            return cls._write(register, val)
        elif not enable:
            res = cls._read(register)
            val = res^data
            return cls._write(register, val)
        else:
            return False


    @classmethod
    def init(cls):
        if cls._read(ID) != ID_VALUE:
            return False
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