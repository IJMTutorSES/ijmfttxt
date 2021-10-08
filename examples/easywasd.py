import ijmrobopy
from ijmrobopy.keyboard import Keyboard

KEYBOARD = ijmrobopy.Keyboard()
TXT = ijmrobopy.TXT("auto")

motor_l = TXT.motor(1)
motor_r = TXT.motor(2)

while True:
    if KEYBOARD.is_pressed("w"):
        motor_l.setSpeed(512)
        motor_r.setSpeed(512)
    elif KEYBOARD.is_pressed("s"):
        motor_l.setSpeed(-512)
        motor_r.setSpeed(-512)
    elif KEYBOARD.is_pressed("a"):
        motor_l.setSpeed(-512)
        motor_r.setSpeed(512)
    elif KEYBOARD.is_pressed("d"):
        motor_l.setSpeed(512)
        motor_r.setSpeed(-512)
    else:
        motor_l.stop()
        motor_r.stop()