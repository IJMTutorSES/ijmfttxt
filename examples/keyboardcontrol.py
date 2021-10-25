import ijmrobopy
from ijmrobopy.keyboard import Keyboard

#Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT("auto")

#Initialize and start Listener for Keyboardinputs
KEYBOARD = ijmrobopy.Keyboard()

#Get Motor connected to Output 1
motor_l = TXT.motor(1)

#Get Motor connected to Output 2
motor_r = TXT.motor(2)

#Repeat forever
while True:
    #If w is pressed drive forwards
    if KEYBOARD.is_pressed("w"):
        motor_l.setSpeed(512)
        motor_r.setSpeed(512)
    #If s is pressed drive backwards
    elif KEYBOARD.is_pressed("s"):
        motor_l.setSpeed(-512)
        motor_r.setSpeed(-512)
    #If a is pressed drive to the left
    elif KEYBOARD.is_pressed("a"):
        motor_l.setSpeed(-512)
        motor_r.setSpeed(512)
    #If d is pressed drive to the righr
    elif KEYBOARD.is_pressed("d"):
        motor_l.setSpeed(512)
        motor_r.setSpeed(-512)
    #If no key is pressed stop
    else:
        motor_l.stop()
        motor_r.stop()