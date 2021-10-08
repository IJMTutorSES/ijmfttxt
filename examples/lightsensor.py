import ijmrobopy

TXT = ijmrobopy.TXT("auto")

light_sensor = TXT.light_sensor()
light_sensor.turn_on()

for _ in range(60):
    print(light_sensor.get_brightness())
    ijmrobopy.wait(1)
light_sensor.turn_off()
