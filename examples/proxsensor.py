import time

import ijmfttxt

# Initialize and setup Connection to TXT Controller
tx = ijmfttxt.TXT()

# Get proximity sensor connected via i2c-connection
proximity_sensor = txt.proximitySensor()

# Turn proximity sensor on
proximity_sensor.turnOn()

# Print for one minute every second the distance
for i in range(60):
    print(proximity_sensor.getDistance())
    time.sleep(1)

# Turn the proximity sensor off
proximity_sensor.turnOff()
