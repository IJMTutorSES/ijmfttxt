import ijmfttxt

# Initialize and setup Connection to TXT Controller
TXT = ijmfttxt.TXT()

# get the rgb sensor connected via i2c-connection
color_sensor = TXT.colorSensor()

# turn the rgb sensor on
color_sensor.turnOn()

# print for one minute every second the red, green and blue data
for _ in range(60):
    color = color_sensor.getColor()
    print("rot", color.r)
    print("grün", color.g)
    print("blau", color.b)
    time.sleep(1)

# turn the rgb sensor off
color_sensor.turnOff()
