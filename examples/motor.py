import ijmrobopy

#Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT("auto")

#Get Motor connect to Output 1
motor = TXT.motor(1)

#Set Moter speed to 5 for 3 seconds and then stop
motor.setSpeed(5)
ijmrobopy.wait(3)
motor.stop()