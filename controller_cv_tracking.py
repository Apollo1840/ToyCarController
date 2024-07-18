from flask import Flask, render_template, request, Response
from adafruit_servokit import ServoKit
import cv2
import time
import threading
import logging
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO)


class ServoController:
    def __init__(self, channels=16):
        self.kit = ServoKit(channels=channels)
        self.horizontal_range = (40, 180)
        self.vertical_range = (0, 50)
        self.horizontal_angle = (self.horizontal_range[1] + self.horizontal_range[0]) // 2
        self.vertical_angle = (self.vertical_range[1] + self.vertical_range[0]) // 2
        self.horizontal_step = self.horizontal_range[1] // 60
        self.vertical_step = self.vertical_range[1] // 40
        self.is_tracking = False
        self.tracking_tol = 20
        self.tracking_thread = None
        self.stop_tracking_flag = threading.Event()
        self.face_positions = deque(maxlen=5)  # Store recent face positions for smoothing

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

    def set_tracking(self, tracking):
        self.is_tracking = tracking
        if tracking:
            self.stop_tracking_flag.clear()
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.start()
        else:
            self.stop_tracking_flag.set()
            if self.tracking_thread:
                self.tracking_thread.join()

    def tracking_loop(self):
        frame_width = 640  # Assuming a fixed frame width
        frame_height = 480  # Assuming a fixed frame height
        while not self.stop_tracking_flag.is_set():
            face_x, face_y = face_detector.face_center()

            target_x, target_y = self.tracking_face_algorithm(face_x, face_y)
            if target_x is not None and target_y is not None:
                self.track_face(target_x, target_y, frame_width, frame_height)

            time.sleep(0.1)  # Adjust the sleep time as needed

    def track_face(self, face_x, face_y, frame_width, frame_height):
        if self.is_tracking:
            center_x, center_y = frame_width // 2, frame_height // 2
            logging.info(f"Navigating face at x: {face_x}, y: {face_y} to the center x: {center_x}, y: {center_y} ")

            # if center is too right(high x value of center), move the camera left
            if face_x < center_x - self.tracking_tol:
                self.move_servo('left')
                # logging.info(f"> move the camera left")

            elif face_x > center_x + self.tracking_tol:
                self.move_servo('right')
                # logging.info(f"> move the camera right")

            # if center is too high(low y value of center), move the camera down
            if face_y > center_y + self.tracking_tol:
                self.move_servo('down')
                # logging.info(f"> move the camera down")

            elif face_y < center_y - self.tracking_tol:
                self.move_servo('up')
                # logging.info(f"> move the camera up")

    def tracking_face_algorithm(self, face_x, face_y):
        if face_x is not None and face_y is not None:
            self.face_positions.append((face_x, face_y))

        target_x, target_y = None, None
        if len(self.face_positions) > 0:
            weights = [2 ** i for i in range(len(self.face_positions))]
            total_weight = sum(weights)
            weighted_x = sum(pos[0] * weight for pos, weight in zip(self.face_positions, weights)) / total_weight
            weighted_y = sum(pos[1] * weight for pos, weight in zip(self.face_positions, weights)) / total_weight
            target_x = weighted_x
            target_y = weighted_y
        return target_x, target_y


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

                # Log detected faces
                if len(detected_faces) > 0:
                    for (x, y, w, h) in detected_faces:
                        logging.info(f"Detected face at x: {x}, y: {y}, width: {w}, height: {h}")

                with self.faces_lock:
                    self.faces = detected_faces
                last_detection_time = current_time

    def generate_frames(self):
        while True:
            success, frame = self.camera.read()
            if not success:
                break

            ul, lr = self.face_box()
            if ul and lr:
                cv2.rectangle(frame, ul, lr, color=(255, 0, 0), thickness=2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def face_center(self):
        face_x, face_y = None, None
        with self.faces_lock:
            if len(self.faces) > 0:
                x, y, w, h = self.faces[0]
                face_x, face_y = x + w // 2, y + h // 2
        return face_x, face_y

    def face_box(self):
        ul, lr = None, None
        with self.faces_lock:
            if len(self.faces) > 0:
                x, y, w, h = self.faces[0]
                ul, lr = (x, y), (x + w, y + h)
        return ul, lr


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


@app.route('/toggle_tracking')
def toggle_tracking():
    enabled = request.args.get('enabled', 'false') == 'true'
    servo_controller.set_tracking(enabled)
    return ('', 204)


@app.route('/video_feed')
def video_feed():
    return Response(face_detector.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    threading.Thread(target=face_detector.detect_faces, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)