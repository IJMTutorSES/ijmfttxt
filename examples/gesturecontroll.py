import ijmfttxt

# Initialize and setup Connection to TXT Controller
TXT = ijmfttxt.TXT()

# Get Motor connected to Output 1
motor_hl = TXT.motor(1)
# Get Motor connected to Output 2
motor_vl = TXT.motor(2)
# Get Motor connected to Output 3
motor_vr = TXT.motor(3)
# Get Motor connected to Output 4
motor_hr = TXT.motor(4)

# Get proximity sensor connected via i2c-connection
gesture_sensor = TXT.gestureSensor()

# Turn gesture sensor on
gesture_sensor.turnOn()

# Method for setting motor speed acording to drive direction
def controll_robot(ud, lr):
    if ud != 0:
        # Moving forwards/backwards
        motor_hl.setSpeed(8 * ud)
        motor_vl.setSpeed(8 * ud)
        motor_vr.setSpeed(8 * ud)
        motor_hr.setSpeed(8 * ud)
    elif lr != 0:
        # Moving to the left/right
        motor_hl.setSpeed(8 * lr)
        motor_vr.setSpeed(8 * -lr)
        motor_vl.setSpeed(8 * lr)
        motor_hr.setSpeed(8 * -lr)
    else:
        # Stop
        motor_hl.setSpeed(0)
        motor_vl.setSpeed(0)
        motor_vr.setSpeed(0)
        motor_hr.setSpeed(0)


# Direction for forwards/backwards
up_down = 0

# Direction for left/right
left_right = 0

# Repeat forever
while True:
    # Get latest detected Motion
    gesture = gesture_sensor.getGesture()
    if gesture == "UP":
        # Set direction values for forward motion
        up_down += 1
        left_right = 0
    elif gesture == "DOWN":
        # Set direction values for backward motion
        up_down -= 1
        left_right = 0
    elif gesture == "LEFT":
        # Set direction values for left-strave motion
        left_right += 1
        up_down = 0
    elif gesture == "RIGHT":
        # Set direction values for right-strave motion
        left_right -= 1
        up_down = 0
    controll_robot(up_down, left_right)
