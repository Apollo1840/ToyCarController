from flask import Flask, render_template, request, Response
import threading
import logging
from servo_controller_cv import FaceDetector, TrackableServoController

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
face_detector = FaceDetector()
servo_controller = TrackableServoController(face_detector)


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
