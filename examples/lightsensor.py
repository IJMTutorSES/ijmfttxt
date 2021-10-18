import ijmrobopy

#Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT("auto")

#Get light sensor connect via i2c-connection
light_sensor = TXT.lightSensor()

#Turn the light sensor on 
light_sensor.turnOn()

#print for one minute every second the Brightness
for _ in range(60):
    print(light_sensor.getBrightness())
    ijmrobopy.wait(1)

#turn the light sensor off
light_sensor.turnOff()
