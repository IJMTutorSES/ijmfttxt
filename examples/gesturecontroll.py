import ijmfttxt

TXT = ijmfttxt.TXT()

motor_hl = TXT.motor(1)
motor_vl = TXT.motor(2)
motor_vr = TXT.motor(3)
motor_hr = TXT.motor(4)

gesture_sensor = TXT.gestureSensor()

def controll_robot(ud, lr):
    if ud != 0:
        motor_hl.setSpeed(512*ud)
        motor_vl.setSpeed(512*ud)
        motor_vr.setSpeed(512*ud)
        motor_hr.setSpeed(512*ud)
    elif lr != 0:
        motor_hl.setSpeed(512*lr)
        motor_vr.setSpeed(512*-lr)
        motor_vl.setSpeed(512*lr)
        motor_hr.setSpeed(512*-lr)
    else:
        motor_hl.setSpeed(0)
        motor_vl.setSpeed(0)
        motor_vr.setSpeed(0)
        motor_hr.setSpeed(0)

up_down = 0
left_right = 0

while True:
    gesture = gesture_sensor.getGesture()
    if gesture == "UP":
        up_down += 1
        left_right = 0
    elif gesture == "DOWN":
        up_down -= 1
        left_right = 0
    elif gesture == "LEFT":
        left_right += 1
        up_down = 0
    elif gesture == "RIGHT":
        left_right -= 1
        up_down = 0
    controll_robot(up_down, left_right)

