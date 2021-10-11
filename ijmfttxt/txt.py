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
    
    def proximity_sensor(self):
        """Gibt ein Verweis zur Klasse mit der der Abstandsesnor gestuert werden kann zurück"""        
        class _prox:
            _outer: TXT
            R_PDATA = 0x9c
            POWER = 0b00000100

            @classmethod
            def turn_on(cls):
                """Schaltet den Abstandsensor an"""              
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, 0x05)
                cls._outer.i2c_write(cls._outer.ADR, 0x8F, 0x0C)

            @classmethod
            def turn_off(cls):
                """Schaltet den Abstandssensor aus"""
                data = struct.unpack('<h', cls._outer.i2c_read(cls._outer.ADR, cls._outer.R_ENABLE, data_len=2))[0] ^ bytes(cls.POWER)
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, data)

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
            R_CDATAH = 0x95
            POWER = 0b00000010

            @classmethod
            def turn_on(cls):
                """Schaltet den Lichtsensor aus"""
                #data = cls._outer.i2c_read(cls._outer.ADR, cls._outer.R_ENABLE, data_len=2) | (cls._outer.POWER & cls.POWER)
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, 0x03)
            
            @classmethod
            def turn_off(cls):
                """Schaltet den Lichtsensor an"""
                data = cls._outer.i2c_read(cls._outer.ADR, cls._outer.R_ENABLE, data_len=2) ^ cls.POWER
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, data)
            
            @classmethod
            def get_brightness(cls) -> int:
                """Gibt den gemessenen elligkeisswer zurück

                Returns:
                    int: Wert zwischen 0-65535
                """
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_CDATAL, data_len=2)#lo
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

            @classmethod
            def turn_on(cls):
                """Schaltet den Farbsensor an"""
                #data = cls._outer.i2c_read(cls._outer.ADR, cls._outer.R_ENABLE, data_len=2) | (cls._outer.POWER & cls.POWER)
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, 0x03)
                cls._outer.i2c_write(cls._outer.ADR, 0x81, 0xB6)
                cls._outer.i2c_write(cls._outer.ADR, 0x8F, 0x01)
            
            @classmethod
            def turn_off(cls):
                """Schaltet den Farbsensor aus"""
                data = cls._outer.i2c_read(cls._outer.ADR, cls._outer.R_ENABLE, data_len=2) ^ cls.POWER
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, data)
            
            @classmethod
            def get_red(cls) -> int:
                """Gibt den gemessenen Rotwert zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_RDATAL, data_len = 2) #lowbyte
                val = struct.unpack('<H', res)
                return val
            
            @classmethod
            def get_green(cls) -> int:
                """Gibt den gemessenen Grünwert zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_GDATAL, data_len = 2) #lowbyte
                val = struct.unpack('<H', res)
                return val
            
            @classmethod
            def get_blue(cls) -> int:
                """Gibt den gemmessenen Baluwert zurück

                Returns:
                    int: Wert zwischen 0-65535
                """                
                res = cls._outer.i2c_read(cls._outer.ADR, cls.R_BDATAL, data_len = 2) #lowbyte
                val = struct.unpack('<H', res)
                return val
            
        _rgb._outer = self
        return _rgb

    def gesture_sensor(self):
        class _gesture:
            _outer: TXT
            R_GCON1 = 0xA2
            R_GCON2 = 0xA3
            R_GCON3 = 0xAA
            R_GCON4 = 0xAB
            R_GFLVL = 0xAE
            R_FIFO = 0xFC
            R_GPENTH = 0xA0
            POWER = 0x44
            
            gesture_data = {
                "up": [0 for _ in range(32)],
                "down": [0 for _ in range(32)],
                "right": [0 for _ in range(32)],
                "left": [0 for _ in range(32)]
            }
            gesture_motion = "None"
            index = 0
            total_gestures = 0
            ud_delta = 0
            lr_delta = 0
            ud_count = 0
            lr_count = 0
            near_count = 0
            far_count = 0
            state = 0
            
            SENS1 = 50
            SENS2 = 20
            
            THRESHOLD = 10
            
            @classmethod
            def turn_on(cls):
                cls._outer.i2c_write(cls._outer.ADR, cls.R_GCON1, 0x40)
                cls._outer.i2c_write(cls._outer.ADR, cls.R_GCON2, 0x67)
                cls._outer.i2c_write(cls._outer.ADR, cls.R_GCON3, 0x00)
                cls._outer.i2c_write(cls._outer.ADR, cls.R_GCON4, 0x03)
                cls._outer.i2c_write(cls._outer.ADR, cls.R_GPENTH, 0x32)
                cls._outer.i2c_write(cls._outer.ADR, 0x90, 0x01)
                cls._outer.i2c_write(cls._outer.ADR, 0xA1, 0x00)
                cls._outer.i2c_write(cls._outer.ADR, 0x83, 0x00) 
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, 0x4D)

            @classmethod
            def turn_off(cls):
                cls._outer.i2c_write(cls._outer.ADR, cls._outer.R_ENABLE, 0x00)
            
            @classmethod
            def reset(cls):
                cls.index = 0
                cls.total_gestures = 0
                cls.ud_delta = 0
                cls.lr_delta = 0
                cls.ud_count = 0
                cls.lr_count = 0
                cls.near_count = 0
                cls.far_count = 0
                cls.state = 0
                cls.gesture_motion = -1
            
            @classmethod
            def _processData(cls):
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
                if cls.total_gestures <= 4:
                    return False
                if cls.total_gestures <= 32 and cls.total_gestures > 0:
                    for i in range(cls.total_gestures):
                        if cls.gesture_data["up"][i] > cls.THRESHOLD and cls.gesture_data["down"][i] > cls.THRESHOLD and cls.gesture_data["left"][i] > cls.THRESHOLD and cls.gesture_data["right"][i] > cls.THRESHOLD:
                            u_first = cls.gesture_data["up"][i]
                            d_first = cls.gesture_data["down"][i]
                            l_first = cls.gesture_data["left"][i]
                            r_first = cls.gesture_data["right"][i]
                            break
                    if u_first == 0 or d_first == 0 or l_first == 0 or r_first == 0:
                        return False
                    for i in range(cls.total_gestures-1, 0, -1):
                        if cls.gesture_data["up"][i] > cls.THRESHOLD and cls.gesture_data["down"][i] > cls.THRESHOLD and cls.gesture_data["left"][i] > cls.THRESHOLD and cls.gesture_data["right"][i] > cls.THRESHOLD:
                            u_last = cls.gesture_data["up"][i]
                            d_last = cls.gesture_data["down"][i]
                            l_last = cls.gesture_data["left"][i]
                            r_last = cls.gesture_data["right"][i]
                            break
                ud_ratio_first = (u_first - d_first) * 100 / (u_first + d_first)
                lr_ratio_first = (l_first - r_first) * 100 / (l_first + r_first)
                ud_ratio_last = (u_last - d_last) * 100 / (u_last + d_last)
                lr_ratio_last = (l_last - r_last) * 100 / (l_last + r_last)
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
            def _decodeGesture(cls):
                if cls.state == "near":
                    cls.gesture_motion = 5
                    return True
                elif cls.state == "far":
                    cls.gesture_motion = 6
                    return True
                
                if cls.ud_count == -1 and cls.lr_count == 0:
                    cls.gesture_motion = "Up"
                elif cls.ud_count == 1 and cls.lr_count == 0:
                    cls.gesture_motion = "Down"
                elif cls.ud_count == 0 and cls.lr_count == 1:
                    cls.gesture_motion == "Right"
                elif cls.ud_count == 0 and cls.lr_count == -1:
                    cls.gesture_motion == "Left"
                elif cls.ud_count == -1 and cls.lr_count == 1:
                    if abs(cls.ud_delta) > abs(cls.lr_delta):
                        cls.gesture_motion = "Up"
                    else:
                        cls.gesture_motion = "Right"
                elif cls.ud_count == 1 and cls.lr_count == -1:
                    if abs(cls.ud_delta) > abs(cls.lr_delta):
                        cls.gesture_motion = "Down"
                    else:
                        cls.gesture_motion = "Left"
                elif cls.ud_count == 1 and cls.lr_count == 1:
                    if abs(cls.ud_delta) > abs(cls.lr_delta):
                        cls.gesture_motion = "Down"
                    else:
                        cls.gesture_motion = "Right"
                else:
                    return False
                return True
            
            @classmethod
            def _valid(cls):
                gstatus = struct.unpack('<B', cls._outer.i2c_read(cls._outer.ADR, 0xAF, data_len=1))[0]
                print(gstatus)
                return gstatus%2
            
            @classmethod
            def get_gesture(cls) -> int:
                fifo_level = 0
                bytes_read = 0
                fifo_data = None
                gstatus = 0
                motion = "None"
                
                if not cls._valid():
                    print("here")
                    return "None"
                
                while True:
                    if cls._valid():
                        fifo_level = struct.unpack('<B', cls._outer.i2c_read(cls._outer.ADR, cls.R_GFLVL, data_len=1))[0]
                        if fifo_level > 0:
                            fifo_data = struct.unpack('<' + 'BBBB' * fifo_level, cls._outer.i2c_read(cls._outer.ADR, 0xFC, data_len=4*fifo_level))
                            fifo_level = struct.unpack('<B', cls._outer.i2c_read(cls._outer.ADR, cls.R_GFLVL, data_len=1))[0]
                            if len(fifo_data) >= 4:
                                for i in range(0, len(fifo_data), 4):
                                    cls.gesture_data["up"][cls.index] = fifo_data[i+0]
                                    cls.gesture_data["down"][cls.index] = fifo_data[i+1]
                                    cls.gesture_data["right"][cls.index] = fifo_data[i+2]
                                    cls.gesture_data["left"][cls.index] = fifo_data[i+3]
                                    cls.index += 1
                                    cls.total_gestures += 1
                            cls._processData()
                            cls._decodeGesture()
                            cls.index = 0
                            cls.total_gestures = 0
                    else:
                        print("here")
                        cls._decodeGesture()
                        motion = cls.gesture_motion
                        cls.reset()
                        return motion
                        
                
        _gesture._outer = self
        return _gesture

