import time

import ijmfttxt


# Initialize and setup Connection to TXT Controller
txt = ijmfttxt.TXT("auto")

# Get Motor connect to Output 1
motor = txt.motor(1)

# Set Moter speed to 5 for 3 seconds and then stop
motor.setSpeed(5)
time.sleep(3)
motor.stop()
