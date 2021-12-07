import ijmfttxt

# Initialize and setup Connection to TXT Controller
txt = ijmfttxt.TXT()

# get the rgb sensor connected via i2c-connection
color_sensor = txt.colorSensor()

# turn the rgb sensor on
color_sensor.turnOn()

# print for one minute every second the red, green and blue data and also the guessed name of the color
for _ in range(60):
    color = color_sensor.getColor()
    print("rot", color.r)
    print("grün", color.g)
    print("blau", color.b)
    print(color.name)
    time.sleep(1)

# turn the rgb sensor off
color_sensor.turnOff()
