import time
import ijmfttxt

# Initialize and setup Connection to TXT Controller
TXT = ijmrobopy.TXT()

# Get light sensor connect via i2c-connection
light_sensor = TXT.lightSensor()

# Turn the light sensor on
light_sensor.turnOn()

# print for one minute every second the Brightness
for _ in range(60):
    print(light_sensor.getBrightness())
    time.sleep(1)

# turn the light sensor off
light_sensor.turnOff()
