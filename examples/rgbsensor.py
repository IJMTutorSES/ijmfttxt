import ijmrobopy

TXT = ijmrobopy.TXT("auto")

rgb_sensor = TXT.rgb_sensor()
rgb_sensor.turn_on()

for _ in range(60):
    print("rot", rgb_sensor.get_red())
    print("grün", rgb_sensor.get_green())
    print("blau", rgb_sensor.get_blue())
    ijmrobopy.wait(1)
rgb_sensor.turn_off()