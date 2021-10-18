import ijmrobopy

#Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT("auto")

#get the rgb sensor connected via i2c-connection
rgb_sensor = TXT.rgbSensor()

#turn the rgb sensor on
rgb_sensor.turnOn()

#print for one minute every second the red, green and blue data
for _ in range(60):
    print("rot", rgb_sensor.getRed())
    print("grün", rgb_sensor.getGreen())
    print("blau", rgb_sensor.getBlue())
    ijmrobopy.wait(1)

#turn the rgb sensor off
rgb_sensor.turnOff()