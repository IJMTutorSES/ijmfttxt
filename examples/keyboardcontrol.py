import ijmfttxt

# Initialize and setup Connection to TXT Controller
TXT = ijmftxt.TXT("auto")

# Initialize and start Listener for Keyboardinputs
KEYBOARD = ijmfttxt.Keyboard()

# Get Motor connected to Output 1
motor_l = TXT.motor(1)

# Get Motor connected to Output 2
motor_r = TXT.motor(2)

# Repeat forever
while True:
    # If w is pressed drive forwards
    if KEYBOARD.is_pressed("w"):
        motor_l.setSpeed(8)
        motor_r.setSpeed(8)
    # If s is pressed drive backwards
    elif KEYBOARD.is_pressed("s"):
        motor_l.setSpeed(-8)
        motor_r.setSpeed(-8)
    # If a is pressed drive to the left
    elif KEYBOARD.is_pressed("a"):
        motor_l.setSpeed(-8)
        motor_r.setSpeed(8)
    # If d is pressed drive to the righr
    elif KEYBOARD.is_pressed("d"):
        motor_l.setSpeed(8)
        motor_r.setSpeed(-8)
    # If no key is pressed stop
    else:
        motor_l.stop()
        motor_r.stop()
