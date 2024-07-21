import threading
import time
import logging
from adafruit_motorkit import MotorKit


class MotorController:
    def __init__(self):
        self.kit = MotorKit()
        self.is_recentering = False
        self.recenter_thread = None

    def move(self, direction):
        if not self.is_recentering:
            if direction == 'forward':
                self.kit.motor1.throttle = 1.0
                self.kit.motor2.throttle = 1.0
                self.kit.motor3.throttle = 1.0
                self.kit.motor4.throttle = 1.0
            elif direction == 'backward':
                self.kit.motor1.throttle = -1.0
                self.kit.motor2.throttle = -1.0
                self.kit.motor3.throttle = -1.0
                self.kit.motor4.throttle = -1.0
            elif direction == 'left':
                self.kit.motor1.throttle = -0.5
                self.kit.motor2.throttle = 0.5
                self.kit.motor3.throttle = -0.5
                self.kit.motor4.throttle = 0.5
            elif direction == 'right':
                self.kit.motor1.throttle = 0.5
                self.kit.motor2.throttle = -0.5
                self.kit.motor3.throttle = 0.5
                self.kit.motor4.throttle = -0.5

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
