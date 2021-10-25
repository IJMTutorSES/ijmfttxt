import ijmrobopy

#Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT("192.168.7.2")

#Get proximity sensor connected via i2c-connection
proximity_sensor = TXT.proximitySensor()

#Turn proximity sensor on
proximity_sensor.turnOn()

#Print for one minute every second the distance
for _ in range(60):
    print(proximity_sensor.getDistance())
    ijmrobopy.wait(1)

#Turn the proximity sensor off
proximity_sensor.turnOff()