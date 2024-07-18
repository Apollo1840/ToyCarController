from flask import Flask, render_template, request, Response
from adafruit_servokit import ServoKit
import cv2
import time
import threading


class ServoController:
    def __init__(self, channels=16):
        self.kit = ServoKit(channels=channels)
        self.horizontal_range = (40, 180)
        self.vertical_range = (0, 50)
        self.horizontal_angle = self.horizontal_range[1] // 2
        self.vertical_angle = self.vertical_range[1] // 2
        self.horizontal_step = self.horizontal_range[1] // 30
        self.vertical_step = self.vertical_range[1] // 20

    def move_servo(self, direction):
        if direction == 'up':
            self.vertical_angle = min(self.vertical_angle + self.vertical_step, self.vertical_range[1])
            self.kit.servo[1].angle = self.vertical_angle
        elif direction == 'down':
            self.vertical_angle = max(self.vertical_angle - self.vertical_step, self.vertical_range[0])
            self.kit.servo[1].angle = self.vertical_angle
        elif direction == 'right':
            self.horizontal_angle = max(self.horizontal_angle - self.horizontal_step, self.horizontal_range[0])
            self.kit.servo[0].angle = self.horizontal_angle
        elif direction == 'left':
            self.horizontal_angle = min(self.horizontal_angle + self.horizontal_step, self.horizontal_range[1])
            self.kit.servo[0].angle = self.horizontal_angle


class FaceDetector:
    def __init__(self, camera_index=0, cascade_path=cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
                 frame_rate=5):
        self.camera = cv2.VideoCapture(camera_index)
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.frame_rate = frame_rate
        self.faces = []
        self.faces_lock = threading.Lock()

    def detect_faces(self):
        last_detection_time = 0
        while True:
            current_time = time.time()
            if current_time - last_detection_time >= 1 / self.frame_rate:
                success, frame = self.camera.read()
                if not success:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected_faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                                                    minSize=(30, 30))
                with self.faces_lock:
                    self.faces = detected_faces
                last_detection_time = current_time

    def generate_frames(self):
        while True:
            success, frame = self.camera.read()
            if not success:
                break
            with self.faces_lock:
                current_faces = self.faces
            for (x, y, w, h) in current_faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


app = Flask(__name__)
servo_controller = ServoController()
face_detector = FaceDetector()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/move')
def move():
    direction = request.args.get('direction')
    servo_controller.move_servo(direction)
    return ('', 204)


@app.route('/video_feed')
def video_feed():
    return Response(face_detector.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    threading.Thread(target=face_detector.detect_faces, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
