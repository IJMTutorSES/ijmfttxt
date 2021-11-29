import ijmfttxt

# Initialize and setup Connection to TXT Controller
TXT = ijmfttxt.TXT()

# get the rgb sensor connected via i2c-connection
rgb_sensor = TXT.rgbSensor()

# turn the rgb sensor on
rgb_sensor.turnOn()

# print for one minute every second the red, green and blue data
for _ in range(60):
    color = rgb_sensor.getColor()
    print("rot", color.r)
    print("grün", color.g)
    print("blau", color.b)
    time.sleep(1)

# turn the rgb sensor off
rgb_sensor.turnOff()
