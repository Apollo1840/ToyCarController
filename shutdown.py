import board
import busio
from adafruit_motorkit import MotorKit
from adafruit_servokit import ServoKit

# Initialize I2C bus and MotorKit
i2c = busio.I2C(board.SCL, board.SDA)
print("Devices found on I2C bus: ", i2c.scan())

kit = MotorKit(i2c=i2c)
kit2 = ServoKit(channels=16)


if __name__ == "__main__":
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0

    kit2.servo[0].angle = 90
    kit2.servo[1].angle = 0

