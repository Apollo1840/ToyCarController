import board
import busio
from time import sleep
from adafruit_servokit import ServoKit

i2c = busio.I2C(board.SCL, board.SDA)
print("find device on: ", i2c.scan())

kit = ServoKit(channels=16)
kit.servo[1].angle = 0
sleep(1)

while True:
    for angle in range(0, 90, 10):
        kit.servo[1].angle = angle
        print(f"angle at {angle} degree for 3 seconds")
        sleep(2)

    for angle in range(0, 170, 10):
        kit.servo[0].angle = angle
        print(f"angle at {angle} degree for 3 seconds")
        sleep(2)