import board
import busio
import numpy as np
import time
from adafruit_motorkit import MotorKit

# Initialize I2C bus and MotorKit
i2c = busio.I2C(board.SCL, board.SDA)
print("Devices found on I2C bus: ", i2c.scan())

kit = MotorKit(i2c=i2c)


# Function to run the motor at a specified throttle for a certain duration
def run_motor(motor, target_throttle, duration):
    current_throttle = motor.throttle if motor.throttle is not None else 0
    step = 0.1 if target_throttle > current_throttle else -0.1

    for t in np.arange(current_throttle, target_throttle, step):
        motor.throttle = t
        time.sleep(0.1)

    motor.throttle = target_throttle
    print(f"Motor running at throttle {target_throttle} for {duration} seconds")
    time.sleep(duration)

    motor.throttle = 0
    print("Motor stopped")


if __name__ == "__main__":
    kit = MotorKit()

    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0

    print("Prepare to run (3 seconds)")
    time.sleep(3)

    # Run motor 1 forward and backward
    run_motor(kit.motor1, 1.0, 3)
    time.sleep(1)
    run_motor(kit.motor1, -1.0, 3)

    # Run motor 2 forward and backward
    run_motor(kit.motor2, 1.0, 3)
    time.sleep(1)
    run_motor(kit.motor2, -1.0, 3)

    # Run motor 3 forward and backward
    run_motor(kit.motor3, 1.0, 3)
    time.sleep(1)
    run_motor(kit.motor3, -1.0, 3)

    # Run motor 4 forward and backward
    run_motor(kit.motor4, 1.0, 3)
    time.sleep(1)
    run_motor(kit.motor4, -1.0, 3)

    print("End")
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    kit.motor3.throttle = 0
    kit.motor4.throttle = 0