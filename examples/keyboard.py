import ijmrobopy

TXT = ijmrobopy.TXT("auto")
KEYBOARD = ijmrobopy.Keyboard()

motor = TXT.motor(1)

while True:
    if KEYBOARD.is_pressed("a"):
        motor.setSpeed(512)
    else:
        motor.setSpeed(0)
