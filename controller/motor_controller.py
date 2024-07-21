import threading
import time
import logging
from adafruit_motorkit import MotorKit


class MotorController:
    def __init__(self):
        self.kit = MotorKit()
        self.is_recentering = False
        self.recenter_thread = None
        self.current_throttle = {
            "motor1": 0,
            "motor2": 0,
            "motor3": 0,
            "motor4": 0
        }

    def move(self, direction):
        if not self.is_recentering:
            target_throttle = {
                "motor1": 0,
                "motor2": 0,
                "motor3": 0,
                "motor4": 0
            }

            if direction == 'forward':
                target_throttle = {"motor1": 1.0, "motor2": 1.0, "motor3": 1.0, "motor4": 1.0}
            elif direction == 'backward':
                target_throttle = {"motor1": -1.0, "motor2": -1.0, "motor3": -1.0, "motor4": -1.0}
            elif direction == 'left':
                target_throttle = {"motor1": -0.5, "motor2": 0.5, "motor3": -0.5, "motor4": 0.5}
            elif direction == 'right':
                target_throttle = {"motor1": 0.5, "motor2": -0.5, "motor3": 0.5, "motor4": -0.5}

            self._gradual_throttle_change(target_throttle)

    def _gradual_throttle_change(self, target_throttle):
        step = 0.1
        for motor, target in target_throttle.items():
            current = self.current_throttle[motor]
            if target > current:
                while current < target:
                    current = min(current + step, target)
                    self._set_motor_throttle(motor, current)
                    time.sleep(0.1)
            elif target < current:
                while current > target:
                    current = max(current - step, target)
                    self._set_motor_throttle(motor, current)
                    time.sleep(0.1)

    def _set_motor_throttle(self, motor, throttle):
        setattr(self.kit, motor).throttle = throttle
        self.current_throttle[motor] = throttle
        print(f"{motor} throttle set to {throttle}")

    def stop(self):
        self.kit.motor1.throttle = 0
        self.kit.motor2.throttle = 0
        self.kit.motor3.throttle = 0
        self.kit.motor4.throttle = 0

    def recenter(self):
        if not self.is_recentering:
            self.is_recentering = True
            self.recenter_thread = threading.Thread(target=self._recenter_motors)
            self.recenter_thread.start()

    def stop_recenter(self):
        self.is_recentering = False
        if self.recenter_thread and self.recenter_thread.is_alive():
            # Here you can add logic to safely stop the recentering process if necessary
            pass
        self.enable_motors()

    def _recenter_motors(self):
        # PlaceHolder

        # Logic to recenter the motors
        logging.info("Recentering motors...")
        # Move motors to a specific position for recentering
        self.kit.motor1.throttle = 0.5
        self.kit.motor2.throttle = 0.5
        self.kit.motor3.throttle = 0.5
        self.kit.motor4.throttle = 0.5

        # Simulate recentering process
        time.sleep(2)

        # Stop motors after recentering
        self.stop()
        self.is_recentering = False
        logging.info("Motors recentered")

    def enable_motors(self):
        # Logic to enable motor movement after recentering
        self.stop()
