import ijmrobopy

#
TXT = ijmrobopy.TXT("192.168.7.2")

#Get proximity sensor connected via i2c-connection
proximity_sensor = TXT.proximitySensor()

#turn proximity sensor on
proximity_sensor.turnOn()

#print for one minute every second the distance
for _ in range(60):
    print(proximity_sensor.getDistance())
    ijmrobopy.wait(1)

#turn the proximity sensor off
proximity_sensor.turnOff()