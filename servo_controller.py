from adafruit_servokit import ServoKit


class ServoController:
    def __init__(self, channels=16):
        self.kit = ServoKit(channels=channels)
        self.horizontal_range = (40, 180)
        self.vertical_range = (0, 50)
        self.horizontal_angle = (self.horizontal_range[1] + self.horizontal_range[0]) // 2
        self.vertical_angle = (self.vertical_range[1] + self.vertical_range[0]) // 2
        self.horizontal_step = self.horizontal_range[1] // 60
        self.vertical_step = self.vertical_range[1] // 40

    def move_servo(self, direction, amplify=1):
        if direction == 'up':
            self.vertical_angle = min(self.vertical_angle + self.vertical_step*amplify, self.vertical_range[1])
            self.kit.servo[1].angle = self.vertical_angle
        elif direction == 'down':
            self.vertical_angle = max(self.vertical_angle - self.vertical_step*amplify, self.vertical_range[0])
            self.kit.servo[1].angle = self.vertical_angle
        elif direction == 'right':
            self.horizontal_angle = max(self.horizontal_angle - self.horizontal_step*amplify, self.horizontal_range[0])
            self.kit.servo[0].angle = self.horizontal_angle
        elif direction == 'left':
            self.horizontal_angle = min(self.horizontal_angle + self.horizontal_step*amplify, self.horizontal_range[1])
            self.kit.servo[0].angle = self.horizontal_angle
