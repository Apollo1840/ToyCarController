from flask import Flask, render_template, request, Response
from adafruit_servokit import ServoKit
import cv2
import time
import threading

# Initialize the ServoKit for 16 channels
kit = ServoKit(channels=16)

# Initial positions for servos
horizontal_range = (40, 180)
vertical_range = (0, 50)
horizontal_angle = horizontal_range[1] // 2
vertical_angle = vertical_range[1] // 2
horizontal_step = horizontal_range[1] // 30
vertical_step = vertical_range[1] // 20

detect_frame_rate = 5  # Detection frame rate in Hz

# Initialize the Flask application
app = Flask(__name__)

# Open the video capture (assuming the USB camera is at /dev/video0)
camera = cv2.VideoCapture(0)
# camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
# camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Load the Haar cascade file for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Shared resource for faces
faces = []
faces_lock = threading.Lock()


def face_detection_loop():
    global faces
    last_detection_time = 0

    while True:
        current_time = time.time()
        if current_time - last_detection_time >= 1 / detect_frame_rate:
            success, frame = camera.read()
            if not success:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            with faces_lock:
                faces = [detected_faces[0]]

            last_detection_time = current_time


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        with faces_lock:
            current_faces = faces

        # for (x, y, w, h) in current_faces:
        #    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        if current_faces:
            x, y, w, h = current_faces[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


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
        vertical_angle = max(vertical_angle - vertical_step, vertical_range[0])
        kit.servo[1].angle = vertical_angle
    elif direction == 'right':
        horizontal_angle = max(horizontal_angle - horizontal_step, horizontal_range[0])
        kit.servo[0].angle = horizontal_angle
    elif direction == 'left':
        horizontal_angle = min(horizontal_angle + horizontal_step, horizontal_range[1])
        kit.servo[0].angle = horizontal_angle

    return ('', 204)  # Return an empty response


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # Start face detection in a separate thread
    threading.Thread(target=face_detection_loop, daemon=True).start()

    app.run(host='0.0.0.0', port=5000)
