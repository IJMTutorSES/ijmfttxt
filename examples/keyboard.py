import ijmrobopy

#Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT("auto")

#Initialize and setup Listener fo Keyboardinputs
KEYBOARD = ijmrobopy.Keyboard()

#Get Motor connected to Output 1
motor = TXT.motor(1)

#Repeat forever
while True:
    #If e is pressed start Motor else stop Motor
    if KEYBOARD.is_pressed("e"):
        motor.setSpeed(512)
    else:
        motor.setSpeed(0)
