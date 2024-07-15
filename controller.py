from flask import Flask, render_template, request
from adafruit_servokit import ServoKit

# Initialize the ServoKit for 16 channels
kit = ServoKit(channels=16)

# Initial positions for servos
horizontal_angle = 90
vertical_angle = 0

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/move')
def move():
    global horizontal_angle, vertical_angle
    direction = request.args.get('direction')

    if direction == 'up':
        vertical_angle = min(vertical_angle + 10, 180)
        kit.servo[1].angle = vertical_angle
    elif direction == 'down':
        vertical_angle = max(vertical_angle - 10, 0)
        kit.servo[1].angle = vertical_angle
    elif direction == 'left':
        horizontal_angle = max(horizontal_angle - 10, 0)
        kit.servo[0].angle = horizontal_angle
    elif direction == 'right':
        horizontal_angle = min(horizontal_angle + 10, 180)
        kit.servo[0].angle = horizontal_angle

    return ('', 204)  # Return an empty response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
