import board
import busio
from time import sleep
from adafruit_servokit import ServoKit

i2c = busio.I2C(board.SCL, board.SDA)
print("find device on: ", i2c.scan())

kit = ServoKit(channels=16)
kit.servo[0].angle = 0
sleep(1)

while True:
    kit.servo[0].angle = 90
    sleep(3)
    print("angle at 90 degree for 3 seconds")

    kit.servo[0].angle = 0
    sleep(3)
    print("angle at 0 degree for 3 seconds")
