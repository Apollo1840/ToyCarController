from flask import Flask, render_template, request, Response
from adafruit_servokit import ServoKit
import cv2

# Initialize the ServoKit for 16 channels
kit = ServoKit(channels=16)

# Initial positions for servos
horizontal_range = (40, 180)
vertical_range = (0, 50)
horizontal_angle = horizontal_range[1]//2
vertical_angle = vertical_range[1]//2
horizontal_step = horizontal_range[1]//20
vertical_step = vertical_range[1]//20

# Initialize the Flask application
app = Flask(__name__)

# Open the video capture (assuming the USB camera is at /dev/video0)
camera = cv2.VideoCapture(0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move')
def move():
    global horizontal_angle, vertical_angle
    direction = request.args.get('direction')

    if direction == 'up':
        vertical_angle = min(vertical_angle + vertical_step, vertical_range[1])
        kit.servo[1].angle = vertical_angle
    elif direction == 'down':
        vertical_angle = min(vertical_angle - vertical_step, vertical_range[0])
        kit.servo[1].angle = vertical_angle
    elif direction == 'right':
        horizontal_angle = max(horizontal_angle - horizontal_range, horizontal_range[0])
        kit.servo[0].angle = horizontal_angle
    elif direction == 'left':
        horizontal_angle = min(horizontal_angle + horizontal_range, horizontal_range[1])
        kit.servo[0].angle = horizontal_angle

    return ('', 204)  # Return an empty response

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
