import board
import busio
from time import sleep
from adafruit_motorkit import MotorKit

# Initialize I2C bus and MotorKit
i2c = busio.I2C(board.SCL, board.SDA)
print("Devices found on I2C bus: ", i2c.scan())

kit = MotorKit(i2c=i2c)


# Function to run the motor at a specified throttle for a certain duration
def run_motor(motor, throttle, duration):
    for t in range(0, throttle, 0.1):
        motor.throttle = t
        sleep(0.1)
    print(f"Motor running at throttle {throttle} for {duration} seconds")
    sleep(duration)
    motor.throttle = 0
    print("Motor stopped")


if __name__ == "__main__":
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0

    print("prepare to run (3 seconds)")
    sleep(3)

    # Run motor 1 forward and backward
    run_motor(kit.motor1, 1.0, 3)
    run_motor(kit.motor1, -1.0, 3)

    # Run motor 2 forward and backward
    run_motor(kit.motor2, 1.0, 3)
    run_motor(kit.motor2, -1.0, 3)

    # Run motor 3 forward and backward
    run_motor(kit.motor3, 1.0, 3)
    run_motor(kit.motor3, -1.0, 3)

    # Run motor 4 forward and backward
    run_motor(kit.motor4, 1.0, 3)
    run_motor(kit.motor4, -1.0, 3)

    print("end")
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0
