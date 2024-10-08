import cv2
import time
import threading
import logging
from collections import deque
from .servo_controller import ServoController

# Configure logging
logging.basicConfig(level=logging.INFO)


class TrackableServoController(ServoController):
    def __init__(self, face_detector, channels=16):
        super().__init__(channels)
        self.face_detector = face_detector
        self.frame_width = 640  # Assuming a fixed frame width
        self.frame_height = 480  # Assuming a fixed frame height
        self.frame_center_x, self.frame_center_y = self.frame_width // 2, self.frame_height // 2

        self.is_tracking = False
        self.tracking_tol = 20
        self.tracking_speed = 0.4  # recommend: 0.1-1
        self.tracking_freq = 10  # Hz
        self.tracking_thread = None
        self.stop_tracking_flag = threading.Event()

        self.face_positions = deque(maxlen=5)  # Store recent face positions for smoothing

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

        while not self.stop_tracking_flag.is_set():
            face_x, face_y = self.face_detector.face_center()

            if face_x and face_y:
                logging.info(
                    f"{self.__class__.__name__}: detected face at x: {face_x}, y: {face_y} ")

            target_x, target_y = self.tracking_face_algorithm(face_x, face_y)
            if target_x is not None and target_y is not None:
                self.track_face(target_x, target_y)

            time.sleep(1 / self.tracking_freq)  # Adjust the sleep time as needed

    def track_face(self, face_x, face_y):
        if self.is_tracking:
            logging.info(
                f"{self.__class__.__name__}: Estimate face at x: {int(face_x)}, y: {int(face_y)}")
            logging.info(
                f"{self.__class__.__name__}: Prepare to move it towards camera center x: {self.frame_center_x}, y: {self.frame_center_y} ")

            # Calculate the distance from the center
            distance_x = abs(face_x - self.frame_center_x)
            distance_y = abs(face_y - self.frame_center_y)

            # Calculate damp_factor (approaches 0 when near center, 1 otherwise)
            damp_factor_x = min(1, distance_x / (3 * self.tracking_tol))
            damp_factor_y = min(1, distance_y / (3 * self.tracking_tol))

            if damp_factor_x < 1:
                logging.info(
                    f"{self.__class__.__name__}: horizontal close, damp factor: {damp_factor_x}")
            if damp_factor_y < 1:
                logging.info(
                    f"{self.__class__.__name__}: vertical close, damp factor: {damp_factor_y}")

            # If the center is too right (high x value of center), move the camera left
            if face_x < self.frame_center_x - self.tracking_tol:
                self.move_servo('left', amplify=self.tracking_speed * damp_factor_x)
                logging.info(f"{self.__class__.__name__}: Moved the camera left")

            elif face_x > self.frame_center_x + self.tracking_tol:
                self.move_servo('right', amplify=self.tracking_speed * damp_factor_x)
                logging.info(f"{self.__class__.__name__}: Moved the camera right")

            # If the center is too high (low y value of center), move the camera down
            if face_y > self.frame_center_y + self.tracking_tol:
                self.move_servo('down', amplify=self.tracking_speed * damp_factor_y)
                logging.info(f"{self.__class__.__name__}: Moved the camera down")

            elif face_y < self.frame_center_y - self.tracking_tol:
                self.move_servo('up', amplify=self.tracking_speed * damp_factor_y)
                logging.info(f"{self.__class__.__name__}: Moved the camera up")

    def tracking_face_algorithm(self, face_x, face_y):
        if face_x is not None and face_y is not None:
            self.face_positions.append((face_x, face_y))
        else:
            # do not move if no detection of face
            self.face_positions.append((self.frame_center_x, self.frame_center_y))

        logging.info(f"{self.__class__.__name__}: captured face locations:" + " ".join(
            [f"({int(fp[0])}, {int(fp[1])})" for fp in self.face_positions]))

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
        if not self.camera.isOpened():
            raise ValueError(f"Unable to open camera with index {camera_index}")

        # Load the face cascade
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise ValueError(f"Unable to load cascade file from path {cascade_path}")

        self.frame_rate = frame_rate
        self.faces = []
        self.faces_lock = threading.Lock()
        self.is_detecting = threading.Event()

    def detect_faces(self):
        last_detection_time = 0
        self.is_detecting.set()
        while self.is_detecting.is_set():
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
                        logging.info(
                            f"{self.__class__.__name__}: Detected face at x: {x}, y: {y}, width: {w}, height: {h}")

                with self.faces_lock:
                    self.faces = detected_faces
                last_detection_time = current_time

    def generate_frames(self):
        while True:
            success, frame = self.camera.read()
            if not success:
                break
            # else:
            #    print("success")

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
