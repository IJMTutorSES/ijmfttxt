from . import ftrobopy

import time
import struct

def wait(sec: int):
    """halte das Programm für eine gewisse Zeit an

    Args:
        sec (int): Zeit die das Programm pausiert in Sekunden
    """    
    time.sleep(sec)

class TXT(ftrobopy.ftrobopy):

    def __init__(self, mode):    
        super().__init__(mode)
        self.ADR = 0x39
        self.R_ENABLE = 0x80
        self.R_STATUS = 0x93
        self.R_ID = 0x92
        self.POWER = 0b00000001
        self.R_CONFIG1 = 0x8F
    
    def proximity_sensor(self):
        """Gibt ein Verweis zur Klasse mit der der Abstandsesnor gestuert werden kann zurück"""        
        class _prox:
            _outer: TXT
            R_PDATA = 0x9c
            POWER = 0b00000100

            @classmethod
            def turn_on(cls):
                """Schaltet den Abstandsensor an"""              
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, cls.POWER & cls._outer.POWER) #Enable Proximity Engine
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_CONFIG1, 0x0C) #Set GAIN o x8

            @classmethod
            def turn_off(cls):
                """Schaltet den Abstandssensor aus"""
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, cls._outer.POWER)

            @classmethod
            def get_distance(cls) -> int:
                """Gib den gemessenen Abstand zurück

                Returns:
                    int: Wert zwischen 0-255
                """                
                res = cls._outer.i2c_read(cls._outer.ADR,cls.R_PDATA, data_len=1)
                value = struct.unpack('<B', res)
                return value[0]
        
        _prox._outer = self
        return _prox
    
    def light_sensor(self):
        """Gibt ein Verweis zur Klasse mit dem der Lichtsensor gesteuertert werden kann zurück"""
        class _light:
            _outer: TXT
            R_CDATAL = 0x94
            POWER = 0b00000010
            R_ATIME = 0x81

            @classmethod
            def turn_on(cls):
                """Schaltet den Lichtsensor aus"""
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, cls.POWER & cls._outer.POWER) #Enable ASL Engine
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_CONFIG1, 0x01) #Set GAIN to x4
                cls._outer.i2c_write(cls._outer.ADR, cls.R_ATIME, 0xB6) #Set ADC Integration time to 182 (Cycles: 72, Time: 200ms)
            
            @classmethod
            def turn_off(cls):
                """Schaltet den Lichtsensor an"""
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, cls._outer.POWER)
            
            @classmethod
            def get_brightness(cls) -> int:
                """Gibt den gemessenen elligkeisswer zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_CDATAL, data_len=2)
                val = struct.unpack('<H', res)
                return val

        _light._outer = self
        return _light
    
    def rgb_sensor(self):
        """Gibt ein Verweis zur Klasse mit der der Farbsensor gestuert werden kann zurück"""
        class _rgb:
            _outer: TXT
            R_RDATAL = 0x96
            R_GDATAL = 0x98
            R_BDATAL = 0x9A
            POWER = 0b00000010
            R_ATIME = 0x81

            @classmethod
            def turn_on(cls):
                """Schaltet den Farbsensor an"""
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, cls.POWER & cls._outer.POWER) #Enable ASL Engine
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_CONFIG1, 0x01) #Set GAIN to x4
                cls._outer.i2c_write(cls._outer.ADR, cls.R_ATIME, 0xB6) #Set ADC Integration time to 182 (Cycles: 72, Time:200ms)
            
            @classmethod
            def turn_off(cls):
                """Schaltet den Farbsensor aus"""
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, cls._outer.POWER)
            
            @classmethod
            def get_red(cls) -> int:
                """Gibt den gemessenen Rotwert zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_RDATAL, data_len=2)
                val = struct.unpack('<H', res)
                return val
            
            @classmethod
            def get_green(cls) -> int:
                """Gibt den gemessenen Grünwert zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_GDATAL, data_len=2)
                val = struct.unpack('<H', res)
                return val
            
            @classmethod
            def get_blue(cls) -> int:
                """Gibt den gemmessenen Blauwert zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_BDATAL, data_len=2)
                val = struct.unpack('<H', res)
                return val
            
        _rgb._outer = self
        return _rgb

    def gesture_sensor(self):
        class _gesture:
            _outer: TXT
            R_GCON4 = 0xAB


            @classmethod
            def turn_on(cls):
                pass

            @classmethod
            def turn_off(cls):
                pass
            
            @classmethod
            def get_gesture(cls) -> int:
                pass
