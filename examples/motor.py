import ijmrobopy

TXT = ijmrobopy.TXT("auto")
motor = TXT.motor(1)

motor.setSpeed(5)
ijmrobopy.wait(3)
motor.stop()