import threading
import time
import logging
from adafruit_motorkit import MotorKit


class MotorController:
    def __init__(self, speed=1):
        self.kit = MotorKit()
        self.speed = speed

        self.target_throttle = {
            "forward": {"motor1": -1.0 * self.speed,
                        "motor2": 1.0 * self.speed,
                        "motor3": -1.0 * self.speed,
                        "motor4": 1.0 * self.speed},
            "backward": {"motor1": 1.0 * self.speed,
                         "motor2": -1.0 * self.speed,
                         "motor3": 1.0 * self.speed,
                         "motor4": -1.0 * self.speed},
            "left": {"motor1": -1.0 * self.speed,
                     "motor2": 1.0 * self.speed,
                     "motor3": 1.0 * self.speed,
                     "motor4": -1.0 * self.speed},
            "right": {"motor1": 1.0 * self.speed,
                      "motor2": -1.0 * self.speed,
                      "motor3": -1.0 * self.speed,
                      "motor4": 1.0 * self.speed}
        }

        self.is_recentering = False
        self.recenter_thread = None
        self.current_throttle = {
            "motor1": 0,
            "motor2": 0,
            "motor3": 0,
            "motor4": 0
        }
        self.stopping = True

    def move(self, direction):
        if not self.is_recentering and direction in self.target_throttle:
            self._gradual_throttle_change(self.target_throttle[direction])

    def _gradual_throttle_change(self, target_throttle):
        self.stopping = False
        step = 0.05
        max_steps = int(2 / step)
        for _ in range(max_steps):
            all_reached = True
            for motor, target in target_throttle.items():
                current = self.current_throttle[motor]
                if abs(target - current) > step:
                    all_reached = False
                    if target > current:
                        current = min(current + step, target)
                    elif target < current:
                        current = max(current - step, target)
                    # print(f"motor: {motor}, target: {target}, current: {current}")
                    self._set_motor_throttle(motor, current)
            if all_reached:
                break
            if self.stopping:
                self.stop()
                break
            time.sleep(0.1)

    def _set_motor_throttle(self, motor, throttle):
        motor_obj = getattr(self.kit, motor)
        motor_obj.throttle = throttle
        self.current_throttle[motor] = throttle
        print(f"{motor} throttle set to {throttle}")

    def stop(self):
        print("stopping motors")
        self.stopping = True

        self.kit.motor1.throttle = 0
        self.kit.motor2.throttle = 0
        self.kit.motor3.throttle = 0
        self.kit.motor4.throttle = 0

        self.current_throttle = {
            "motor1": 0,
            "motor2": 0,
            "motor3": 0,
            "motor4": 0
        }

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
