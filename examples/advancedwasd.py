import ijmrobopy

KEYBOARD = ijmrobopy.Keyboard()
TXT = ijmrobopy.TXT("auto")

STOP = 0b0000
FORWARD = 0b0001
BACKWARD = 0b0010
RIGHT = 0b0100
LEFT = 0b1000

DIRECTIONS = {
    STOP: (0,0),
    FORWARD: (1,1),
    BACKWARD: (-1,-1),
    RIGHT: (1,-1),
    LEFT: (-1,1),
    FORWARD^LEFT: (0,1),
    FORWARD^RIGHT: (1,0),
    BACKWARD^LEFT: (-1, 0),
    BACKWARD^RIGHT: (0,-1)
}

motor_l = TXT.motor(1)
motor_r = TXT.motor(2)

def set_motor_speed(direction):
    dir = DIRECTIONS[direction]
    motor_l.setSpeed(512*dir[0])
    motor_r.setSpeed(512*dir[1])

direction = 0b0000

while True:
    if KEYBOARD.is_pressed("w"):
        direction ^= FORWARD
    else:
        direction &= FORWARD

    if KEYBOARD.is_pressed("s"):
        direction ^= BACKWARD
    else:
        direction &= BACKWARD

    if KEYBOARD.is_pressed("d"):
        direction ^= LEFT
    else:
        direction &= LEFT 

    if KEYBOARD.is_pressed("a"):
        direction ^= RIGHT
    else:
        direction &= RIGHT

    set_motor_speed(direction)