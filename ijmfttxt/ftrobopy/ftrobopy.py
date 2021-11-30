"""
***********************************************************************
**ftrobopy** - Ansteuerung des fischertechnik TXT Controllers in Python
***********************************************************************
(c) 2015, 2016, 2017, 2018, 2019, 2020, 2021 by Torsten Stuehn
"""

from __future__ import print_function
from os import system
import os
import platform
import sys
import socket
import threading
import struct
import time
from math import sqrt, log

try:
    import ftTA2py
except:
    pass

__author__ = "Torsten Stuehn"
__copyright__ = "Copyright 2015 - 2021 by Torsten Stuehn"
__credits__ = "fischertechnik GmbH"
__license__ = "MIT License"
__version__ = "1.97"
__maintainer__ = "Torsten Stuehn"
__email__ = "stuehn@mailbox.org"
__status__ = "beta"
__date__ = "07/04/2021"

try:
    xrange
except NameError:
    xrange = range


def version():

    return __version__ + " " + __status__


def default_error_handler(message, exception):
    print(message)
    return False


def default_data_handler(ftTXT):
    pass


class ftTXT(object):

    C_VOLTAGE = 0
    C_SWITCH = 1
    C_RESISTOR = 1
    C_ULTRASONIC = 3
    C_ANALOG = 0
    C_DIGITAL = 1
    C_OUTPUT = 0
    C_MOTOR = 1

    # command codes for TXT motor shield
    C_MOT_CMD_CONFIG_IO = 0x51
    C_MOT_CMD_EXCHANGE_DATA = 0x54

    # input configuration codes for TXT motor shield
    C_MOT_INPUT_DIGITAL_VOLTAGE = 0
    C_MOT_INPUT_DIGITAL_5K = 1
    C_MOT_INPUT_ANALOG_VOLTAGE = 2
    C_MOT_INPUT_ANALOG_5K = 3
    C_MOT_INPUT_ULTRASONIC = 4

    C_EXT_MASTER = 0  # use TXT master
    C_EXT_SLAVE = 1  # use TXT slave extension

    # sound commands and messages for spi communication to motor shield (only needed in direct mode)
    C_SND_CMD_STATUS = 0x80
    C_SND_CMD_DATA = 0x81
    C_SND_CMD_RESET = 0x90
    C_SND_MSG_RX_CMD = 0xBB  # return if in CMD mode
    C_SND_MSG_RX_DATA = 0x55  # return if in DATA mode
    C_SND_MSG_RX_COMPLETE = 0xAA  # return after all data has been transfered
    C_SND_MSG_ERR_SIZE = 0xFE  # spi buffer overflow
    C_SND_MSG_ERR_FULL = 0xFF  # spi communication not possible, all buffers are full
    C_SND_FRAME_SIZE = 441  # 22050 Hz, 20ms
    # sound communication state machine
    C_SND_STATE_IDLE = 0x00
    C_SND_STATE_START = 0x01
    C_SND_STATE_STOP = 0x02
    C_SND_STATE_RUNNING = 0x03
    C_SND_STATE_DATA = 0x04

    def __init__(
        self,
        host="127.0.0.1",
        port=65000,
        serport="/dev/ttyO2",
        on_error=default_error_handler,
        on_data=default_data_handler,
        directmode=False,
        use_extension=False,
        use_TransferAreaMode=False,
    ):

        self._m_devicename = b""
        self._m_version = 0
        self._host = host
        self._port = port
        self._ser_port = serport
        self.handle_error = on_error
        self.handle_data = on_data
        self._directmode = directmode
        self._use_extension = use_extension
        self._use_TransferAreaMode = use_TransferAreaMode
        self._spi = None
        self._SoundFilesDir = ""
        self._SoundFilesList = []
        # current state of sound-communication state-machine in 'direct'-mode
        self._sound_state = 0
        self._sound_data = []  # curent buffer for sound data (wav-file[44:])
        self._sound_data_idx = 0
        self._sound_current_rep = 0
        self._sound_current_volume = 100
        self._TransferArea_isInitialized = False
        if self._use_TransferAreaMode:
            if (ftTA2py.initTA()) == 1:
                self._TransferArea_isInitialized = True
            else:
                print(
                    "Error: Transfer Area could not be initialized! Please check if ftTA2py.so exists."
                )
                sys.exit(-1)
        elif self._directmode:
            if use_extension:
                print(
                    "Error: direct-mode does currently not support TXT slave extensions."
                )
                sys.exit(-1)
            import serial

            self._ser_ms = serial.Serial(self._ser_port, 230000, timeout=1)
            self._sock = None
            import spidev

            try:
                self._spi = spidev.SpiDev(1, 0)  # /dev/spidev1.0
            except error:
                print(
                    "Error opening SPI device (this is needed for sound in 'direct'-mode)."
                )
                # print(error)
                self._spi = None
            if self._spi:
                self._spi.mode = 3
                self._spi.bits_per_word = 8
                self._spi.max_speed_hz = 1000000
                # reset sound on motor shield
                res = self._spi.xfer([self.C_SND_CMD_RESET, 0, 0])
                if res[0] != self.C_SND_MSG_RX_CMD:
                    print(
                        "Error: initial sound reset returns: ",
                        "".join(["0x%02X " % x for x in res]).split(),
                    )
                    sys.exit(-1)
                # check if we are running on original-firmware or on community-firmware
                # this is only needed to find the original Sound Files
                if os.path.isdir("/rom"):
                    self._SoundFilesDir = "/rom/opt/knobloch/SoundFiles/"
                else:
                    self._SoundFilesDir = "/opt/knobloch/SoundFiles/"
                self._SoundFilesList = os.listdir(self._SoundFilesDir)
                self._SoundFilesList.sort()

        else:
            self._sock = socket.socket()
            self._sock.settimeout(5)
            self._sock.connect((self._host, self._port))
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.setblocking(1)
            self._ser_ms = None
            self._i2c_sock = socket.socket()
            self._i2c_sock.settimeout(5)

        self._txt_stop_event = threading.Event()
        self._camera_stop_event = threading.Event()
        self._bt_joystick_stop_event = threading.Event()
        self._txt_stop_event.set()
        self._camera_stop_event.set()
        self._bt_joystick_stop_event.set()
        self._exchange_data_lock = threading.RLock()
        self._camera_data_lock = threading.Lock()
        self._bt_joystick_lock = threading.RLock()
        self._socket_lock = threading.Lock()
        self._txt_thread = None
        self._camera_thread = None
        self._bt_joystick_thread = None
        self._update_status = 0
        self._update_timer = time.time()
        self._cycle_count = 0
        self._sound_timer = self._update_timer
        self._sound_length = 0
        self._config_id = [0, 0]  # [0]:master [1]:slave
        self._config_id_old = 0  # only used in direct mode
        self._TransferDataChanged = False
        self._ftX1_pgm_state_req = 0
        self._ftX1_old_FtTransfer = 0
        self._ftX1_dummy = b"\x00\x00"
        self._ftX1_motor = [1, 1, 1, 1, 1, 1, 1, 1]
        self._ftX1_uni = [
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
            1,
            1,
            b"\x00\x00",
        ]
        self._ftX1_cnt = [
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
            1,
            b"\x00\x00\x00",
        ]
        self._ftX1_motor_config = [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
        self._exchange_data_lock.acquire()
        self._pwm = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self._motor_sync = [0, 0, 0, 0, 0, 0, 0, 0]
        self._motor_dist = [0, 0, 0, 0, 0, 0, 0, 0]
        self._motor_cmd_id = [0, 0, 0, 0, 0, 0, 0, 0]
        self._counter = [0, 0, 0, 0, 0, 0, 0, 0]
        self._sound = [0, 0]
        self._sound_index = [0, 0]
        self._sound_repeat = [0, 0]
        self._current_input = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self._current_counter = [0, 0, 0, 0, 0, 0, 0, 0]
        self._current_counter_value = [0, 0, 0, 0, 0, 0, 0, 0]
        self._current_counter_cmd_id = [0, 0, 0, 0, 0, 0, 0, 0]
        self._current_motor_cmd_id = [0, 0, 0, 0, 0, 0, 0, 0]
        self._current_sound_cmd_id = [0, 0]
        self._current_ir = [0 for i in range(26)]
        self._ir_current_ljoy_left_right = [0, 0, 0, 0, 0]  # -15 ... 15
        self._ir_current_ljoy_up_down = [0, 0, 0, 0, 0]  # -15 ... 15
        self._ir_current_rjoy_left_right = [0, 0, 0, 0, 0]  # -15 ... 15
        self._ir_current_rjoy_up_down = [0, 0, 0, 0, 0]  # -15 ... 15
        self._ir_current_buttons = [0, 0, 0, 0, 0]  # 0:OFF 1:ON
        # 0:all 1:0-0 2:1-0 3:0-1 4:1-1
        self._ir_current_dip_switch = [0, 0, 0, 0, 0]
        self._bt_ljoy_left_right = 0  # -32767 ... 32512
        self._bt_ljoy_up_down = 0  # -32767 ... 32512
        self._bt_rjoy_left_right = 0  # -32767 ... 32512
        self._bt_rjoy_up_down = 0  # -32767 ... 32512
        # self._bt_buttons                 = 0 # the bluetooth remote has no detectable buttons
        # self._bt_dip_switch              = 0 # and no dip switches; currently only one bt remote can be connected
        self._current_power = 0  # voltage of battery or power supply
        self._current_temperature = 0  # temperature of ARM CPU
        self._current_reference_power = 0
        self._current_extension_power = 0
        self._debug = []
        self._firstUpdateConfig = [True, True]
        self._exchange_data_lock.release()

    def stopTransferArea(self):
        if self._TransferArea_isInitialized:
            ftTA2py.stopTA()

    def isOnline(self):
        if self._use_TransferAreaMode:
            return self._TransferArea_isInitialized
        else:
            return (not self._txt_stop_event.is_set()) and (
                self._txt_thread is not None
            )

    def cameraIsOnline(self):
        return (not self._camera_stop_event.is_set()) and (
            self._camera_thread is not None
        )

    def queryStatus(self):

        if self._use_TransferAreaMode:
            # TODO
            # not sure how to detect version yet, just set standard value
            self._m_devicename = "TXT TransferAreaMode"
            self._m_version = 0x4060600
            self._m_firmware = "firmware version not detected"
            return self._m_devicename, self._m_version
        elif self._directmode:
            # not sure how to detect version yet, just set standard value
            self._m_devicename = "TXT direct"
            self._m_version = 0x4010500
            self._m_firmware = "firmware version not detected"
            return self._m_devicename, self._m_version
        m_id = 0xDC21219A
        m_resp_id = 0xBAC9723E
        buf = struct.pack("<I", m_id)
        self._socket_lock.acquire()
        res = self._sock.send(buf)
        data = self._sock.recv(512)
        self._socket_lock.release()
        fstr = "<I16sI"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            response_id, m_devicename, m_version = struct.unpack(fstr, data)
        else:
            m_devicename = ""
            m_version = 0
        if response_id != m_resp_id:
            print(
                "WARNING: ResponseID ",
                hex(response_id),
                "of queryStatus command does not match",
            )
        self._m_devicename = m_devicename.decode("utf-8").strip("\x00")
        self._m_version = m_version
        v1 = int(hex(m_version)[2])
        v2 = int(hex(m_version)[3:5])
        v3 = int(hex(m_version)[5:7])
        self._m_firmware = "firmware version " + str(v1) + "." + str(v2) + "." + str(v3)
        return m_devicename, m_version

    def i2c_read(self, dev, reg, reg_len=1, data_len=1, debug=False):

        m_id = 0xB9DB3B39
        m_resp_id = 0x87FD0D90
        m_command = 0x01
        buf = struct.pack(">IBIIHH", m_id, m_command, dev, reg_len, data_len, reg)
        if debug:
            print("i2c_read, sendbuffer: ", end="")
            for k in buf:
                print(format(int(k), "02X"), end=" ")
            print()
        res = self._i2c_sock.send(buf)
        data = self._i2c_sock.recv(512)
        if debug:
            print("i2c_read, receivebuffer: ", end="")
            for k in data:
                print(format(int(k), "02X"), end=" ")
            print()
        fstr = ">IBIHB"
        for k in range(data_len):
            fstr += "B"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            response_id = struct.unpack(fstr, data)[0]
        if response_id != m_resp_id:
            self.handle_error(
                "WARNING: ResponseID %s of I2C read command does not match"
                % hex(response_id),
                None,
            )
            return None
        return data[-data_len:]

    def i2c_write(self, dev, reg, value, debug=False):

        m_id = 0xB9DB3B39
        m_resp_id = 0x87FD0D90
        m_command = 0x02
        buf = struct.pack(">IBIIIB", m_id, m_command, dev, 0x02, reg, value)
        if debug:
            print("i2c_write, sendbuffer: ", end="")
            for k in buf:
                print(format(int(k), "02X"), end=" ")
            print()
        res = self._i2c_sock.send(buf)
        data = self._i2c_sock.recv(512)
        if debug:
            print("i2c_write, receivebuffer: ", end="")
            for k in data:
                print(format(int(k), "02X"), end=" ")
            print()
        fstr = ">III"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            response_id = struct.unpack(fstr, data)[0]
        if response_id != m_resp_id:
            self.handle_error(
                "WARNING: ResponseID %s of I2C write command does not match"
                % hex(response_id),
                None,
            )
            return None
        return True

    def i2c_write_bytes(self, dev, *argv):
        m_id = 0xB9DB3B39
        m_resp_id = 0x87FD0D90

        m_lenth = 0
        for i in argv:
            m_lenth += 1
        buf = struct.pack(">IBIIBBB", m_id, m_lenth, dev, m_lenth, 0x00, 0x00, 0x00)
        for i in argv:
            buf += struct.pack("B", i)

        if debug:
            print("i2c_write, sendbuffer: ", end="")
            for k in buf:
                print(format(int(k), "02X"), end=" ")
            print()
        res = self._i2c_sock.send(buf)
        data = self._i2c_sock.recv(512)

        if debug:
            print("i2c_write, receivebuffer: ", end="")
            for k in data:
                print(format(int(k), "02X"), end=" ")
            print()
        fstr = ">III"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            response_id = struct.unpack(fstr, data)[0]
        if response_id != m_resp_id:
            self.handle_error(
                "WARNING: ResponseID %s of I2C write command does not match"
                % hex(response_id),
                None,
            )
            return None

        return True

    def i2c_write_buffer(self, dev, buffer, m_length, debug=False):
        m_id = 0xB9DB3B39
        buf = (
            struct.pack(">IBIIBBB", m_id, m_length, dev, m_length, 0x00, 0x00, 0x00)
            + buffer
        )

        if debug:
            print("i2c_write, sendbuffer: ", end="")
            for k in buf:
                print(format(int(k), "02X"), end=" ")
            print()
        res = self._i2c_sock.send(buf)
        data = self._i2c_sock.recv(512)

        if debug:
            print("i2c_write, receivebuffer: ", end="")
            for k in data:
                print(format(int(k), "02X"), end=" ")
            print()
        fstr = ">III"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            response_id = struct.unpack(fstr, data)[0]
        if response_id != 0x87FD0D90:
            self.handle_error(
                "WARNING: ResponseID %s of I2C write command does not match"
                % hex(response_id),
                None,
            )
            return None

        return True

    def getDevicename(self):

        return self._m_devicename

    def getVersionNumber(self):

        return self._m_version

    def getFirmwareVersion(self):

        return self._m_firmware

    def startOnline(self, update_interval=0.02):

        if self._TransferArea_isInitialized:
            return
        if self._directmode == True:
            if self._txt_stop_event.is_set():
                self._txt_stop_event.clear()
            if self._txt_thread is None:
                self._txt_thread = ftTXTexchange(
                    txt=self,
                    sleep_between_updates=update_interval,
                    stop_event=self._txt_stop_event,
                )
                self._txt_thread.setDaemon(True)
                self._txt_thread.start()
                # keep_connection_thread is only needed when using SyncDataBegin/End in interactive python mode
                # self._txt_keep_connection_stop_event = threading.Event()
                # self._txt_keep_connection_thread = ftTXTKeepConnection(self, 1.0, self._txt_keep_connection_stop_event)
                # self._txt_keep_connection_thread.setDaemon(True)
                # self._txt_keep_connection_thread.start()
            return None
        if self._txt_stop_event.is_set():
            self._txt_stop_event.clear()
        else:
            return
        if self._txt_thread is None:
            m_id = 0x163FF61D
            m_resp_id = 0xCA689F75
            buf = struct.pack("<I64s", m_id, b"")
            self._socket_lock.acquire()
            res = self._sock.send(buf)
            data = self._sock.recv(512)
            self._socket_lock.release()
            fstr = "<I"
            response_id = 0
            if len(data) == struct.calcsize(fstr):
                (response_id,) = struct.unpack(fstr, data)
            if response_id != m_resp_id:
                self.handle_error(
                    "WARNING: ResponseID %s of startOnline command does not match"
                    % hex(response_id),
                    None,
                )
            else:
                self.updateConfig(self.C_EXT_MASTER)
                if self._use_extension:
                    self.updateConfig(self.C_EXT_SLAVE)
                self._txt_thread = ftTXTexchange(
                    txt=self,
                    sleep_between_updates=update_interval,
                    stop_event=self._txt_stop_event,
                )
                self._txt_thread.setDaemon(True)
                self._txt_thread.start()
                # keep_connection_thread is needed when using SyncDataBegin/End in interactive python mode
                self._txt_keep_connection_stop_event = threading.Event()
                self._txt_keep_connection_thread = ftTXTKeepConnection(
                    self, 1.0, self._txt_keep_connection_stop_event
                )
                self._txt_keep_connection_thread.setDaemon(True)
                self._txt_keep_connection_thread.start()
                time.sleep(0.1)
                self._i2c_sock.connect((self._host, self._port + 2))
                self._i2c_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._i2c_sock.setblocking(1)
        return None

    def stopOnline(self):

        if self._TransferArea_isInitialized:
            self.stopTransferArea()
            return None
        if self._directmode:
            self._txt_stop_event.set()
            self._txt_thread = None
            if self._spi:
                self._spi.close()
            return None
        if not self.isOnline():
            return
        self._txt_stop_event.set()
        self._txt_keep_connection_stop_event.set()
        m_id = 0x9BE5082C
        m_resp_id = 0xFBF600D2
        buf = struct.pack("<I", m_id)
        self._socket_lock.acquire()
        res = self._sock.send(buf)
        data = self._sock.recv(512)
        self._socket_lock.release()
        fstr = "<I"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            (response_id,) = struct.unpack(fstr, data)
        if response_id != m_resp_id:
            self.handle_error(
                "WARNING: ResponseID %s of stopOnline command does not match"
                % hex(response_id),
                None,
            )
        self._txt_thread = None
        return None

    def setConfig(self, M, I, ext=C_EXT_MASTER):

        self._config_id[ext] += 1
        # Configuration of motors
        # 0=single output O1/O2
        # 1=motor output M1
        # self.ftX1_motor          = [M[0],M[1],M[2],M[3]]  # BOOL8[4]
        self._ftX1_motor[4 * ext : 4 * ext + 4] = M
        # Universal input mode, see enum InputMode:
        # MODE_U=0
        # MODE_R=1
        # MODE_R2=2
        # MODE_ULTRASONIC=3
        # MODE_INVALID=4
        # print("setConfig I=", I)
        self._ftX1_uni[24 * ext : 24 * ext + 24] = [
            I[0][0],
            I[0][1],
            b"\x00\x00",
            I[1][0],
            I[1][1],
            b"\x00\x00",
            I[2][0],
            I[2][1],
            b"\x00\x00",
            I[3][0],
            I[3][1],
            b"\x00\x00",
            I[4][0],
            I[4][1],
            b"\x00\x00",
            I[5][0],
            I[5][1],
            b"\x00\x00",
            I[6][0],
            I[6][1],
            b"\x00\x00",
            I[7][0],
            I[7][1],
            b"\x00\x00",
        ]
        return None

    def getConfig(self, ext=C_EXT_MASTER):

        m = self._ftX1_motor[4 * ext : 4 * ext + 4]
        i = self._ftX1_uni[24 * ext : 24 * ext + 24]
        ii = [
            (i[0], i[1]),
            (i[3], i[4]),
            (i[6], i[7]),
            (i[9], i[10]),
            (i[12], i[13]),
            (i[15], i[16]),
            (i[18], i[19]),
            (i[21], i[22]),
        ]
        return m, ii

    def updateConfig(self, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            # in TransferAreaMode the configuration is automatically updated
            return
        if self._directmode:
            # in direct mode i/o port configuration is performed automatically in exchangeData thread
            return
        if not self._firstUpdateConfig[ext]:
            if not self.isOnline():
                self.handle_error(
                    "Controller must be online before updateConfig() is called", None
                )
                return
            self._firstUpdateConfig[ext] = False
        m_id = 0x060EF27E
        m_resp_id = 0x9689A68C
        self._config_id[ext] += 1
        fields = [m_id, self._config_id[ext], ext]
        fields.append(self._ftX1_pgm_state_req)
        fields.append(self._ftX1_old_FtTransfer)
        fields.append(self._ftX1_dummy)
        fields += self._ftX1_motor[4 * ext : 4 * ext + 4]
        fields += self._ftX1_uni[24 * ext : 24 * ext + 24]
        fields += self._ftX1_cnt[8 * ext : 8 * ext + 8]
        fields += self._ftX1_motor_config[16 * ext : 16 * ext + 16]
        buf = struct.pack(
            "<Ihh B B 2s BBBB BB2s BB2s BB2s BB2s BB2s BB2s BB2s BB2s B3s B3s B3s B3s 16h",
            *fields
        )
        self._socket_lock.acquire()
        res = self._sock.send(buf)
        data = self._sock.recv(512)
        self._socket_lock.release()
        fstr = "<I"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            (response_id,) = struct.unpack(fstr, data)
        if response_id != m_resp_id:
            self.handle_error(
                "WARNING: ResponseID %s of updateConfig command does not match"
                % hex(response_id),
                None,
            )
            # Stop the data exchange thread and the keep connection thread if we were online
            self._txt_stop_event.set()
            self._txt_keep_connection_stop_event.set()
        return None

    def startCameraOnline(self):

        if self._directmode:
            # ftrobopy.py does not support camera in direct mode, please use native camera support (e.g. ftrobopylib.so or opencv)
            return
        if self._camera_stop_event.is_set():
            self._camera_stop_event.clear()
        else:
            return
        if self._camera_thread is None:
            m_id = 0x882A40A6
            m_resp_id = 0xCF41B24E
            self._m_width = 320
            self._m_height = 240
            self._m_framerate = 15
            self._m_powerlinefreq = 0  # 0=auto, 1=50Hz, 2=60Hz
            buf = struct.pack(
                "<I4i",
                m_id,
                self._m_width,
                self._m_height,
                self._m_framerate,
                self._m_powerlinefreq,
            )
            self._socket_lock.acquire()
            res = self._sock.send(buf)
            data = self._sock.recv(512)
            self._socket_lock.release()
            fstr = "<I"
            response_id = 0
            if len(data) == struct.calcsize(fstr):
                (response_id,) = struct.unpack(fstr, data)
            if response_id != m_resp_id:
                print(
                    "WARNING: ResponseID ",
                    hex(response_id),
                    " of startCameraOnline command does not match",
                )
            else:
                self._camera_thread = camera(
                    self._host,
                    self._port + 1,
                    self._camera_data_lock,
                    self._camera_stop_event,
                )
                self._camera_thread.setDaemon(True)
                self._camera_thread.start()
        return

    def stopCameraOnline(self):

        if self._directmode:
            return
        if not self.cameraIsOnline():
            return
        self._camera_stop_event.set()
        m_id = 0x17C31F2F
        m_resp_id = 0x4B3C1EB6
        buf = struct.pack("<I", m_id)
        self._socket_lock.acquire()
        res = self._sock.send(buf)
        data = self._sock.recv(512)
        self._socket_lock.release()
        fstr = "<I"
        response_id = 0
        if len(data) == struct.calcsize(fstr):
            (response_id,) = struct.unpack(fstr, data)
        if response_id != m_resp_id:
            print(
                "WARNING: ResponseID ",
                hex(response_id),
                " of stopCameraOnline command does not match",
            )
        self._camera_thread = None
        return

    def getCameraFrame(self):

        if self._directmode:
            return
        if self.cameraIsOnline():
            count = 0
            frame = None
            while frame == None:
                frame = self._camera_thread.getCameraFrame()
                count += 1
                if frame != None:
                    if len(frame) == 0:
                        frame = None
                if count > 20:
                    print("Timeout while getting new frame from camera")
                    return None
                time.sleep(0.01)
            return frame
        else:
            return None

    def incrMotorCmdId(self, idx, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            ftTA2py.fX1out_incr_motor_cmd_id(ext, idx)
        else:
            self._exchange_data_lock.acquire()
            self._motor_cmd_id[4 * ext + idx] += 1
            self._motor_cmd_id[4 * ext + idx] &= 0x07
            self._exchange_data_lock.release()
            self._TransferDataChanged = True
        return None

    def getMotorCmdId(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            if idx != None:
                ret = ftTA2py.fX1in_motor_ex_cmd_id(ext, idx)
            else:
                ret = [
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 0),
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 1),
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 2),
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 3),
                ]
        else:
            if idx != None:
                ret = self._motor_cmd_id[4 * ext + idx]
            else:
                ret = self._motor_cmd_id[4 * ext : 4 * ext + 4]
        return ret

    def cameraOnline(self):

        return self._camera_online

    def getSoundCmdId(self, ext=C_EXT_MASTER):

        return self._sound[ext]

    def incrCounterCmdId(self, idx, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            # not used
            return
        self._exchange_data_lock.acquire()
        self._counter[4 * ext + idx] += 1
        self._counter[4 * ext + idx] &= 0x07
        self._exchange_data_lock.release()
        self._TransferDataChanged = True
        return None

    def incrSoundCmdId(self, ext=C_EXT_MASTER):

        self._exchange_data_lock.acquire()
        self._sound[ext] += 1
        self._sound[ext] &= 0x0F
        self._exchange_data_lock.release()
        self._TransferDataChanged = True
        return None

    def setSoundIndex(self, idx, ext=C_EXT_MASTER):

        self._exchange_data_lock.acquire()
        self._sound_index[ext] = idx
        self._exchange_data_lock.release()
        if self._directmode and self._spi:
            self._exchange_data_lock.acquire()
            self._sound_data = []
            self._sound_data_idx = 0
            self._exchange_data_lock.release()
            if idx > 0:
                snd_file_name = self._SoundFilesDir + self._SoundFilesList[idx - 1]
                with open(snd_file_name, "rb") as f:
                    buf = f.read()
                    # first 44 bytes of ft soundfiles is header data
                    self._exchange_data_lock.acquire()
                    self._sound_data = list(bytearray(buf[44:]))
                    filler = [
                        0x80
                        for i in range(
                            self.C_SND_FRAME_SIZE
                            - (len(self._sound_data) % self.C_SND_FRAME_SIZE)
                        )
                    ]
                    self._sound_data += filler
                    self._sound_data_idx = 0
                    self._exchange_data_lock.release()
                    self._sound_current_volume = 100
        self._TransferDataChanged = True
        return None

    def getSoundIndex(self, ext=C_EXT_MASTER):

        return self._sound_index[ext]

    def setSoundRepeat(self, rep, ext=C_EXT_MASTER):

        self._exchange_data_lock.acquire()
        self._sound_repeat[ext] = rep
        self._exchange_data_lock.release()
        self._TransferDataChanged = True
        return None

    def getSoundRepeat(self, ext=C_EXT_MASTER):

        return self._sound_repeat[ext]

    def setSoundVolume(self, volume):

        if self._directmode:
            if volume > 100:
                volume = 100
            if volume < 0:
                volume = 0
            if volume > self.getSoundVolume():
                # load wav-file again when increasing volume to get best results
                self.setSoundIndex(self.getSoundIndex())
            if self._sound_current_volume != volume:
                self._sound_current_volume = volume
                self._exchange_data_lock.acquire()
                for i in xrange(0, len(self._sound_data)):
                    w = self._sound_current_volume * self._sound_data[i] / 100
                    self._sound_data[i] = int(w) & 0xFF
                self._sound_data_idx = 0
                self._exchange_data_lock.release()
        else:
            print("setSoundVolume() steht nur im 'direct'-Modus zur Verfuegung.")
            return None

    def getSoundVolume(self):

        if self._directmode:
            return self._sound_current_volume
        else:
            print("getSoundVolume() steht nur im 'direct'-Modus zur Verfuegung.")
            return None

    def getCounterCmdId(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            # not used
            return
        if idx != None:
            ret = self._counter[4 * ext + idx]
        else:
            ret = self._counter[4 * ext : 4 * ext + 4]
        return ret

    def setPwm(self, idx, value, ext=C_EXT_MASTER):

        if value == 1:
            value = 0
        if self._use_TransferAreaMode:
            ftTA2py.fX1out_duty(0, idx, value)
            self._pwm[8 * ext + idx] = value
            return
        self._exchange_data_lock.acquire()
        self._pwm[8 * ext + idx] = value
        self._exchange_data_lock.release()
        self._TransferDataChanged = True
        return None

    def stopAll(self):

        if self._use_extension:
            n = 16
        else:
            n = 8
        for i in range(n):
            self.setPwm(i, 0)
        self._TransferDataChanged = True
        return

    def getPwm(self, idx=None, ext=C_EXT_MASTER):

        if idx != None:
            ret = self._pwm[8 * ext + idx]
        else:
            ret = self._pwm[8 * ext : 8 * ext + 8]
        return ret

    def setMotorSyncMaster(self, idx, value, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            ftTA2py.fX1out_master(ext, idx, value)
            self._motor_sync[4 * ext + idx] = value
            return
        self._exchange_data_lock.acquire()
        self._motor_sync[4 * ext + idx] = value
        self._exchange_data_lock.release()
        self._TransferDataChanged = True
        return None

    def getMotorSyncMaster(self, idx=None, ext=C_EXT_MASTER):

        if idx != None:
            ret = self._motor_sync[4 * ext + idx]
        else:
            ret = self._motor_sync[4 * ext : ext + 4]
        return ret

    def setMotorDistance(self, idx, value, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            ftTA2py.fX1out_distance(ext, idx, value)
            self._motor_dist[4 * ext + idx] = value
            return
        self._exchange_data_lock.acquire()
        self._motor_dist[4 * ext + idx] = value
        self._exchange_data_lock.release()
        self._TransferDataChanged = True
        return None

    def getMotorDistance(self, idx=None, ext=C_EXT_MASTER):

        if idx != None:
            ret = self._motor_dist[4 * ext + idx]
        else:
            ret = self._motor_dist[4 * ext : 4 * ext + 4]
        return ret

    def getCurrentInput(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            if idx != None:
                ret = ftTA2py.fX1in_uni(ext, idx)
            else:
                ret = [
                    ftTA2py.fX1in_uni(ext, 0),
                    ftTA2py.fX1in_uni(ext, 1),
                    ftTA2py.fX1in_uni(ext, 2),
                    ftTA2py.fX1in_uni(ext, 3),
                    ftTA2py.fX1in_uni(ext, 4),
                    ftTA2py.fX1in_uni(ext, 5),
                    ftTA2py.fX1in_uni(ext, 6),
                    ftTA2py.fX1in_uni(ext, 7),
                ]
        else:
            if idx != None:
                ret = self._current_input[8 * ext + idx]
            else:
                ret = self._current_input[8 * ext : 8 * ext + 8]
        return ret

    def getCurrentCounterInput(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            if idx != None:
                ret = ftTA2py.fX1in_cnt_in(ext, idx)
            else:
                ret = [
                    ftTA2py.fX1in_cnt_in(ext, 0),
                    ftTA2py.fX1in_cnt_in(ext, 1),
                    ftTA2py.fX1in_cnt_in(ext, 2),
                    ftTA2py.fX1in_cnt_in(ext, 3),
                ]
        else:
            if idx != None:
                ret = self._current_counter[4 * ext + idx]
            else:
                ret = self._current_counter[4 * ext : 4 * ext + 4]
        return ret

    def getCurrentCounterValue(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            if idx != None:
                ret = ftTA2py.fX1in_counter(ext, idx)
            else:
                ret = [
                    ftTA2py.fX1in_counter(ext, 0),
                    ftTA2py.fX1in_counter(ext, 1),
                    ftTA2py.fX1in_counter(ext, 2),
                    ftTA2py.fX1in_counter(ext, 3),
                ]
        else:
            if idx != None:
                ret = self._current_counter_value[4 * ext + idx]
            else:
                ret = self._current_counter_value[4 * ext : 4 * ext + 4]
        return ret

    def getCurrentCounterCmdId(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            if idx != None:
                ret = ftTA2py.fX1in_cnt_reset_cmd_id(ext, idx)
            else:
                ret = [
                    ftTA2py.fX1in_cnt_reset_cmd_id(ext, 0),
                    ftTA2py.fX1in_cnt_reset_cmd_id(ext, 1),
                    ftTA2py.fX1in_cnt_reset_cmd_id(ext, 2),
                    ftTA2py.fX1in_cnt_reset_cmd_id(ext, 3),
                ]
        else:
            if idx != None:
                ret = self._current_counter_cmd_id[4 * ext + idx]
            else:
                ret = self._current_counter_cmd_id[4 * ext : 4 * ext + 4]
        return ret

    def getCurrentMotorCmdId(self, idx=None, ext=C_EXT_MASTER):

        if self._use_TransferAreaMode:
            if idx != None:
                ret = ftTA2py.fX1in_motor_ex_cmd_id(ext, idx)
            else:
                ret = [
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 0),
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 1),
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 2),
                    ftTA2py.fX1in_motor_ex_cmd_id(ext, 3),
                ]
        else:
            if idx != None:
                ret = self._current_motor_cmd_id[4 * ext + idx]
            else:
                ret = self._current_motor_cmd_id[4 * ext : 4 * ext + 4]
        return ret

    def getCurrentSoundCmdId(self, ext=C_EXT_MASTER):

        ret = self._current_sound_cmd_id[ext]
        return ret

    def getCurrentIr(self):

        if self._directmode:
            return
        ret = self._current_ir
        return ret

    def getHost(self):

        return self._host

    def getPort(self):

        return self._port

    def getPower(self, ext=C_EXT_MASTER):

        if self._use_TransferMode:
            return ftTA2py.TxtPowerSupply(ext)
        elif self._directmode:
            return self._current_power
        else:
            print("Diese Funktion steht nur im 'direct'-Modus zur Verfuegung.")
            return None

    def getTemperature(self, ext=C_EXT_MASTER):

        if self._use_TransferMode:
            return ftTA2py.TxtCPUTemperature(ext)
        if self._directmode:
            return self._current_temperature
        else:
            print("Diese Funktion steht nur im 'direct'-Modus zur Verfuegung.")
            return None

    def getReferencePower(self):

        if self._directmode:
            return self._current_reference_power
        else:
            print("Diese Funktion steht nur im 'direct'-Modus zur Verfuegung.")
            return None

    def getExtensionPower(self):

        if self._directmode:
            return self._current_extension_power
        else:
            print("Diese Funktion steht nur im 'direct'-Modus zur Verfuegung.")
            return None

    def SyncDataBegin(self):

        if self._use_TransferAreaMode:
            return
        self._exchange_data_lock.acquire()

    def SyncDataEnd(self):

        if self._use_TransferAreaMode:
            return
        self._exchange_data_lock.release()

    def updateWait(self, minimum_time=0.001):

        if self._use_TransferAreaMode:
            return
        self._exchange_data_lock.acquire()
        self._update_status = 0
        self._exchange_data_lock.release()
        while self._update_status == 0:
            time.sleep(minimum_time)


class ftTXTKeepConnection(threading.Thread):
    def __init__(self, txt, maxtime, stop_event):
        threading.Thread.__init__(self)
        self._txt = txt
        self._txt_maxtime = maxtime
        self._txt_stop_event = stop_event
        return

    def run(self):
        while not self._txt_stop_event.is_set():
            try:
                self._txt._keep_running_lock.acquire()
                o_time = self._txt._update_timer
                self._txt._keep_running_lock.release()
                m_time = time.time() - o_time
                if m_time > self._txt_maxtime:
                    m_id = 0xDC21219A
                    m_resp_id = 0xBAC9723E
                    buf = struct.pack("<I", m_id)
                    self._txt._keep_running_lock.acquire()
                    res = self._txt._sock.send(buf)
                    data = self._txt._sock.recv(512)
                    self._txt._update_timer = time.time()
                    self._txt._keep_running_lock.release()
                    fstr = "<I16sI"
                    response_id = 0
                    if len(data) == struct.calcsize(fstr):
                        response_id, m_devicename, m_version = struct.unpack(fstr, data)
                    else:
                        m_devicename = ""
                        m_version = ""
                    if response_id != m_resp_id:
                        print(
                            "ResponseID ",
                            hex(response_id),
                            "of keep connection queryStatus command does not match",
                        )
                        self._txt_stop_event.set()
                time.sleep(1.0)
            except:
                return
        return


class CRC32(object):
    def __init__(self):
        self.Reset()
        self.m_table = [0 for i in range(256)]
        for dividend in range(256):
            # remainder = (dividend << 24) & 0xffffffff
            remainder = dividend << 24
            for bit in range(8, 0, -1):
                if remainder & 0x80000000:
                    remainder = (remainder << 1) ^ 0x04C11DB7
                else:
                    remainder = remainder << 1
                # remainder &= 0xffffffff
            self.m_table[dividend] = remainder & 0xFFFFFFFF
        return

    def Reset(self):
        self.m_crc = 0xFFFFFFFF
        self.c = 0
        return

    def Add16bit(self, val):
        self.c += 1
        val &= 0xFFFF
        data = (self.m_crc >> 24) ^ (val >> 8)
        data &= 0xFF
        self.m_crc = (self.m_crc << 8) ^ self.m_table[data]
        self.m_crc &= 0xFFFFFFFF
        data = (self.m_crc >> 24) ^ (val & 0xFF)
        data &= 0xFF
        self.m_crc = ((self.m_crc << 8) & 0xFFFFFFFF) ^ self.m_table[data]
        self.m_crc &= 0xFFFFFFFF
        return


class compBuffer(object):
    def __init__(self):
        self.m_crc = CRC32()
        self.Reset()
        return

    def Reset(self):
        self.Rewind()
        self.m_compressed = []
        self.m_nochange_count = 0
        return

    def Rewind(self):
        self.m_bitbuffer = 0
        self.m_bitcount = 0
        self.m_nochange_count = 0
        self.m_previous_word = 0
        self.m_crc.Reset()
        return

    def GetBits(self, count):
        # byte      |2 2 2 2 2 2 2 2|1 1 1 1 1 1 1 1|
        # fragment  |7 7|6 6|5 5|4 4 4 4|3 3|2 2|1 1|
        while self.m_bitcount < count:
            cp = self.m_compressed[0]
            if isinstance(cp, str):
                self.m_bitbuffer |= ord(cp) << self.m_bitcount
            else:
                self.m_bitbuffer |= cp << self.m_bitcount
            self.m_compressed = self.m_compressed[1:]
            self.m_bitcount += 8
        res = self.m_bitbuffer & (0xFFFFFFFF >> (32 - count))
        self.m_bitbuffer >>= count
        self.m_bitcount -= count
        # print("m_bitcount=", self.m_bitcount, " m_bitbuffer=",format(self.m_bitbuffer, '016b'), " m_compressed=",' '.join(format(ord(x),'08b') for x in self.m_compressed))
        return res

    def GetWord(self):
        word = 0
        if self.m_nochange_count > 0:
            self.m_nochange_count -= 1
            word = self.m_previous_word
        else:
            head = self.GetBits(2)
            if head == 0:
                # 00 NoChange 1x16 bit
                word = self.m_previous_word
            elif head == 1:
                # 01 00 NoChange 2x16 bit
                # 01 01 NoChange 3x16 bit
                # 01 10 NoChange 4x16 bit
                # 01 11 xxxx NoChange 5..19x16 bit
                # 01 11 1111 xxxxxxxx NoChange 20..274 x16 bit
                # 01 11 1111 11111111 xxxxxxxx-xxxxxxxx NoChange 275... x16 bit
                word = self.m_previous_word
                count = self.GetBits(2)
                if count < 3:
                    self.m_nochange_count = count + 2 - 1
                else:
                    count = self.GetBits(4)
                    if count < 15:
                        self.m_nochange_count = count + 5 - 1
                    else:
                        count = self.GetBits(8)
                        if count < 255:
                            self.m_nochange_count = count + 20 - 1
                        else:
                            count = self.GetBits(16)
                            self.m_nochange_count = count + 275 - 1
            elif head == 2:
                if self.m_previous_word > 0:
                    word = 0
                else:
                    word = 1
            elif head == 3:
                word = self.GetBits(16)
        self.m_previous_word = 0
        # self.m_crc.Add16bit(word)
        return word

    def PushBits(self, count, bits):
        self.m_bitbuffer |= bits << self.m_bitcount
        self.m_bitbuffer &= 0xFFFFFFFF
        self.m_bitcount += count
        while self.m_bitcount >= 8:
            self.m_bitcount -= 8
            self.m_compressed.append(self.m_bitbuffer & 0xFF)
            self.m_bitbuffer >>= 8
        # print("m_bitcount=", self.m_bitcount, " m_bitbuffer=",format(self.m_bitbuffer, '016b'), " m_compressed=",' '.join(format(ord(x),'08b') for x in self.m_compressed))
        return

    def EncodeNoChangeCount(self):
        # 00 NoChange 1x16 bit
        # 01 00 NoChange 2x16 bit
        # 01 01 NoChange 3x16 bit
        # 01 10 NoChange 4x16 bit
        # 01 11 xxxx NoChange 5..19x16 bit
        # 01 11 1111 xxxxxxxx NoChange 20..274 x16 bit
        # 01 11 1111 11111111 xxxxxxxx-xxxxxxxx NoChange 275... bit
        while self.m_nochange_count > 0:
            if self.m_nochange_count == 1:
                self.PushBits(2, 0)
                break
            elif self.m_nochange_count <= 4:
                self.PushBits(2, 1)
                self.PushBits(2, self.m_nochange_count - 2)
                break
            elif self.m_nochange_count <= 4 + 15:
                self.PushBits(2, 1)
                self.PushBits(2, 3)
                self.PushBits(4, self.m_nochange_count - 4 - 1)
                break
            elif self.m_nochange_count <= 4 + 15 + 255:
                self.PushBits(2, 1)
                self.PushBits(2, 3)
                self.PushBits(4, 15)
                self.PushBits(8, self.m_nochange_count - 4 - 15 - 1)
                break
            elif self.m_nochange_count <= 4 + 15 + 255 + 4096:
                self.PushBits(2, 1)
                self.PushBits(2, 3)
                self.PushBits(4, 15)
                self.PushBits(8, 255)
                self.PushBits(16, self.m_nochange_count - 4 - 15 - 255 - 1)
                break
            else:
                self.PushBits(2, 1)
                self.PushBits(2, 3)
                self.PushBits(4, 15)
                self.PushBits(8, 255)
                self.PushBits(16, 4095)
                self.m_nochange_count += -4 - 15 - 255 - 4096
        self.m_nochange_count = 0
        return

    def AddWord(self, word, word_for_crc=None):
        if word_for_crc == None:
            self.m_crc.Add16bit(word)
        else:
            self.m_crc.Add16bit(word_for_crc)

        if word == self.m_previous_word:
            self.m_nochange_count += 1
        else:
            self.EncodeNoChangeCount()
            if (word == 1 and self.m_previous_word == 0) or (
                word == 0 and self.m_previous_word != 0
            ):
                # 10 Toggle (0 to 1, everything else to 0)
                self.PushBits(2, 2)
            else:
                # 11 16 bit follow immediately
                self.PushBits(2, 3)
                self.PushBits(16, word)
        self.m_previous_word = 0

    def Finish(self):
        self.EncodeNoChangeCount()
        if self.m_bitcount > 0:
            self.PushBits(8 - self.m_bitcount, 0)

    def GetCompBuffer(self):
        return self.m_compressed


class ftTXTexchange(threading.Thread):
    def __init__(self, txt, sleep_between_updates, stop_event):
        threading.Thread.__init__(self)
        self._txt = txt
        self._txt_sleep_between_updates = sleep_between_updates
        self._txt_stop_event = stop_event
        self._txt_interval_timer = time.time()
        if self._txt._use_extension:
            self.compBuffer = compBuffer()
        self._crc0 = 809550095
        self._cmpbuf0 = [253, 34]  # '\xfd"' # chr(253),chr(34)
        self._previous_uncbuf = [0 for i in range(54)]
        self._previous_response = [0 for i in range(84)]
        self._previous_crc = self._crc0
        self._recv_crc0 = 0x628EBB05
        self._recv_crc = self._recv_crc0
        self._prev_recv_crc = self._recv_crc
        return

    def run(self):
        while not self._txt_stop_event.is_set():
            if self._txt._directmode:
                if self._txt_sleep_between_updates > 0:
                    time.sleep(self._txt_sleep_between_updates)

                self._txt._cycle_count += 1
                if self._txt._cycle_count > 15:
                    self._txt._cycle_count = 0

                self._txt._exchange_data_lock.acquire()

                if self._txt._config_id[0] != self._txt._config_id_old:
                    self._txt._config_id_old = self._txt._config_id[0]
                    #
                    # at first, transfer i/o config data from TXT to motor shield
                    # (this is only necessary, if config data has been changed, e.g. the config_id number has been increased)
                    #
                    fields = []
                    fmtstr = "<BBB BBBB H BBBBBB"
                    # fmtstr = '<' # little endian
                    fields.append(ftTXT.C_MOT_CMD_CONFIG_IO)
                    # cycle counter of transmitted and received data have to match (not yet checked here yet !)
                    fields.append(self._txt._cycle_count)
                    fields.append(0)  # only master
                    # fmtstr += 'BBB'
                    inp = [0, 0, 0, 0]
                    for k in range(8):
                        mode = self._txt._ftX1_uni[k * 3]
                        digital = self._txt._ftX1_uni[k * 3 + 1]
                        if (mode, digital) == (
                            ftTXT.C_SWITCH,
                            ftTXT.C_DIGITAL,
                        ):  # ftrobopy.input
                            # digital switch with 5k pull up
                            direct_mode = ftTXT.C_MOT_INPUT_DIGITAL_5K
                            # is 0 if voltage over pull up is < 1600 mV (switch closed) else 1 (switch open)
                        # currently not used in ftrobopy
                        elif (mode, digital) == (ftTXT.C_VOLTAGE, ftTXT.C_DIGITAL):
                            # digital voltage is 1 if Input > 600 mV else 0
                            direct_mode = ftTXT.C_MOT_INPUT_DIGITAL_VOLTAGE
                        elif (mode, digital) == (
                            ftTXT.C_RESISTOR,
                            ftTXT.C_ANALOG,
                        ):  # ftrobopy.resistor
                            # analog resistor with 5k pull up [0 - 15K Ohm]
                            direct_mode = ftTXT.C_MOT_INPUT_ANALOG_5K
                            # unit of return value is [Ohm]
                        elif (mode, digital) == (
                            ftTXT.C_VOLTAGE,
                            ftTXT.C_ANALOG,
                        ):  # ftrobopy.voltage
                            # analog voltage [5 mV - 10V]
                            direct_mode = ftTXT.C_MOT_INPUT_ANALOG_VOLTAGE
                            # bit in response[4] for digital input is also set to 1 if value > 600 mV else 0
                        elif mode == ftTXT.C_ULTRASONIC:  # ftrobopy.ultrasonic
                            # ultrasonic for both C_ANALOG and C_DIGITAL
                            direct_mode = ftTXT.C_MOT_INPUT_ULTRASONIC
                        else:
                            # fall back to default case
                            direct_mode = ftTXT.C_MOT_INPUT_ANALOG_VOLTAGE

                        inp[int(k / 2)] |= (direct_mode & 0x0F) << (4 * (k % 2))
                    fields.append(inp[0])
                    fields.append(inp[1])
                    fields.append(inp[2])
                    fields.append(inp[3])
                    # fmtstr += 'BBBB'
                    fields.append(0)  # CRC (not used ?)
                    # fmtstr += 'H'
                    fields.append(0)
                    fields.append(0)
                    fields.append(0)
                    fields.append(0)
                    fields.append(0)
                    fields.append(0)
                    # fmtstr += 'BBBBBB' # dummy bytes to fill up structure to 15 bytes in total
                    buflen = struct.calcsize(fmtstr)
                    buf = struct.pack(fmtstr, *fields)
                    self._txt._ser_ms.write(buf)
                    data = self._txt._ser_ms.read(len(buf))

                #
                # transfer parameter data from TXT to motor shield
                #
                fields = []
                fmtstr = "<BBBB BBBBBBBB BB BBBB HHHH BBBB BBBBBBBBBBBB H"
                # fmtstr = '<' # little endian
                fields.append(ftTXT.C_MOT_CMD_EXCHANGE_DATA)
                # number of bytes to transfer will be set below
                fields.append(0)
                fields.append(self._txt._cycle_count)
                # bit pattern of connected txt extension modules, 0 = only master
                fields.append(0)
                # fmtstr += 'BBBB'

                # pwm data
                #
                for k in range(8):
                    if self._txt._pwm[k] == 512:
                        pwm = 255
                    else:
                        pwm = int(self._txt._pwm[k] / 2)
                    fields.append(pwm)
                    # fmtstr += 'B'

                # synchronization data (for encoder motors)
                #
                # low byte: M1:0000 M2:0000, high byte: M3:0000 M4:0000
                # Mx = 0000      : no synchronization
                # Mx = 1 - 4     : synchronize to motor n
                # Mx = 5 - 8     : "error injection" into synchronization to allow for closed loops (together with distance values)
                S = self._txt.getMotorSyncMaster()
                sync_low = (S[0] & 0x0F) | ((S[1] & 0x0F) << 4)
                sync_high = (S[2] & 0x0F) | ((S[3] & 0x0F) << 4)
                fields.append(sync_low)
                fields.append(sync_high)
                # fmtstr += 'BB'

                # cmd id data
                #
                # "counter reset cmd id" (bits 0-2) of 4 counters and "motor cmd id" (bits 0-2) of 4 motors
                # are packed into 3 bytes + 1 reserve byte = 1 32bit unsigned integer
                # lowest byte  : c3 c3 c2 c2 c2 c1 c1 c1 (bit7 .. bit0)
                # next byte    : m2 m1 m1 m1 c4 c4 c4 c3 (bit7 .. bit0)
                # next byte    : m4 m4 m4 m3 m3 m3 m2 m2 (bit7 .. bit 0)
                # highest byte : 00 00 00 00 00 00 00 00 (reserved byte)
                M = self._txt.getMotorCmdId()
                C = self._txt.getCounterCmdId()
                b0 = C[0] & 0x07
                b0 |= (C[1] & 0x07) << 3
                b0 |= (C[2] & 0x03) << 6
                b1 = (C[2] & 0x04) >> 2
                b1 |= (C[3] & 0x07) << 1
                b1 |= (M[0] & 0x07) << 4
                b1 |= (M[1] & 0x01) << 7
                b2 = (M[1] & 0x06) >> 1
                b2 |= (M[2] & 0x07) << 2
                b2 |= (M[3] & 0x07) << 5
                fields.append(b0)
                fields.append(b1)
                fields.append(b2)
                fields.append(0)
                # fmtstr += 'BBBB'

                # distance counters
                #
                D = self._txt.getMotorDistance()
                fields.append(D[0])  # distance counter 1
                fields.append(D[1])  # distance counter 2
                fields.append(D[2])  # distance counter 3
                fields.append(D[3])  # distance counter 4
                # fmtstr += 'HHHH'

                # reserve bytes
                #
                fields.append(0)
                fields.append(0)
                fields.append(0)
                fields.append(0)
                # fmtstr += 'BBBB'

                # more filler bytes
                #
                # the length of the transmitted data block (from the txt to the motor shield)
                # has to be at least as large as the length of the expected data block
                # (the answer of the motor shield will never be longer than the initial send)
                for k in range(12):
                    fields.append(0)
                    # fmtstr += 'B'

                # crc
                #
                # it seems that the crc is not used on the motor shield
                fields.append(0)
                # fmtstr += 'H'

                buflen = struct.calcsize(fmtstr)
                fields[1] = buflen
                buf = struct.pack(fmtstr, *fields)
                self._txt._ser_ms.write(buf)
                data = self._txt._ser_ms.read(len(buf))
                # the answer of the motor shield has the following format
                #
                # fmtstr  = '<'
                # fmtstr += 'B'    # [0]     command code
                # fmtstr += 'B'    # [1]     length of data block
                # fmtstr += 'B'    # [2]     cycle counter
                # fmtstr += 'B'    # [3]     bit pattern of connected txt extension modules, 0 = only master
                # fmtstr += 'B'    # [4]     digital input bits
                # fmtstr += 'BBBB' # [5:9]   analog inputs I1-I4 bits 0-7
                # fmtstr += 'BBB'  # [9:12]  analog inputs I1-I4 bits 8-13 : 22111111 33332222 44444433  |  44444433 33332222 22111111
                # fmtstr += 'BBBB' # [12:16] analog inputs I5-I8 bits 0-7
                # fmtstr += 'BBB'  # [16:19] analog inputs I5-I8 bits 8-13 : 66555555 77776666 88888877  |  88888877 77776666 66555555
                # fmtstr += 'B'    # [19]    voltage power supply analog bits 0-7
                # fmtstr += 'B'    # [20]    temperature analog bits 0-7
                # fmtstr += 'B'    # [21]    pwr and temp bits 8-12: ttpp pppp
                # fmtstr += 'B'    # [22]    reference voltage analog bits 0-7
                # fmtstr += 'B'    # [23]    extension voltage VBUS analog bits 0-7
                # fmtstr += 'B'    # [24]    ref and ext analog bits 8-12 : eeee rrrr
                # fmtstr += 'B'    # [25]    bit pattern of fast counters (bit0=C1 .. bit3=C2, bit4-7 not used)
                #         specifies, if fast counter value changed since last data exchange
                # fmtstr += 'H'    # [26]    counter 1 value
                # fmtstr += 'H'    # [27]    counter 2 value
                # fmtstr += 'H'    # [28]    counter 3 value
                # fmtstr += 'H'    # [29]    counter 4 value
                # fmtstr += 'B'    # [30]    ir byte 0
                # fmtstr += 'B'    # [31]    ir byte 1
                # fmtstr += 'B'    # [32]    ir byte 2
                # fmtstr += 'B'    # [33]    (?)
                # fmtstr += 'B'    # [34]    motor cmd id
                # fmtstr += 'B'    # [35]    motor cmd id and counter reset cmd id
                # fmtstr += 'B'    # [36]    counter reset cmd id
                # fmtstr += 'B'    # [37]    reserve byte 1
                # fmtstr += 'BB'   # [38:39] 2 byte crc (not used)

                fmtstr = "<BBBBB BBBB BBB BBBB BBB BBBBBBB HHHH BBBBBBBB BB"

                if len(data) == struct.calcsize(fmtstr):
                    response = struct.unpack(fmtstr, data)
                else:
                    response = ["i", [0] * len(data)]

                #
                # convert received data and write to ftrobopy data structures
                #

                # inputs
                #
                m, i = self._txt.getConfig()
                for k in range(8):
                    if i[k][1] == ftTXT.C_DIGITAL:
                        if response[4] & (1 << k):
                            self._txt._current_input[k] = 1
                        else:
                            self._txt._current_input[k] = 0
                    else:
                        if k == 0:
                            self._txt._current_input[k] = response[5] + 256 * (
                                response[9] & 0x3F
                            )
                        elif k == 1:
                            self._txt._current_input[k] = response[6] + 256 * (
                                ((response[9] >> 6) & 0x03)
                                + ((response[10] << 2) & 0x3C)
                            )
                        elif k == 2:
                            self._txt._current_input[k] = response[7] + 256 * (
                                ((response[10] >> 4) & 0x0F)
                                + ((response[11] << 4) & 0x30)
                            )
                        elif k == 3:
                            self._txt._current_input[k] = response[8] + 256 * (
                                (response[11] >> 2) & 0x3F
                            )
                        elif k == 4:
                            self._txt._current_input[k] = response[12] + 256 * (
                                response[16] & 0x3F
                            )
                        elif k == 5:
                            self._txt._current_input[k] = response[13] + 256 * (
                                ((response[16] >> 6) & 0x03)
                                + ((response[17] << 2) & 0x3C)
                            )
                        elif k == 6:
                            self._txt._current_input[k] = response[14] + 256 * (
                                ((response[17] >> 4) & 0x0F)
                                + ((response[18] << 4) & 0x30)
                            )
                        elif k == 7:
                            self._txt._current_input[k] = response[15] + 256 * (
                                (response[18] >> 2) & 0x3F
                            )

                # power (of battery and/or main power supply) in volt and internal TXT temperature
                #
                self._txt._current_power = response[19] + 256 * (response[21] & 0x3F)
                self._txt._current_temperature = response[20] + 256 * (
                    (response[21] >> 6) & 0x03
                )

                # reference voltage and extension voltage
                #
                self._txt._current_reference_power = response[22] + 256 * (
                    response[24] & 0x0F
                )
                self._txt._current_extension_power = response[23] + 256 * (
                    (response[24] >> 4) & 0x0F
                )

                # signals which fast counters did change since last data exchange
                #
                for k in range(4):
                    if response[25] & (1 << k):
                        self._txt._current_counter[k] = 1
                    else:
                        self._txt._current_counter[k] = 0
                self._txt.debug = response[25]

                # current values of fast counters
                #
                self._txt._current_counter_value = response[26:30]

                # - ir data: response[30:33]
                #
                # ir remote 0 (any)

                self._txt._ir_current_buttons[0] = (response[30] >> 4) & 0x03
                self._txt._ir_current_dip_switch[0] = (response[30] >> 6) & 0x03
                if response[30] & 0x01:
                    self._txt._ir_current_rjoy_left_right[0] = response[31] & 0x0F
                else:
                    self._txt._ir_current_rjoy_left_right[0] = -(response[31] & 0x0F)
                if response[30] & 0x02:
                    self._txt._ir_current_rjoy_up_down[0] = (response[31] >> 4) & 0x0F
                else:
                    self._txt._ir_current_rjoy_up_down[0] = -(
                        (response[31] >> 4) & 0x0F
                    )
                if response[30] & 0x04:
                    self._txt._ir_current_ljoy_left_right[0] = response[32] & 0x0F
                else:
                    self._txt._ir_current_ljoy_left_right[0] = -(response[32] & 0x0F)
                if response[30] & 0x08:
                    self._txt._ir_current_ljoy_up_down[0] = (response[32] >> 4) & 0x0F
                else:
                    self._txt._ir_current_ljoy_up_down[0] = -(
                        (response[32] >> 4) & 0x0F
                    )
                # ir remote 1-4 ( = copy of ir remote 0)
                irNr = ((response[30] >> 6) & 0x03) + 1
                self._txt._ir_current_buttons[irNr] = self._txt._ir_current_buttons[0]
                self._txt._ir_current_dip_switch[
                    irNr
                ] = self._txt._ir_current_dip_switch[0]
                self._txt._ir_current_rjoy_left_right[
                    irNr
                ] = self._txt._ir_current_rjoy_left_right[0]
                self._txt._ir_current_rjoy_up_down[
                    irNr
                ] = self._txt._ir_current_rjoy_up_down[0]
                self._txt._ir_current_ljoy_left_right[
                    irNr
                ] = self._txt._ir_current_ljoy_left_right[0]
                self._txt._ir_current_ljoy_up_down[
                    irNr
                ] = self._txt._ir_current_ljoy_up_down[0]

                # current values of motor cmd id and counter reset id
                #
                # packed into 3 bytes
                # lowest byte  : c3 c3 c2 c2 c2 c1 c1 c1 (bit7 .. bit0)
                # next byte    : m2 m1 m1 m1 c4 c4 c4 c3 (bit7 .. bit0)
                # next byte    : m4 m4 m4 m3 m3 m3 m2 m2 (bit7 .. bit 0)

                b0 = response[34]
                b1 = response[35]
                b2 = response[36]
                self._txt._debug = [b0, b1, b2]
                # get pointers to current counter and motor cmd id data structures
                cC = self._txt.getCurrentCounterCmdId()
                cM = self._txt.getCurrentMotorCmdId()
                cC[0] = b0 & 0x07
                cC[1] = (b0 >> 3) & 0x07
                cC[2] = (b0 >> 6) & 0x03 | (b1 << 2) & 0x04
                cC[3] = (b1 >> 1) & 0x07
                cM[0] = (b1 >> 4) & 0x07
                cM[1] = (b1 >> 7) & 0x01 | (b2 << 1) & 0x06
                cM[2] = (b2 >> 2) & 0x07
                cM[3] = (b2 >> 5) & 0x07

                self._txt._update_status = 1
                self._txt._exchange_data_lock.release()

                #
                # send sound data over spi-bus to motor shield
                #
                if self._txt._spi:
                    if self._txt._sound_state == self._txt.C_SND_STATE_IDLE:
                        if (
                            self._txt.getCurrentSoundCmdId()
                            != self._txt.getSoundCmdId()
                        ):
                            res = self._txt._spi.xfer([self._txt.C_SND_CMD_RESET, 0, 0])
                            self._txt._exchange_data_lock.acquire()
                            self._txt._sound_state = self._txt.C_SND_STATE_DATA
                            self._txt._sound_data_idx = 0
                            self._txt._sound_current_rep = 0
                            self._txt._exchange_data_lock.release()

                    if self._txt._sound_state == self._txt.C_SND_STATE_DATA:
                        res = self._txt._spi.xfer(
                            [self._txt.C_SND_CMD_STATUS, self._txt.getSoundCmdId(), 0]
                        )
                        if res[0] == self._txt.C_SND_MSG_RX_CMD:
                            nFreeBuffers = res[1]
                            while nFreeBuffers > 1:
                                if self._txt._sound_data_idx < len(
                                    self._txt._sound_data
                                ):
                                    res = self._txt._spi.xfer(
                                        [
                                            self._txt.C_SND_CMD_DATA,
                                            self._txt.getSoundCmdId(),
                                            0,
                                        ]
                                        + self._txt._sound_data[
                                            self._txt._sound_data_idx : self._txt._sound_data_idx
                                            + self._txt.C_SND_FRAME_SIZE
                                        ]
                                    )
                                    nFreeBuffers = res[1]
                                    self._txt._sound_data_idx += (
                                        self._txt.C_SND_FRAME_SIZE
                                    )
                                else:
                                    self._txt._sound_current_rep += 1
                                    if (
                                        self._txt._sound_current_rep
                                        < self._txt.getSoundRepeat()
                                    ):
                                        self._txt._sound_data_idx = 0
                                    else:
                                        res = self._txt._spi.xfer(
                                            [
                                                self._txt.C_SND_CMD_STATUS,
                                                self._txt.getSoundCmdId(),
                                                0,
                                            ]
                                        )
                                        nFreeBuffers = res[1]
                                        self._txt._sound_state = (
                                            self._txt.C_SND_STATE_IDLE
                                        )
                                        self._txt._current_sound_cmd_id[
                                            0
                                        ] = self._txt.getSoundCmdId()
                                        break
            else:
                try:
                    if self._txt_sleep_between_updates > 0:
                        time.sleep(self._txt_sleep_between_updates)

                    if self._txt._use_extension:
                        # start_time=time.time()
                        m_id = 0xFBC56F98
                        m_resp_id = 0x6F3B54E6
                        m_extrasize = 0
                        self._txt._exchange_data_lock.acquire()
                        fields = [m_id]  # commad id
                        fields += [m_extrasize]  # will be calculated below
                        fields += [0]  # CRC, set below
                        fields += [1]  # number of active extensions
                        fields += [0]  # 16 bit dummy align
                        fstr = "<IIIHH"
                        self._txt._exchange_data_lock.release()
                        if self._txt._TransferDataChanged:
                            uncbuf = []
                            # add MASTER fields
                            self._txt._exchange_data_lock.acquire()
                            uncbuf += self._txt._pwm[:8]
                            uncbuf += self._txt._motor_sync[:4]
                            uncbuf += self._txt._motor_dist[:4]
                            uncbuf += self._txt._motor_cmd_id[:4]
                            uncbuf += self._txt._counter[:4]
                            uncbuf += [
                                self._txt._sound[0],
                                self._txt._sound_index[0],
                                self._txt._sound_repeat[0],
                            ]
                            # add SLAVE flieds
                            uncbuf += self._txt._pwm[8:]
                            uncbuf += self._txt._motor_sync[4:]
                            uncbuf += self._txt._motor_dist[4:]
                            uncbuf += self._txt._motor_cmd_id[4:]
                            uncbuf += self._txt._counter[4:]
                            # for now use same sound as for MASTER
                            uncbuf += [
                                self._txt._sound[1],
                                self._txt._sound_index[1],
                                self._txt._sound_repeat[1],
                            ]
                            self._txt._exchange_data_lock.release()
                            # print(uncbuf)
                            # compress buffer
                            self.compBuffer.Reset()
                            for i in range(len(uncbuf)):
                                if uncbuf[i] == self._previous_uncbuf[i]:
                                    self.compBuffer.AddWord(0, word_for_crc=uncbuf[i])
                                else:
                                    if uncbuf[i] == 0:
                                        self.compBuffer.AddWord(1, word_for_crc=0)
                                    else:
                                        self.compBuffer.AddWord(uncbuf[i])
                            self.compBuffer.Finish()
                            self._previous_uncbuf = uncbuf[:]
                            crc = self.compBuffer.m_crc.m_crc & 0xFFFFFFFF
                            cmpbuf = self.compBuffer.m_compressed
                            self._txt._TransferDataChanged = False
                            self._previous_crc = crc
                        else:
                            crc = self._previous_crc
                            cmpbuf = self._cmpbuf0

                        m_extrasize = len(cmpbuf)
                        fields += cmpbuf
                        fstr += str(m_extrasize) + "B"
                        # fields += [0] # dummy byte UINT8
                        # fstr   += 'B'
                        fields[1] = m_extrasize
                        fields[2] = crc
                        # print("fields=", fields)
                        # print("crc=",hex(crc)," : ", format((crc >>24) & 255, '3d'), format((crc >>16) & 255, '3d'), format((crc >>8) & 255, '3d'), format(crc & 255, '3d'), "  cmpbuf=", ' '.join(format(x,'3d') for x in cmpbuf) )

                        buf = struct.pack(fstr, *fields)
                        # print("buf=",' '.join(format(x, '02x') for x in buf))
                        self._txt._socket_lock.acquire()
                        res = self._txt._sock.send(buf)

                        retbuf = self._txt._sock.recv(512)
                        self._txt._update_timer = time.time()
                        self._txt._socket_lock.release()

                        if len(retbuf) == 0:
                            print(
                                "ERROR: no data received in ftTXTexchange thread during exchange data compressed, possibly due to network error or CRC failure"
                            )
                            print("Connection to TXT aborted")
                            self._txt_stop_event.set()
                            return
                        # print("retbuf=",','.join(format(ord(x),'4d') for x in retbuf))
                        # head of response is uncompressed
                        self._prev_recv_crc = self._recv_crc  # save previous checksum
                        resphead = struct.unpack("<IIIHH", retbuf[:16])
                        response_id = resphead[0]
                        extra_size = resphead[1]  # size of compressed data
                        # CRC32 checksum of compressed data
                        self._recv_crc = resphead[2]
                        nr_ext = resphead[3]  # number of active extensions
                        # dmy_align      = resphead[4] # dummy align
                        if response_id != m_resp_id:
                            print(
                                "ResponseID ",
                                hex(response_id),
                                " of exchangeData command in exchange thread does not match",
                            )
                            print("Connection to TXT aborted")
                            self._txt_stop_event.set()
                            return
                        # response=[response_id]
                        if self._prev_recv_crc != self._recv_crc:
                            # uncompress body of response
                            self.compBuffer.Reset()
                            self.compBuffer.m_compressed = retbuf[16:]
                            response = list(
                                map(lambda x: self.compBuffer.GetWord(), range(77))
                            )
                            # print(self._recv_crc, response)
                            self._txt._exchange_data_lock.acquire()

                            def conv_null(a, b):
                                return [
                                    a[i]
                                    if b[i] == 0
                                    else 0
                                    if (b[i] == 1 and a[i] == 1)
                                    else 1
                                    if (b[i] == 1 and a[i] == 0)
                                    else b[i]
                                    for i in range(len(b))
                                ]

                            # MASTER
                            self._txt._current_input[:8] = conv_null(
                                self._txt._current_input[:8], response[:8]
                            )
                            self._txt._current_counter[:4] = conv_null(
                                self._txt._current_counter[:4], response[8:12]
                            )
                            self._txt._current_counter_value[:4] = conv_null(
                                self._txt._current_counter_value[:4], response[12:16]
                            )
                            self._txt._current_counter_cmd_id[:4] = conv_null(
                                self._txt._current_counter_cmd_id[:4], response[16:20]
                            )
                            self._txt._current_motor_cmd_id[:4] = conv_null(
                                self._txt._current_motor_cmd_id[:4], response[20:24]
                            )
                            self._txt._current_sound_cmd_id[0] = conv_null(
                                [self._txt._current_sound_cmd_id[0]], [response[24]]
                            )[0]
                            # self._txt._current_ir[:26]            = conv_null(self._txt._current_ir[:26], response[25:52])
                            # EXTENSION
                            self._txt._current_input[8:] = conv_null(
                                self._txt._current_input[8:], response[52:60]
                            )
                            self._txt._current_counter[4:] = conv_null(
                                self._txt._current_counter[4:], response[60:64]
                            )
                            self._txt._current_counter_value[4:] = conv_null(
                                self._txt._current_counter_value[4:], response[64:68]
                            )
                            self._txt._current_counter_cmd_id[4:] = conv_null(
                                self._txt._current_counter_cmd_id[4:], response[68:72]
                            )
                            self._txt._current_motor_cmd_id[4:] = conv_null(
                                self._txt._current_motor_cmd_id[4:], response[72:76]
                            )
                            # self._txt._current_sound_cmd_id[1]    = conv_null([self._txt._current_sound_cmd_id[1]], [response[76]])
                            # last 3 are not used
                            # dummy                             = response[77:80]

                            self._txt.handle_data(self._txt)
                            self._txt._exchange_data_lock.release()
                            # end_time=time.time()
                            # print("time=",end_time-start_time)

                    else:
                        m_id = 0xCC3597BA
                        m_resp_id = 0x4EEFAC41
                        self._txt._exchange_data_lock.acquire()
                        fields = [m_id]
                        fields += self._txt._pwm[:8]
                        fields += self._txt._motor_sync[:4]
                        fields += self._txt._motor_dist[:4]
                        fields += self._txt._motor_cmd_id[:4]
                        fields += self._txt._counter[:4]
                        fields += [
                            self._txt._sound[0],
                            self._txt._sound_index[0],
                            self._txt._sound_repeat[0],
                            0,
                            0,
                        ]
                        self._txt._exchange_data_lock.release()
                        buf = struct.pack("<I8h4h4h4h4hHHHbb", *fields)
                        self._txt._socket_lock.acquire()
                        res = self._txt._sock.send(buf)
                        data = self._txt._sock.recv(512)
                        self._txt._update_timer = time.time()
                        self._txt._socket_lock.release()
                        fstr = "<I8h4h4h4h4hH4bB4bB4bB4bB4bBb"
                        response_id = 0
                        if len(data) == struct.calcsize(fstr):
                            response = struct.unpack(fstr, data)
                        else:
                            print(
                                "Received data size (",
                                len(data),
                                ") does not match length of format string (",
                                struct.calcsize(fstr),
                                ")",
                            )
                            print("Connection to TXT aborted")
                            self._txt_stop_event.set()
                            return
                        response_id = response[0]
                        if response_id != m_resp_id:
                            print(
                                "ResponseID ",
                                hex(response_id),
                                " of exchangeData command in exchange thread does not match",
                            )
                            print("Connection to TXT aborted")
                            self._txt_stop_event.set()
                            return
                        self._txt._exchange_data_lock.acquire()
                        self._txt._current_input[:8] = response[1:9]
                        self._txt._current_counter[:4] = response[9:13]
                        self._txt._current_counter_value[:4] = response[13:17]
                        self._txt._current_counter_cmd_id[:4] = response[17:21]
                        self._txt._current_motor_cmd_id[:4] = response[21:25]
                        self._txt._current_sound_cmd_id[0] = response[25]
                        self._txt._current_ir = response[26:52]
                        self._txt.handle_data(self._txt)
                        self._txt._exchange_data_lock.release()

                except Exception as err:
                    self._txt_stop_event.set()
                    print("Network error ", err)
                    self._txt.handle_error("Network error", err)
                    return
                self._txt._exchange_data_lock.acquire()
                self._txt._update_status = 1
                self._txt._exchange_data_lock.release()
                # extract values of IR-Remotes
                irNr = ((self._txt._current_ir[4] >> 2) & 3) + 1
                # IR-Remote any
                self._txt._ir_current_ljoy_left_right[0] = self._txt._current_ir[0]
                self._txt._ir_current_ljoy_up_down[0] = self._txt._current_ir[1]
                self._txt._ir_current_rjoy_left_right[0] = self._txt._current_ir[2]
                self._txt._ir_current_rjoy_up_down[0] = self._txt._current_ir[3]
                self._txt._ir_current_buttons[0] = self._txt._current_ir[4] & 3
                self._txt._ir_current_dip_switch[0] = (
                    self._txt._current_ir[4] >> 2
                ) & 3
                # IR-Remote 1 to 4
                self._txt._ir_current_ljoy_left_right[irNr] = self._txt._current_ir[
                    irNr * 5 + 0
                ]
                self._txt._ir_current_ljoy_up_down[irNr] = self._txt._current_ir[
                    irNr * 5 + 1
                ]
                self._txt._ir_current_rjoy_left_right[irNr] = self._txt._current_ir[
                    irNr * 5 + 2
                ]
                self._txt._ir_current_rjoy_up_down[irNr] = self._txt._current_ir[
                    irNr * 5 + 3
                ]
                self._txt._ir_current_buttons[irNr] = (
                    self._txt._current_ir[irNr * 5 + 4] & 3
                )
                self._txt._ir_current_dip_switch[irNr] = (
                    self._txt._current_ir[irNr * 5 + 4] >> 2
                ) & 3
        return


class camera(threading.Thread):
    def __init__(self, host, port, lock, stop_event):
        threading.Thread.__init__(self)
        self._camera_host = host
        self._camera_port = port
        self._camera_stop_event = stop_event
        self._camera_data_lock = lock
        self._m_numframesready = 0
        self._m_framewidth = 0
        self._m_frameheight = 0
        self._m_framesizeraw = 0
        self._m_framesizecompressed = 0
        self._m_framedata = []
        return

    def run(self):
        self._camera_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._camera_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._camera_sock.setblocking(1)
        self._total_bytes_read = 0
        camera_ready = False
        fault_count = 0
        while not camera_ready:
            time.sleep(0.02)
            try:
                self._camera_sock.connect((self._camera_host, self._camera_port))
                camera_ready = True
            except:
                fault_count += 1
            if fault_count > 150:
                camera_ready = True
                self._camera_stop_event.set()
                print("Camera not connected")
        if not self._camera_stop_event.is_set():
            print("Camera connected")
        while not self._camera_stop_event.is_set():
            try:
                m_id = 0xBDC2D7A1
                m_ack_id = 0xADA09FBA
                fstr = "<Iihhii"
                # data struct size without jpeg data
                ds_size = struct.calcsize(fstr)
                data = self._camera_sock.recv(ds_size)
                data_size = len(data)
                if data_size > 0:
                    self._total_bytes_read += data_size
                    if self._total_bytes_read == ds_size:
                        response = struct.unpack(fstr, data)
                        if response[0] != m_id:
                            print(
                                "WARNING: ResponseID ",
                                hex(response[0]),
                                " of cameraOnlineFrame command does not match",
                            )
                        self._m_numframesready = response[1]
                        self._m_framewidth = response[2]
                        self._m_frameheight = response[3]
                        self._m_framesizeraw = response[4]
                        self._m_framesizecompressed = response[5]
                        self._m_framedata = []
                        m_framedata_part = []
                        fdatacount = 0
                        while (
                            len(data) > 0
                            and self._total_bytes_read
                            < ds_size + self._m_framesizecompressed
                        ):
                            data = self._camera_sock.recv(1500)
                            m_framedata_part[fdatacount:] = data[:]
                            fdatacount += len(data)
                            self._total_bytes_read += len(data)
                        self._camera_data_lock.acquire()
                        self._m_framedata[:] = m_framedata_part[:]
                        self._camera_data_lock.release()
                        if len(data) == 0:
                            print("WARNING: Connection to camera lost")
                            self._camera_stop_event.set()
                        if (
                            self._total_bytes_read
                            == ds_size + self._m_framesizecompressed
                        ):
                            buf = struct.pack("<I", m_ack_id)
                            res = self._camera_sock.send(buf)
                        self._total_bytes_read = 0
                else:
                    self._camera_stop_event.set()
            except Exception as err:
                print("ERROR in camera thread: ", err)
                self._camera_sock.close()
                return
        self._camera_sock.close()
        return

    def getCameraFrame(self):

        self._camera_data_lock.acquire()
        data = self._m_framedata
        self._m_framedata = []
        self._camera_data_lock.release()
        return data


class BTJoystickEval(threading.Thread):
    def __init__(self, txt, sleep_between_updates, stop_event, jsdev):
        threading.Thread.__init__(self)
        self._txt = txt
        self._bt_joystick_sleep_between_updates = sleep_between_updates
        self._bt_joystick_stop_event = stop_event
        self._bt_joystick_interval_timer = time.time()
        self._jsdev = jsdev
        return

    def run(self):
        while not self._bt_joystick_stop_event.is_set():
            if self._bt_joystick_sleep_between_updates > 0:
                time.sleep(self._bt_joystick_sleep_between_updates)
            self._txt._bt_joystick_lock.acquire()
            if self._jsdev:
                buf = self._jsdev.read(8)
                if buf:
                    t, v, evt, n = struct.unpack("IhBB", buf)
                    if evt & 0x02:
                        # print("axe ", n, " value=", v)
                        if n == 0:
                            self._txt._bt_ljoy_left_right = v
                        elif n == 1:
                            self._txt._bt_ljoy_up_down = v
                        elif n == 2:
                            self._txt._bt_rjoy_left_right = v
                        elif n == 3:
                            self._txt._bt_rjoy_up_down = v
            self._txt._bt_joystick_lock.release()


class ftrobopy(ftTXT):
    def __init__(
        self,
        host="127.0.0.1",
        port=65000,
        update_interval=0.01,
        special_connection="127.0.0.1",
        use_extension=False,
        use_TransferAreaMode=False,
    ):
        def probe_socket(host, p=65000, timeout=0.5):
            s = socket.socket()
            s.settimeout(timeout)
            ok = True
            try:
                s.connect((host, p))
            except Exception as err:
                ok = False
            s.close()
            return ok

        self._txt_is_initialized = False
        if host[:4] == "auto" or host == "127.0.0.1" or host == "localhost":
            # first check if running on TXT:
            if (
                str.find(socket.gethostname(), "FT-txt") >= 0
                or str.find(socket.gethostname(), "ft-txt") >= 0
            ):
                txt_control_main_is_running = False
                # check if TxtMainControl is not running
                pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
                for pid in pids:
                    try:
                        line = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
                        if line.decode("utf-8").find("TxtControlMain") >= 0:
                            txt_control_main_is_running = True
                            break
                    except IOError:
                        continue
                    except:
                        break
                if txt_control_main_is_running:
                    if probe_socket("127.0.0.1"):
                        host = "127.0.0.1"
                    else:
                        print(
                            "Error: auto-detection failed, TxtControlMain-Prozess is running, but did not respond."
                        )
                        return
                else:
                    host = "direct"
            # not running on TXT-controller, check standard ports (only in auto mode)
            else:
                if host[:4] == "auto":
                    if probe_socket("192.168.7.2"):  # USB (Ethernet)
                        host = "192.168.7.2"
                    elif probe_socket("192.168.8.2"):  # WLAN
                        host = "192.168.8.2"
                    elif probe_socket("192.168.9.2"):  # Blutooth
                        host = "192.168.9.2"
                    # non standard port, e.g. home network
                    elif probe_socket(special_connection):
                        host = special_connection
                    else:
                        print(
                            "Error: could not auto detect TXT connection. Please specify host and port manually !"
                        )
                        return
        if host[:6] == "direct":
            # check if running on FT-txt
            if (
                str.find(socket.gethostname(), "FT-txt") < 0
                and str.find(socket.gethostname(), "ft-txt") < 0
            ):
                print("ftrobopy konnte nicht initialisiert werden.")
                print(
                    "Der 'direct'-Modus kann nur im Download/Offline-Betrieb auf dem TXT verwendet werden !"
                )
                return None
            # check if TxtMainControl is running, if yes quit
            pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
            for pid in pids:
                try:
                    line = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
                    if line.decode("utf-8").find("TxtControlMain") >= 0:
                        print("ftrobopy konnte nicht initialisiert werden.")
                        print(
                            "Der Prozess 'TxtControlMain' muss vor der Verwendung des 'direct'-Modus beendet werden !"
                        )
                        return None
                except IOError:
                    continue
                except:
                    print(
                        "ftrobopy konnte nicht im 'direct'-Modus initialisiert werden."
                    )
                    return
            ftTXT.__init__(self, directmode=True)
        else:
            ftTXT.__init__(
                self,
                host,
                port,
                use_extension=use_extension,
                use_TransferAreaMode=use_TransferAreaMode,
            )
        self._txt_is_initialzed = True
        self.queryStatus()
        if self.getVersionNumber() < 0x4010500:
            print("ftrobopy needs at least firmwareversion ", hex(0x4010500), ".")
            sys.exit()
        print("Connected to ", self.getDevicename(), self.getFirmwareVersion())
        if use_extension:
            n = 16
        else:
            n = 8
        for i in range(n):
            self.setPwm(i, 0)
        self.startOnline(update_interval)
        # self.updateConfig(ftTXT.C_EXT_MASTER)
        # if (use_extension):
        #  self.updateConfig(ftTXT.C_EXT_SLAVE)

    def __del__(self):
        if self._txt_is_initialized:
            self.stopCameraOnline()
            self.stopOnline()
            if self._sock:
                self._sock.close()
            if self._ser_ms:
                self._ser_ms.close()

    def motor(self, output, ext=ftTXT.C_EXT_MASTER, wait=True):
        class mot(object):
            def __init__(self, outer, output, ext):
                self._outer = outer
                self._output = output
                self._ext = ext
                self._speed = 0
                self._distance = 0
                self._outer._exchange_data_lock.acquire()
                self.setSpeed(0)
                self.setDistance(0)
                self._outer._exchange_data_lock.release()

            def setSpeed(self, speed):
                c_speed = int(292 / 8 * int(speed) + 220)
                if c_speed == self._speed:
                    return
                self._outer._exchange_data_lock.acquire()
                if speed == 0:
                    self._speed = 0
                else:
                    self._speed = c_speed
                if speed > 0:
                    self._outer.setPwm((self._output - 1) * 2, self._speed, self._ext)
                    self._outer.setPwm((self._output - 1) * 2 + 1, 0, self._ext)
                else:
                    self._outer.setPwm((self._output - 1) * 2, 0, self._ext)
                    self._outer.setPwm(
                        (self._output - 1) * 2 + 1, -self._speed, self._ext
                    )
                self._outer._exchange_data_lock.release()

            def setDistance(self, distance, syncto=None):
                self._outer._exchange_data_lock.acquire()
                if syncto:
                    self._distance = distance
                    syncto._distance = distance
                    self._command_id = self._outer.getCurrentMotorCmdId(
                        self._output - 1, self._ext
                    )
                    syncto._command_id = syncto._outer.getCurrentMotorCmdId(
                        self._output - 1, self._ext
                    )
                    self._outer.setMotorDistance(self._output - 1, distance, self._ext)
                    self._outer.setMotorDistance(
                        syncto._output - 1, distance, self._ext
                    )
                    self._outer.setMotorSyncMaster(
                        self._output - 1, 4 * self._ext + syncto._output, self._ext
                    )
                    self._outer.setMotorSyncMaster(
                        syncto._output - 1, 4 * self._ext + self._output, self._ext
                    )
                    self._outer.incrMotorCmdId(self._output - 1, self._ext)
                    self._outer.incrMotorCmdId(syncto._output - 1, self._ext)
                else:
                    self._distance = distance
                    self._command_id = self._outer.getCurrentMotorCmdId(
                        self._output - 1, self._ext
                    )
                    self._outer.setMotorDistance(self._output - 1, distance, self._ext)
                    self._outer.setMotorSyncMaster(self._output - 1, 0, self._ext)
                    self._outer.incrMotorCmdId(self._output - 1, self._ext)
                self._outer._exchange_data_lock.release()

            def finished(self):
                if self._outer.getMotorCmdId(
                    self._output - 1, self._ext
                ) == self._outer.getCurrentMotorCmdId(self._output - 1, self._ext):
                    return True
                else:
                    return False

            def getCurrentDistance(self):
                return self._outer.getCurrentCounterValue(
                    idx=self._output - 1, ext=self._ext
                )

            def stop(self):
                self._outer._exchange_data_lock.acquire()
                self.setSpeed(0)
                self.setDistance(0)
                self._outer._exchange_data_lock.release()

        M, I = self.getConfig(ext)
        M[output - 1] = ftTXT.C_MOTOR
        self.setConfig(M, I, ext)
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return mot(self, output, ext)

    def led(self, num, level=0, ext=ftTXT.C_EXT_MASTER, wait=True):
        class out(object):
            def __init__(self, outer, num, level, ext):
                self._outer = outer
                self._num = num
                self._level = level
                self._ext = ext
                self.setLevel(level)

            def setLevel(self, level):
                self._level = level
                self._outer._exchange_data_lock.acquire()
                self._outer.setPwm(num - 1, self._level, self._ext)
                self._outer._exchange_data_lock.release()

        M, I = self.getConfig(ext)
        M[int((num - 1) / 2)] = ftTXT.C_OUTPUT
        self.setConfig(M, I, ext)
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return out(self, num, level, ext)

    def button(self, num, ext=ftTXT.C_EXT_MASTER, wait=True):
        class inp(object):
            def __init__(self, outer, num, ext):
                self._outer = outer
                self._num = num
                self._ext = ext

            def getState(self):
                return self._outer.getCurrentInput(num - 1, self._ext)

        M, I = self.getConfig(ext)
        I[num - 1] = (ftTXT.C_SWITCH, ftTXT.C_DIGITAL)
        self.setConfig(M, I, ext)
        if self._use_TransferAreaMode:
            ftTA2py.fX1config_uni(ext, num - 1, I[num - 1][0], I[num - 1][1])
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return inp(self, num, ext)

    def resistor(self, num, ext=ftTXT.C_EXT_MASTER, wait=True):
        class inp(object):
            def __init__(self, outer, num, ext):
                self._outer = outer
                self._num = num
                self._ext = ext

            def value(self):
                return self._outer.getCurrentInput(num - 1, self._ext)

            def ntcTemperature(self):
                r = self.value()
                if r != 0:
                    x = log(self.value())
                    y = x * x * 1.39323522
                    z = x * -43.9417405
                    T = y + z + 271.870481
                else:
                    T = 10000
                return T

        M, I = self.getConfig(ext)
        I[num - 1] = (ftTXT.C_RESISTOR, ftTXT.C_ANALOG)
        self.setConfig(M, I, ext)
        if self._use_TransferAreaMode:
            ftTA2py.fX1config_uni(ext, num - 1, I[num - 1][0], I[num - 1][1])
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return inp(self, num, ext)

    def ultrasonic(self, num, ext=ftTXT.C_EXT_MASTER, wait=True):
        class inp(object):
            def __init__(self, outer, num, ext):
                self._outer = outer
                self._num = num
                self._ext = ext

            def distance(self):
                return self._outer.getCurrentInput(num - 1, self._ext)

        M, I = self.getConfig(ext)
        I[num - 1] = (ftTXT.C_ULTRASONIC, ftTXT.C_ANALOG)
        self.setConfig(M, I, ext)
        if self._use_TransferAreaMode:
            ftTA2py.fX1config_uni(ext, num - 1, I[num - 1][0], I[num - 1][1])
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return inp(self, num, ext)

    def voltage(self, num, ext=ftTXT.C_EXT_MASTER, wait=True):
        class inp(object):
            def __init__(self, outer, num, ext):
                self._outer = outer
                self._num = num
                self._ext = ext

            def voltage(self):
                return self._outer.getCurrentInput(num - 1, self._ext)

        M, I = self.getConfig(ext)
        I[num - 1] = (ftTXT.C_VOLTAGE, ftTXT.C_ANALOG)
        self.setConfig(M, I, ext)
        if self._use_TransferAreaMode:
            ftTA2py.fX1config_uni(ext, num - 1, I[num - 1][0], I[num - 1][1])
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return inp(self, num, ext)

    def colorsensor(self, num, ext=ftTXT.C_EXT_MASTER, wait=True):
        class inp(object):
            def __init__(self, outer, num, ext):
                self._outer = outer
                self._num = num
                self._ext = ext

            def value(self):
                return self._outer.getCurrentInput(num - 1, self._ext)

            def color(self):
                c = self._outer.getCurrentInput(num - 1, self._ext)
                if c < 200:
                    return "weiss"
                elif c < 1000:
                    return "rot"
                else:
                    return "blau"

        M, I = self.getConfig(ext)
        I[num - 1] = (ftTXT.C_VOLTAGE, ftTXT.C_ANALOG)
        self.setConfig(M, I, ext)
        if self._use_TransferAreaMode:
            ftTA2py.fX1config_uni(ext, num - 1, I[num - 1][0], I[num - 1][1])
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return inp(self, num, ext)

    def trailfollower(self, num, ext=ftTXT.C_EXT_MASTER, wait=True):
        class inp(object):
            def __init__(self, outer, num, ext):
                self._outer = outer
                self._num = num
                self._ext = ext

            def getState(self):
                # in direct-mode digital 1 is set by motor-shield if voltage is > 600mV
                if self._outer.getCurrentInput(num - 1, self._ext) == 1:
                    return 1
                else:
                    # threshold in mV between digital 0 and 1. Use voltage()-Function instead, if analog value of trailfollower is needed.
                    if self._outer.getCurrentInput(num - 1, self._ext) > 600:
                        return False
                    else:
                        return True

        M, I = self.getConfig(ext)
        I[num - 1] = (ftTXT.C_VOLTAGE, ftTXT.C_DIGITAL)
        self.setConfig(M, I, ext)
        if self._use_TransferAreaMode:
            ftTA2py.fX1config_uni(ext, num - 1, I[num - 1][0], I[num - 1][1])
        self.updateConfig(ext)
        if wait:
            self.updateWait()
        return inp(self, num, ext)

    def joystick(self, joynum, remote_number=0, remote_type=0):
        class remote(object):
            def __init__(
                self, outer, joynum, remote_number, remote_type, update_interval=0.01
            ):
                # remote_number: 0=any, 1-4=remote1-4
                # remote_type: IR=0, BT=1
                self._outer = outer
                self._joynum = joynum
                self._remote_number = remote_number
                self._remote_type = remote_type
                self._jsdev = None
                if self._remote_type == 1:  # BT remote
                    self._remote_number = 0  # only 1 BT remote is supported
                    try:
                        # open joystick device
                        self._jsdev = open("/dev/input/js0", "rb")
                    except:
                        self._jsdev = None
                        print("Failed to open BT Joystick")
                    if self._jsdev:
                        if self._outer._bt_joystick_stop_event.is_set():
                            self._outer._bt_joystick_stop_event.clear()
                        if self._outer._bt_joystick_thread is None:
                            self._outer._bt_joystick_thread = BTJoystickEval(
                                txt=self._outer,
                                sleep_between_updates=update_interval,
                                stop_event=self._outer._bt_joystick_stop_event,
                                jsdev=self._jsdev,
                            )
                            self._outer._bt_joystick_thread.setDaemon(True)
                            self._outer._bt_joystick_thread.start()
                return None

            def isConnected(self):
                return (not self._outer._bt_joystick_stop_event.is_set()) and (
                    self._outer._bt_joystick_thread is not None
                )

            def leftright(self):
                if remote_type == 0:  # IR remote
                    if joynum == 0:  # left joystick on remote
                        return (
                            1.0
                            * self._outer._ir_current_ljoy_left_right[remote_number]
                            / 15.0
                        )
                    else:  # right joystick on remote
                        return (
                            1.0
                            * self._outer._ir_current_rjoy_left_right[remote_number]
                            / 15.0
                        )
                else:  # BT remote
                    if joynum == 0:  # left joystick on remote
                        v = 1.0 * self._outer._bt_ljoy_left_right
                        if v < 0:
                            v /= 32767.0
                        else:
                            v /= 32512.0
                        return v
                    else:  # right joystick on remote
                        v = 1.0 * self._outer._bt_rjoy_left_right
                        if v < 0:
                            v /= 32767.0
                        else:
                            v /= 32512.0
                        return v

            def updown(self):
                if remote_type == 0:  # IR remote
                    if joynum == 0:  # left joystick on remote
                        return (
                            1.0
                            * self._outer._ir_current_ljoy_up_down[remote_number]
                            / 15.0
                        )
                    else:  # right joystick on remote
                        return (
                            1.0
                            * self._outer._ir_current_rjoy_up_down[remote_number]
                            / 15.0
                        )
                else:  # BT remote
                    if joynum == 0:  # left joystick on remote
                        v = 1.0 * self._outer._bt_ljoy_up_down
                        if v <= 0:
                            v /= -32767.0
                        else:
                            v /= -32512.0
                        return v
                    else:  # right joystick on remote
                        v = 1.0 * self._outer._bt_rjoy_up_down
                        if v <= 0:
                            v /= -32767.0
                        else:
                            v /= -32512.0
                        return v

        return remote(self, joynum, remote_number, remote_type)

    def joybutton(self, buttonnum, remote_number=0, remote_type=0):
        class remote(object):
            def __init__(self, outer, buttonnum, remote_number, remote_type):
                # remote_number: 0=any, 1-4=remote1-4
                # remote_type: IR=0, BT=1
                self._outer = outer
                self._buttonnum = buttonnum
                self._remote_number = remote_number
                self._remote_type = remote_type

            def pressed(self):
                if remote_type == 0:  # IR remote
                    if buttonnum == 0:  # left button (ON) on remote
                        if self._outer._ir_current_buttons[remote_number] == 1:
                            return True
                        else:
                            return False
                    else:  # right button (OFF) on remote
                        if (self._outer._ir_current_buttons[remote_number]) >> 1 == 1:
                            return True
                        else:
                            return False
                else:  # BT remote has no buttons
                    return False

        return remote(self, buttonnum, remote_number, remote_type)

    def joydipswitch(self, remote_type=0):

        if idx != self.getSoundIndex(ext):
            self.setSoundIndex(idx, ext)
        if volume != self.getSoundVolume and self._directmode:
            self.setSoundVolume(volume)
        self.setSoundRepeat(repeat, ext)
        self.incrSoundCmdId(ext)

    def stop_sound(self, ext=ftTXT.C_EXT_MASTER):

        self.setSoundIndex(0, ext)
        self.setSoundRepeat(1, ext)
        self.incrSoundCmdId(ext)
